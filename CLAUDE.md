# Empireo Backend Developer Guide

Read this fully before writing any code. This is the single source of truth for the Empireo Backend codebase.

## 1. Project Overview

Empireo Brain is a FastAPI backend for a 40+ employee study abroad, recruitment, and processing organization. It's a CRM/case-management system evolving into an AI-powered Company OS.

- **Repo**: github.com/sharonempire/empireobackend
- **Runtime**: Python 3.11 + FastAPI + SQLAlchemy (async) + Redis + Celery
- **Database**: Supabase PostgreSQL 17 (live data, DO NOT drop/recreate tables)
- **Supabase Project ID**: `ebgzlzemrargfahwokti` (region: ap-south-1)

### Connection Strings

```
DATABASE_URL=postgresql+asyncpg://postgres.ebgzlzemrargfahwokti:Empire%402025-2026@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
DATABASE_URL_SYNC=postgresql://postgres.ebgzlzemrargfahwokti:Empire%402025-2026@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
```

## 2. Running Locally

```bash
# Copy env
cp .env.example .env   # fill in real values

# Docker (no local Postgres — connects to Supabase)
docker compose up --build

# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# Redis: localhost:6379
```

Services: `api` (FastAPI + hot reload), `redis` (7-alpine), `worker` (Celery)

## 3. Project Structure

```
empireobackend/
├── CLAUDE.md                      ← YOU ARE HERE
├── docker-compose.yml
├── Dockerfile                     # Python 3.11-slim
├── requirements.txt
├── .env.example
├── .gitignore
├── app/
│   ├── main.py                    # FastAPI app, lifespan, CORS, all routers mounted
│   ├── config.py                  # Pydantic Settings from .env
│   ├── database.py                # SQLAlchemy async engine + session + Base
│   ├── dependencies.py            # get_current_user, require_perm(resource, action)
│   ├── core/
│   │   ├── security.py            # JWT create/decode (HS256), bcrypt hash/verify
│   │   ├── exceptions.py          # NotFoundError, ForbiddenError, ConflictError, BadRequestError
│   │   ├── pagination.py          # PaginatedResponse[T], paginate(), paginate_metadata()
│   │   ├── permissions.py         # has_permission(db, user_id, resource, action)
│   │   └── events.py              # log_event(db, event_type, actor_id, entity_type, entity_id, metadata)
│   ├── modules/                   # Each module: models.py, schemas.py, router.py, [service.py]
│   │   ├── auth/                  # Login + refresh (service.py ✓)
│   │   ├── users/                 # CRUD + RBAC (service.py ✓)
│   │   ├── students/              # Student profiles (service.py ✓)
│   │   ├── cases/                 # Case tracking + stage transitions (service.py ✓)
│   │   ├── applications/          # University applications (service.py ✓)
│   │   ├── documents/             # File metadata + verification (service.py ✓)
│   │   ├── tasks/                 # Follow-ups, to-dos (service.py ✓)
│   │   ├── approvals/             # Draft → Approve → Execute (service.py ✓)
│   │   ├── events/                # Immutable audit log (read-only)
│   │   ├── notifications/         # User notifications
│   │   ├── workflows/             # Workflow definitions + instances
│   │   ├── ai_artifacts/          # AI generation logs
│   │   ├── policies/              # Company policies + embeddings
│   │   ├── leads/                 # Legacy leadslist + lead_info (read-heavy)
│   │   ├── courses/               # Course catalog (55+ columns)
│   │   ├── profiles/              # Legacy staff profiles
│   │   ├── geography/             # Countries → Cities → Universities → Campuses
│   │   ├── intakes/               # Intake periods
│   │   ├── jobs/                  # Job profiles, jobs, saved/applied
│   │   ├── call_events/           # Phone call logs (17K+ rows)
│   │   ├── chat/                  # Chat conversations + messages
│   │   ├── payments/              # Razorpay payments
│   │   ├── attendance/            # Employee attendance
│   │   ├── ig_sessions/           # Instagram DM bot sessions
│   │   ├── employee_automation/   # ★ NEW — Employee performance + AI analysis
│   │   └── misc/                  # ★ NEW — Utility tables (short_links, fcm, etc.)
│   └── workers/
│       ├── celery_app.py          # Celery config (Redis broker)
│       └── tasks.py               # Async task stubs
```

## 4. Architecture & Patterns

### 4.1 Module Pattern (follow this for ALL new modules)

```python
# models.py — SQLAlchemy ORM mapped to EXISTING table
class MyModel(Base):
    __tablename__ = "eb_my_table"  # or legacy table name
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ... columns match DB exactly

# schemas.py — Pydantic request/response
class MyModelOut(BaseModel):           # Response
    model_config = ConfigDict(from_attributes=True)
class MyModelCreate(BaseModel):        # POST body
class MyModelUpdate(BaseModel):        # PATCH body (all Optional)

# service.py — Business logic (list/get/create/update)
async def list_items(db, page, size, **filters) -> tuple[list, int]:
async def get_item(db, item_id) -> Model:
async def create_item(db, data) -> Model:
async def update_item(db, item_id, data) -> Model:

# router.py — FastAPI endpoints
router = APIRouter(prefix="/my-resource", tags=["My Resource"])
```

### 4.2 Authentication & RBAC

```python
# JWT Bearer token (HS256), 480min access / 30day refresh
# In any protected endpoint:
from app.dependencies import get_current_user, require_perm

@router.get("/")
async def list_things(
    user: User = Depends(get_current_user),        # just needs login
    db: AsyncSession = Depends(get_db),
): ...

@router.post("/")
async def create_thing(
    user: User = Depends(require_perm("things", "create")),  # needs permission
    db: AsyncSession = Depends(get_db),
): ...
```

Permission chain: `eb_users → eb_user_roles → eb_role_permissions → eb_permissions(resource, action)`

5 Roles (in DB): `admin`, `manager`, `counselor`, `processor`, `viewer`

### 4.3 Event Logging (MANDATORY for all CUD operations)

```python
from app.core.events import log_event

# After every create/update/delete:
await log_event(
    db=db,
    event_type="student.created",       # format: entity.action
    actor_id=current_user.id,
    entity_type="student",
    entity_id=student.id,
    metadata={"full_name": student.full_name},
)
await db.commit()
```

### 4.4 Pagination

```python
from app.core.pagination import paginate, paginate_metadata, PaginatedResponse

# Option A: Use paginate() helper (auto-counts + offsets)
result = await paginate(db, query, page=page, size=size)
return result  # {items, total, page, size, pages}

# Option B: Manual query + paginate_metadata()
total = (await db.execute(count_stmt)).scalar()
items = (await db.execute(stmt.offset(...).limit(...))).scalars().all()
return {"items": [Schema.model_validate(i) for i in items], **paginate_metadata(total, page, size)}
```

### 4.5 Error Handling

```python
from app.core.exceptions import NotFoundError, ForbiddenError, ConflictError, BadRequestError
# These are HTTPExceptions with correct status codes (404, 403, 409, 400)
raise NotFoundError("Student not found")
```

## 5. Database — Complete Table Reference

### 5.1 Core CRM Tables (eb_* prefix, 18 tables)

| Table | Rows | Key Columns | Notes |
|-------|------|-------------|-------|
| eb_users | 19 | email, full_name, hashed_password, department, is_active, countries(JSONB) | Staff accounts |
| eb_roles | 5 | name (admin/manager/counselor/processor/viewer) | |
| eb_permissions | 44 | resource, action | e.g. "students:read" |
| eb_user_roles | 19 | user_id, role_id (composite PK) | |
| eb_role_permissions | 121 | role_id, permission_id (composite PK) | |
| eb_students | 1,856 | lead_id(→leadslist), full_name, passport, education, counselor_id, processor_id | |
| eb_cases | 1,856 | student_id, case_type, current_stage, priority, counselor/processor/visa_officer | |
| eb_applications | 21 | case_id, university_name, program_name, status, offer_details(JSONB) | |
| eb_documents | 0 | entity_type/id, file_key, is_verified, verified_by | Polymorphic via entity_type |
| eb_tasks | 0 | entity_type/id, title, assigned_to, created_by, due_at, status, priority | |
| eb_events | 0 | event_type, actor_type/id, entity_type/id, metadata(JSONB) | IMMUTABLE audit log |
| eb_action_drafts | 0 | action_type, payload(JSONB), status, requires_approval, approved_by | Approval pipeline |
| eb_action_runs | 0 | action_draft_id, status, result(JSONB), error | Execution log |
| eb_notifications | 0 | user_id, title, message, is_read, entity_type/id | |
| eb_workflow_definitions | 1 | name, stages(JSONB), transitions(JSONB) | |
| eb_workflow_instances | 0 | workflow_definition_id, entity_type/id, current_stage, history(JSONB) | |
| eb_ai_artifacts | 0 | artifact_type, model_used, tokens, output(JSONB), confidence_score | AI generation log |
| eb_policies | 0 | title, category, content, embedding(VECTOR) | RAG-ready |

Valid case stages: `initial_consultation → documents_pending → documents_collected → university_shortlisted → applied → offer_received → offer_accepted → visa_processing → visa_approved → visa_rejected → travel_booked → completed → on_hold → cancelled`

### 5.2 Legacy Tables (Flutter apps still use these — DO NOT modify schema)

| Table | Rows | Key Columns |
|-------|------|-------------|
| leadslist | 2,103 | name, email, phone(BigInt), assigned_to(→profiles.id), status, heat_status, lead_tab(enum: student/job), country_preference(TEXT[]), 37 cols total |
| lead_info | 2,102 | id(FK→leadslist.id), basic_info(JSON), education(JSON), work_expierience(JSON, typo!), budget_info, preferences, english_proficiency, domain_tags(TEXT[]), interest_embedding(VECTOR) |
| lead_assignment_tracker | 1 | last_assigned_employee(UUID) |
| profiles | 21 | diplay_name(typo!), profilepicture, user_type, designation, countries(TEXT[]), callerId |
| courses | 2,813 | 55+ columns. program_name, university, country, approval_status, 15+ AI-normalized fields |
| university_courses | 4,017 | Mirror of courses + source_key, university_image, tuition_fee_international_* |
| call_events | 17,177 | event_type, call_uuid, caller/agent_number, duration, recording_url, phone_norm |
| chat_conversations | 5,205 | counselor_id, lead_uuid, last_message_text/at |
| chat_messages | 237 | conversation_id, sender/receiver_id, message_text/type, file_url, course_deatails(typo!) |
| payments | 118 | user_id, order_id, payment_id, amount, status, razorpay_* |
| attendance | 298 | employee_id(→profiles), checkinat, checkoutat, date (all Text!) |
| countries | 10 | name, currency, commission(JSONB), displayimage |
| cities | 152 | country_id(FK), population, commission |
| universities | 242 | city_id(FK), ranking, accreditation, commission |
| campuses | 50 | university_id(FK), facilities(JSONB), contact_info(JSONB) |
| intakes | 26 | name, start/end_date, universities/courses/fees/scholarships (all JSONB) |
| jobs | 13 | job_information(JSONB), status, job_profile_id |
| job_profiles | 0 | company_name, email_address |
| applied_courses | 27 | user_id(text), course_id(text), course_details(JSONB), status |
| applied_jobs | 35 | user_id(text), job_id(text), job_details(JSONB), candidate_name |
| saved_courses | 51 | user_id(bigint), course_id(bigint), course_details(JSONB) |
| saved_jobs | 3 | user_id(bigint), job_id(bigint), job_details(JSONB) |
| course_approval_requests | 1 | status, payload(JSON), submitted_by |
| conversation_sessions | 8 | ig_user_id, status, messages(JSONB), extracted_data(JSONB), conversation_stage |
| dm_templates | 3 | trigger_type(enum), system_prompt, opening_message, qualification_fields(JSONB) |

### 5.3 Utility Tables (exist in DB, models in misc/ module)

| Table | Rows | Purpose |
|-------|------|---------|
| notifications | 102 | Legacy notifications (FK→auth.users, NOT eb_users) |
| user_push_tokens | 116 | FCM push tokens (FK→auth.users) |
| user_fcm_tokens | 0 | Duplicate FCM table |
| short_links | 21 | URL shortener (code→target_url) |
| chatbot_sessions | 0 | Website chatbot state |
| agent_endpoints | 0 | Phone agent extension mapping (agent_key→profile_id) |
| freelancers | 0 | Freelancer agents |
| freelance_managers | 0 | Freelancer managers |
| commission | 0 | Commission tiers |
| backlog_participants | 0 | Daily backlog standup tracking |
| user_profiles | 0 | Extended user profiles |
| domain_keyword_map | 0 | Course domain→keywords mapping |
| search_synonyms | 0 | Search expansion rules |
| stopwords | 0 | Search stopwords |

### 5.4 Employee Automation Tables (NEW — eb_* prefix)

| Table | Purpose |
|-------|---------|
| eb_file_ingestions | Central pipeline: any file (PDF, audio, image) → AI processing → structured output |
| eb_call_analyses | Call recording transcription, sentiment, quality scoring, AI summary |
| eb_employee_metrics | Daily/weekly/monthly KPI rollups per employee |
| eb_performance_reviews | Periodic reviews with AI-generated summaries |
| eb_employee_goals | Targets and progress tracking |
| eb_work_logs | Granular activity log (auto-captured from events) |
| eb_employee_patterns | AI-detected behavioral patterns (peak hours, call style, etc.) |
| eb_employee_schedules | Shifts, expected hours, leaves |
| eb_training_records | Training completion and skill tracking |

## 6. API Endpoints — 79 currently registered

All under `/api/v1`. Format: `METHOD /path → permission needed`

### Auth (/auth)
- `POST /login` — email+password → JWT tokens
- `POST /refresh` — refresh token → new tokens

### Users (/users) — requires users:*
- `GET /` (list, ?department), `GET /me`, `GET /{id}`, `POST /`, `PATCH /{id}`

### Students (/students) — requires students:*
- `GET /` (?counselor_id, ?search), `GET /{id}`, `POST /`, `PATCH /{id}`

### Cases (/cases) — requires cases:*
- `GET /` (?is_active, ?counselor_id, ?stage), `GET /{id}`, `POST /`, `PATCH /{id}`

### Applications (/applications)
- `GET /` (?case_id), `GET /{id}`, `POST /`, `PATCH /{id}`

### Documents (/documents)
- `GET /` (?entity_type, ?entity_id), `POST /`, `PATCH /{id}/verify`

### Tasks (/tasks)
- `GET /`, `GET /my`, `GET /{id}`, `POST /`, `PATCH /{id}`

### Events (/events) — read-only
- `GET /` (?entity_type, ?entity_id, ?event_type)

### Approvals (/approvals)
- `GET /`, `GET /{id}`, `POST /{id}/review`

### Notifications (/notifications)
- `GET /` (?is_read), `POST /read-all`, `PATCH /{id}/read`

### Workflows (/workflows)
- `GET /definitions`, `GET /instances`

### AI Artifacts (/ai-artifacts)
- `GET /`, `GET /{id}`, `POST /`

### Policies (/policies)
- `GET /`, `GET /{id}`, `POST /`, `PATCH /{id}`

### Leads (/leads) — read-only legacy
- `GET /` (?status, ?heat_status, ?assigned_to, ?search), `GET /{id}` (includes lead_info)

### Courses (/courses)
- `GET /`, `GET /search?q=`, `GET /{id}`

### Geography (/geography)
- `GET /countries`, `GET /countries/{id}`, `GET /cities`, `GET /cities/{id}`
- `GET /universities`, `GET /universities/{id}`, `GET /campuses`, `GET /campuses/{id}`

Plus: profiles, intakes, jobs, call-events, chat, payments, attendance, ig-sessions

## 7. Key Implementation Rules

### CRITICAL — Database Safety

1. **NEVER** run `DROP TABLE`, `CREATE TABLE` on existing tables — they have live data
2. **NEVER** modify legacy table schemas — Flutter apps depend on them
3. For NEW tables, use `eb_` prefix and create via Supabase migrations
4. SQLAlchemy models must match DB columns exactly (including typos like `diplay_name`, `work_expierience`, `course_deatails`)

### Every CUD Operation Must:

1. Check permissions via `require_perm(resource, action)` or `get_current_user`
2. Call `log_event()` to write to `eb_events` before `db.commit()`
3. Return proper errors (404/403/409/400 via `core.exceptions`)

### Pagination Convention:

- Default 20 per page, max 100
- Response shape: `{items: [...], total: int, page: int, size: int, pages: int}`

### CORS:

- `allow_origins=["*"]` in development
- `allow_credentials=True`

### Naming Conventions:

- Table names: `eb_*` for new tables, exact legacy names for old
- API paths: kebab-case (`/call-events`, `/ai-artifacts`)
- Pydantic schemas: `{Model}Out`, `{Model}Create`, `{Model}Update`
- Event types: `entity.action` (e.g., `student.created`, `case.stage_changed`)

## 8. Tech Stack Versions

```
fastapi==0.115.6          uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.36  asyncpg==0.30.0
alembic==1.14.0           pydantic[email]==2.10.3
pydantic-settings==2.7.0  python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4     python-multipart==0.0.19
celery[redis]==5.4.0       redis==5.2.1
httpx==0.28.1             pgvector==0.3.6
boto3==1.35.0             openai==1.58.0
```

## 9. What's Built vs What Needs Work

### ✅ Complete

- All 44 DB tables mapped to SQLAlchemy models
- 79 API endpoints registered and routed
- JWT auth + RBAC permission system
- Event logging infrastructure
- Pagination system
- Docker setup (API + Redis + Worker)
- 8 modules with full service layers (auth, users, students, cases, applications, documents, tasks, approvals)

### ⚠️ Needs Service Layers

These modules have routers with inline queries but no `service.py`:
courses, leads, notifications, events, workflows, profiles, geography, intakes, jobs, call_events, chat, payments, attendance, ai_artifacts, policies, ig_sessions

### 🆕 Needs Building

- **Employee automation module** — file ingestion pipeline, call analysis, metrics, reviews, patterns
- **Misc utility models** — 14 unmapped tables (short_links, agent_endpoints, freelancers, etc.)
- **Celery workers** — real task implementations (currently stubs)
- **OpenAI integration** — call transcription, PDF extraction, performance analysis
- **S3 integration** — actual file upload/download
- **Alembic migrations** — migration history not yet initialized
- **Tests** — no test suite yet
- **WebSocket** — real-time notifications

## 10. Vision — AI Company OS Roadmap

```
Phase 1: Copilot — AI assists humans (email summaries, draft replies, lead scoring)
Phase 2: Department Copilots — counselor next-best-action, processing email drafts
Phase 3: Controlled Autopilot — auto follow-ups, low-risk stage transitions
Phase 4: High Automation — AI-driven intake qualification, auto document validation
```

All AI actions go through the approval pipeline: **Draft → Approve → Execute → Logged Result**

The `eb_file_ingestions` + `eb_call_analyses` + `eb_employee_patterns` tables are the foundation for understanding employee working patterns and automating based on them.
