# Empireo - Complete Project Documentation

> **Last Updated:** February 24, 2026 | **Version:** Frontend v1.0.7+14 | Backend v1.0
> **Database:** 73 tables, 260+ indexes, 65 triggers, 83 RLS policies

---

## PART 1 — EXECUTIVE SUMMARY

Empireo is a vertically integrated **study abroad + recruitment + processing** platform combining a Flutter-based student experience, a FastAPI-powered staff CRM (the Brain), and a Supabase PostgreSQL backend. The system orchestrates lead capture, profile building, case management, payments, AI-enhanced recommendations, and detailed audit trails.

### Key Numbers

| Metric | Value |
|---|---|
| Tables | 73 |
| Leads | 2,111 |
| Registered students/cases | 1,856 |
| Courses | 2,813 |
| University courses | 4,017 |
| Universities | 242 |
| Countries served | 10 |
| Call events | 17,410 |
| Chat conversations | 5,228 |
| Staff | 19 |

### Ecosystem Snapshot

- **Frontend:** Flutter app (508 Dart files, 120+ routes) used by students and guests.
- **Backend:** FastAPI (31 modules, 79+ endpoints) used by counselors, processors, managers.
- **Database:** Supabase PostgreSQL (73 tables, Realtime, Auth, Storage, Edge Functions).
- **Authentication:** Supabase Auth for students, JWT + RBAC for staff.

---

## PART 2 — SYSTEM ARCHITECTURE

### 2.1 Tech Stack

| Layer | Technologies / Versions |
|---|---|
| Frontend | Flutter/Dart ^3.9.2, Riverpod 2.6.1, GoRouter 16.0.0, Supabase Flutter 2.10.0, Firebase 3.8.0 |
| Backend | FastAPI 0.115.6, SQLAlchemy 2.0.36, asyncpg 0.30.0, Celery 5.4.0, Redis 7-alpine |
| Database | Supabase PostgreSQL 17 (ap-south-1, project ID ebgzlzemrargfahwokti) |
| AI | OpenAI GPT-4 (Python SDK 1.58.0) |
| Payments | Razorpay (live), Apple/Google IAP |

### 2.2 Infrastructure Diagram

- **Docker Compose:** Services `api` (FastAPI :8000), `redis` (6379), `worker` (Celery). Background tasks consume jobs from Redis.
- **Supabase Managed:** PostgreSQL, Auth, Storage (lead_details, resumes, user_images, chat_files), Realtime subscriptions, Edge Functions for course/job search and no-language options.
- **Goal:** Flutter clients call Supabase directly for student flows and route to backend via FastAPI for staff workflows and shared data.

### 2.3 Frontend Architecture

- **Project layout:** Feature-first (`features/{application,data,presentation}`) with providers, controllers, and widgets grouped by domain.
- **Routes:** 120+ by GoRouter, covering public, guest, onboarding, protected experiences, and deep links.
- **State:** Riverpod (StateNotifier, FutureProvider, StreamProvider, AsyncNotifier) orchestrates data between UI, repositories, Supabase/HTTP.
- **Data Flow:** UI binds to providers → controller delegates to repository → repository interacts with Supabase (auth, edge functions) or FastAPI via HTTP clients.
- **Infrastructure:** Shared providers for theme (`themeModeProvider`), connectivity, notifications, payments, guest mode, saved/applied lists.

### 2.4 Backend Architecture

- **Module pattern:** Each module contains `models.py`, `schemas.py`, `router.py`, `service.py`, `repository` logic. 31 modules exist; 8 have full service layers (users, students, cases, applications, documents, tasks, approvals, events).
- **Security:** JWT validation, RBAC middleware, request ID, pagination, error handlers, rate limiting.
- **Core features:** Logging (`log_event`), pagination utilities, exception hierarchy, middleware (RequestId, CORS), health probes (`/health`, `/ready`).
- **Async workers:** Celery uses Redis as broker for notifications/document processing, though workers are currently stubs.

---

## PART 3 — AUTHENTICATION (Both Systems)

### 3.1 Student Auth (Supabase Auth + Flutter App)

#### 3.1.1 Email/Password Login

- **Validation:** Email must match `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`, password non-empty.
- **API:** `Supabase.auth.signInWithPassword(email, password)`.
- **Post-login flow:** Clear caches, honor `redirect_after_login`, load profile from `leadslist`, check onboarding (`is_registered`), route based on `finder_type` (course/job) or welcome screens.
- **Error handling:** Maps Supabase `AuthException` codes (e.g., `email_not_confirmed`) to descriptive messages.
- **Token syncing:** Supabase handles JWT; FCM token stored in `user_push_tokens` table plus `leadslist.fcm_token` / `lead_info.fcm_token`.

#### 3.1.2 Email/Password Signup

- **Fields:** `full_name`, `email`, `password`, `confirm_password`, `terms_checkbox`.
- **Validation:** UI enforces 6+ chars; backend expects >=8 with uppercase/lowercase/number/special.
- **Flow:** `auth.signInWithOtp(email, shouldCreateUser: true, data: {...})` → 6-digit OTP → `auth.verifyOTP(type: OtpType.signup)` → `updatePassword()` → create profile record in `leadslist` (status "Lead creation", includes freelancer IDs from URL params).
- **Persistence:** Profile stored locally (SharedPreferences), FCM token synced.

#### 3.1.3 Password Reset (4-step)

1. Enter email → `auth.resetPasswordForEmail(email, redirectTo)` with redirect `your-app-scheme://reset-password`.
2. Enter OTP → `auth.verifyOTP(type: OtpType.recovery)`.
3. Set new password → `auth.updateUser(UserAttributes(password))` → `auth.signOut()`.
4. Success screen displayed.
- **Recovery detection:** App checks deep link for `access_token`, `refresh_token`, `type=recovery` and calls `setSession()`.

#### 3.1.4 Google Sign-In

- **Web:** Uses `GoogleWebCredential` (token pair) → `auth.signInWithIdToken(provider: OAuthProvider.google)`.
- **Mobile:** `GoogleSignIn.signIn()` → `account.authentication` → same Supabase call.
- **Scopes:** `email`, `profile`.
- **Client IDs:** Four (web, android debug, android release, iOS).
- **Errors:** `DEVELOPER_ERROR` (code 10), `CANCELLED`/`12500`, `NETWORK_ERROR` (code 7), `API_UNAVAILABLE` (code 8).

#### 3.1.5 Apple Sign-In

- Uses `sign_in_with_apple` package on iOS.
- Handles fallback email/name (Apple may omit) via `completeAppleSignIn(authResponse, fallbackEmail, fallbackName)`.

#### 3.1.6 Post-OAuth Flow (Google/Apple)

- Extracts email/name from response metadata; fallbacks provided for missing fields.
- Checks `leadslist` for profile; inserts new leads if necessary (source=Google/Apple, status step, includes freelancer IDs).
- Stores details in SharedPreferences, updates FCM token, returns `isNewUser` flag.

#### 3.1.7 Sign Out

- `auth.signOut()` + clear SharedPreferences (`isLoggedIn`, `userDetails`, `userId`, `onboarding`, `finderType`).
- Clears pending saved/applying data.

#### 3.1.8 Delete Account

- Determine lead ID from profile.
- DELETE cascades: `lead_info`, `leadslist`, `saved_courses`, `saved_jobs`, `applied_courses`, `applied_jobs`, `user_fcm_tokens`.
- Remove Supabase storage folders (`user_{leadId}` under `lead_info`, `resumes`, `user_images`).
- Delete Firebase FCM token, call Supabase REST `DELETE /auth/v1/user` with access token, clear SharedPreferences.

#### 3.1.9 Guest Mode

- `guestModeProvider.enableGuestMode()` → navigates to guest routes.
- Keeps `finder_type` selection.
- Disabled actions: saves, applies, chat, resume builder, notifications.
- Prompts sign-up when accessing protected flows.

### 3.2 Staff Auth (JWT + FastAPI)

#### 3.2.1 Login (`POST /api/v1/auth/login`)

- **Rate limit:** 10/min per IP (`rate:auth:login:{ip}` in Redis).
- **Input:** email (`EmailStr`), password (`str`).
- **Process:** Query `eb_users` by email → check `is_active` → hash/password verify → update `last_login_at` → issue tokens.
- **Events:** Log `auth.login_failed` on failure with metadata, `auth.login` on success.
- **Response:** `{ access_token, refresh_token, token_type: "bearer" }`.

#### 3.2.2 Token Management

- **Access Token:** HS256 JWT, 480-minute expiry, payload `{ sub: user_id, type: "access" }`.
- **Refresh Token:** HS256 JWT, 30-day expiry, payload `{ sub: user_id, type: "refresh" }`.
- **Password hashing:** SHA-256 pre-hash + bcrypt.
- **Storage:** SHA-256 hash stored in `eb_refresh_tokens` (`token_hash`, `family_id`, `is_revoked`, etc.).
- **Rotation:** Each refresh token has `family_id` (UUID). Presentation of revoked token triggers family revocation and logs security event.

#### 3.2.3 Refresh (`POST /api/v1/auth/refresh`)

- **Rate limit:** 60/min per IP.
- **Flow:** Decode JWT → hash → lookup token. Revoked token triggers family invalidation (`reuse_detected`). Valid token is rotated with new refresh/access tokens (same family, old token revoked with reason `rotated`).

#### 3.2.4 Logout / Logout All / Change Password

- `POST /auth/logout`: revoke current token (`reason=logout`).
- `POST /auth/logout_all`: revoke all tokens for user (`reason=logout_all`), returns count.
- `POST /auth/change_password`: verify current password → hash new → revoke all tokens (`reason=password_changed`).

#### 3.2.5 Bootstrap (`POST /auth/bootstrap`)

- Requires `BOOTSTRAP_TOKEN` header, ensures zero existing users.
- Creates first admin user and associates initial role.
- One-time guard.

### 3.3 RBAC System

- **Roles:** admin, manager, counselor, processor, viewer.
- **Permissions:** 44 resource-action pairs (e.g., `students:create`, `cases:update`, `approvals:review`).
- **Schema:** `eb_users` → `eb_user_roles` → `eb_roles` → `eb_role_permissions` → `eb_permissions`.
- **Checks:** `has_permission(db, user_id, resource, action)` composes join chain.
- **Routing helpers:** `include_router_with_default` binds permission checks automatically.
- **Endpoint protection:** `Depends(require_perm("resource", "action"))` used for create/update/delete actions.

---

## PART 4 — FRONTEND FEATURES (Flutter App)

### 4.1 Course Finder

#### 4.1.1 Data Model (Course — 55+ columns)

Fields include `id`, `courseName`, `university`, `level`, `duration`, `mode`, `delivery`, `description`, `fees`, `studyType`, `country`, `city`, `createdAt`, `updatedAt`, `fieldOfStudy`, `englishProficiency`, `intakes`, `language`, `universityLogo`, `address`, `applicationFee`, `tuitionFee`, `depositAmount`, `currency`, `minimumPercentage`, `ageLimit`, `academicGap`, `maxBacklogs`, `workExperience`, `requiredSubjects`, `specialRequirements`, `overallMatchPercent`, `eligibilityMatchPercent`, `isEligible`, plus metadata and JSONB blobs mirrored from Supabase edges.

#### 4.1.2 Search & API

- Primary data source: Supabase Edge Function `/course-finder`.
- Parameters: `searchQuery`, `industry`, `isIndustryInFilters`, `level`, `intake`, `countries`, `universities`, `cities`, `deliveryModes`, `languages`, `fieldOfStudies`, `programTypes`, `disciplines`, `specializations`, `englishProficiencies`, `minFees`, `maxFees`, `page`, `pageSize`, `studentId`.
- Response: `{ meta: { next_cursor, has_next, total_pages, total_courses }, courses: [...], filters: {...} }`.
- Voice search via `speech_to_text` package.
- AI natural language queries handled by `openai_course_service.dart` hitting GPT-4.

#### 4.1.3 Filter System (15+ dimensions)

- Cascading filters: Country → City → University (dependent lists).
- Program levels include Undergraduate, Postgraduate, Doctoral, Professional with contextual submenus.
- Dimensions: Mode (Full-time, Part-time, Online), Delivery (On-campus, Online, Hybrid), Duration range, Instruction Language, English proficiency requirement, Tuition fee range (INR conversion), Field of study, Specializations, Intakes (normalized month names). Each filter includes search-enabled selection and case-insensitive, deduped display.

#### 4.1.4 Pagination

- `pageCache` maps `int` page numbers to `List<Course>`.
- Cursor-based pagination used when API supplies `next_cursor`; fallback to page indexing.
- Authenticated flows show 9 per page; home page uses 12.
- Cached pages render immediately while fresh data fetches if missing.

#### 4.1.5 Eligibility Matching

- Backend returns `overall_match_percent`, `eligibility_match_percent`, `is_eligible` per course.
- Flutter compares student profile (education, tests, experience, budget) to course specs using match logic from `course_match_service`.

#### 4.1.6 No-Language-Test Courses

- Separate Edge Function `no_language_course` accepts `{ student_id, limit, page }`.
- UI maintains `noLanguageTestCourses` and `isLoadingNoLanguageTest` states.
- Results include courses where student satisfies requirements without English tests.

#### 4.1.7 Course Details Page

Displays comprehensive course attributes: name, university/logo, country/city/address, level/mode/delivery/duration/language, field of study, English proficiency, intakes list, match `%`, fees (application + tuition + deposit with INR conversion via `CurrencyConverter`), minimum GPA/percentage, age limit, academic gap, max backlogs, work experience, required subjects, special requirements.

#### 4.1.8 Save / Apply Flow

- **Save:** `SavedCoursesNotifier` calls repository → API writes to `saved_courses(user_id, course_id, course_details JSONB)`.
- **Apply:** `applyToCourse()` updates `applied_courses` with status and timestamps; state clears `applyingCourseId` after completion.
- `appliedCourseIds` set keeps render-time quick lookups.

### 4.2 Job Finder

#### 4.2.1 Data Model

`JobModel` fields: `id`, `jobProfileId`, `jobInformation`, `jobDetails`, `locationSalaryDetails`, `requiredQualification`, `status`, `createdAt`, `updatedAt`, `companyName`. JSONB accessors parse nested data for display (`jobTitle`, `jobType`, experience, salary range, languages, responsibilities, benefits, education, skills, location).

#### 4.2.2 Search & Filters

- Free text search covers job title, company, keywords.
- Filters: Country, City, State, Job type (Full-time/Part-time/Contract/Internship), Work mode (On-site/Remote/Hybrid), Industry, Salary range, Experience level, Education, Skills.
- AI Job Assistant uses OpenAI to translate conversational intent into filters.

#### 4.2.3 Save / Apply

- `saved_jobs` table stores `job_details` JSONB per user.
- `applied_jobs` captures `candidate_name`, `status`, application timestamp alongside job details.

### 4.3 Profile & Onboarding

#### 4.3.1 Profile Completion Sections (6 sections)

Each section ~16.7% completion:
1. **Basic Info:** First name, Last name, DOB, Nationality, Phone, Current country/city.
2. **Education:** Institutions, degrees, fields, start/end/graduation dates, GPA.
3. **Work Experience:** Companies, titles, dates, descriptions, current job flag, multi-entry.
4. **Budget:** Range, currency, funding source.
5. **English Proficiency:** Test type (IELTS/TOEFL/Duolingo/PTE), score, test date.
6. **Documents:** Resume, passport, certificates, test scores, bank statements.

#### 4.3.2 Entry Points

- **Resume Upload:** PDF/image uploaded → AI parser auto-fills education/work experience.
- **AI Chatbot:** `chatbot_page_mobile.dart` handles conversational profile building, saving after each response.
- **Manual forms:** Standard forms for each section.

#### 4.3.3 Data Persistence

- `leadslist`: Basic info, `draft_status`, `is_registered`, `profile_completion`, status flags.
- `lead_info`: JSON columns (e.g., `basic_info`, `education`, `work_expierience` [typo preserved], `budget_info`, `preferences`, `english_proficiency`, `documents`).
- Documents stored in Supabase bucket `lead_details`.

#### 4.3.4 Completion Tracking

- `completionPercent = (completed_sections / total_sections) * 100`.
- Profile considered ready when basic info, education, and work experience exist.
- `draft_status` toggles between `completed` and `draft`; onboarding marked via `leadslist.is_registered`.

### 4.4 Chat System

#### 4.4.1 Data Models

`ChatMessage` fields: `id`, `text`, `timestamp`, `isUser`, `isRead`, `status`, attachments metadata, `messageType` (text/voice/image/video/file/course/job), course/job-specific data (e.g., `courseId`, `courseDescription`, `jobTitle`, `salaryRange`).

`ChatConversation`: `id`, `leadUuid`, assigned counselor, `lastMessageText`, timestamps, unread counts, participant metadata.

#### 4.4.2 Real-time Implementation

- Uses `Supabase.from('chat_messages').stream` filtered by `conversation_id`.
- Automatic reconnection after 3 seconds on error.
- Unread counts maintained in `chat_conversations.unread_count_user` and `_assigned` for staff; marking read updates both tables.

#### 4.4.3 Message Types

- **Text:** plain string.
- **Voice:** `.m4a`, stored in `chat_files`, `voiceDuration` recorded.
- **Image:** jpg/png/gif/heic/heif etc.
- **Video:** mp4/mov/avi/mkv/webm/flv/wmv/3gp/m4v.
- **File:** pdf/doc/docx/txt/mp3/wav/aac/ogg/flac/wma.
- **Course/Job:** Embedded data (note typo `course_deatails`).

#### 4.4.4 File Upload

- FilePicker/ImagePicker → read bytes → `chat_files/{conversationId}/{timestamp}-{filename}` → get signed URL → create message with metadata (name, type, size).

#### 4.4.5 Notifications

- Determined by `senderName` and `messageType`.
- Flutter Local Notifications used; payload includes `conversationId` for deep linking.
- Preview truncated to 100 chars, type-specific label ("Voice message", "Photo", etc.).

### 4.5 Resume Builder

#### 4.5.1 Data Model

`ResumeProfile`: `personalInfo`, `professional_summary`, sections for education, experience, skills, certifications, languages.
- **EducationItem:** `school_name`, `degree`, `field_of_study`, `start_date`, `end_date`, `description`.
- **ExperienceItem:** `company_name`, `job_title`, `start_date`, `end_date`, `description`, `skills[]`.
- **CVBlock:** `title`, `description`, `date_range`.

#### 4.5.2 Templates

- **Stellar:** Modern layout.
- **Eclipse:** Professional layout.
- Pagination engine handles multiple pages, overflow gracefully.

#### 4.5.3 Features

- Real-time preview, template switching, reorder sections.
- AI assistance (OpenAI) for summaries and bullet points.
- PDF generation, print support (A4), dark mode editor.

### 4.6 Payments

#### 4.6.1 Razorpay (Web + Android)

- Order creation via `POST https://api.razorpay.com/v1/orders` with Basic Auth (`key:secret`).
- Receipt format `rcpt_{timestamp}{randomSuffix}` (≤40 chars).
- Amount specified in paise (INR × 100).
- Live keys: `rzp_live_RytUd5wRmRGjzw` / `R3WUgMfwvPMFlmgt831FP7T2`.

#### 4.6.2 In-App Purchases (iOS)

- StoreKit 2.
- Premium types: `job`, `course`, `general`.
- Transactions logged in Supabase `payments` table.

#### 4.6.3 Premium Benefits

- **Course Premium:** advanced filters/details.
- **Job Premium:** premium listings/applications.
- **General Premium:** enhanced platform capabilities, notifications, AI perks.

### 4.7 Notifications

#### 4.7.1 Firebase Flow

- `FirebaseMessaging.instance.getToken()` stored locally + `user_fcm_tokens`.
- Foreground: `onMessage.listen()` triggers local notifications or UI badges.
- Background: `onBackgroundMessage` (top-level) displays local notice.
- Terminated: `onMessageOpenedApp.listen()` deep links.
- Channel: `empireo_notifications` (importance high, vibration, badge).

#### 4.7.2 Real-time Updates

- PostgreSQL changes on `notifications` table propagate via realtime listeners.
- Unread counts refreshed immediately once inserts occur.

### 4.8 Guest Mode

- Routes: `/guest-choice` → `/guest-select-country` → `/guest/courses` or `/guest/jobs` → detail views → AI assistant.
- API: `getGuestCourseById()` (no match or sensitive data).
- Limitations: no eligibility matching, saves, applications; certain APIs return limited `totalPages` if data incomplete.
- Protected actions prompt sign-up.

### 4.9 Routing (120+ routes)

#### 4.9.1 Route Map

- **Public:** `/SplashScreen`, `/login`, `/signup`, `/welcome`, `/terms-and-conditions`, `/privacy-policy`, `/delete-account`, `/error/*`.
- **Guest:** `/guest-home`, `/guest-choice`, `/guest-select-country`, `/guest/select`, `/guest/courses/`, `/guest/jobs/`.
- **Protected:** `/home`, `/course`, `/course/:slug`, `/job`, `/job/job-details/:id`, `/chat`, `/chat/:conversationId`, `/notifications`, `/applications`, `/settings`, `/savedJobs`, `/savedCourses`, `/resume-builder`, `/smartProfile`, `/chatbot`, `/upgrade-page`, `/document-upload`.
- **Profile:** `/main-mobile/ProfileCompletion/*` covering `PersonalInfoPage`, `EducationPage`, `WorkExperiencePage`, `BudgetPage`, `PreferencesPage`, `DocumentUpload`, `englishProficiency`, `Profilecompleted`.

#### 4.9.2 Auth Guard

- Public routes allowed for everyone.
- Recovery tokens bypass guard to allow password reset.
- Logged-in users proceed; otherwise redirect to `/login`.
- Onboarding guard checks `leadslist.is_registered` before allowing access.
- Deep links handled (e.g., `/chat/:conversationId`, `/course/:slug` via `UrlSlugHelper`).

### 4.10 Shared Infrastructure

#### 4.10.1 API Keys (`keys.dart`)

- Supabase URL: `https://ebgzlzemrargfahwokti.supabase.co`, Supabase Anon Key (Supabase JWT).
- Dev Supabase: `https://obwbblumxlktdjtktkde.supabase.co`.
- Google Sign-In: 4 client IDs (web, android debug, android release, iOS).
- OpenAI: `sk-proj-EbYjNvml5M01iqR1Mfz_...` (GPT-4).
- Google Places: `AIzaSyBTGn0b062gcIMePz-1dqrW2bYFWuacdNs`.
- Razorpay: live key/secret as above.

#### 4.10.2 Storage Buckets

1. `lead_details` – Student documents (passports, transcripts, certificates).
2. `resumes` – Generated resume PDFs from resume builder.
3. `user_images` – Profile photos.
4. `chat_files` – Chat attachments (voice, image, video, docs).

#### 4.10.3 State Management (Riverpod)

Providers cover:
- `themeModeProvider`, `connectivityProvider`, `userRealtimeProvider` (Supabase Realtime), `courseControllerProvider`, `jobControllerProvider`, `chatControllerProvider`, `chatListControllerProvider`, `paymentControllerProvider`, `notificationServiceProvider`, `guestModeProvider`, `savedCoursesProvider`, `appliedCoursesProvider`, `savedJobsProvider`, `appliedJobsProvider`.

---

## PART 5 — BACKEND API (FastAPI)

### 5.1 Modules with Full Service Layers

#### 5.1.1 Users Module

- **Table:** `eb_users` (UUID `id`, `email` unique, `phone`, `full_name`, `hashed_password`, `department`, `is_active`, `profile_picture`, `caller_id`, `location`, `countries` JSONB, `last_login_at`, `legacy_supabase_id` unique, `created_at`, `updated_at`).
- **Relationships:** `user_roles` → `roles` (exports list of role names).
- **Endpoints:** `GET /users` (paginated, filter `department`), `GET /users/me`, `GET /users/{id}`, `POST /users` (requires `users:create`, checks email uniqueness, assigns roles), `PATCH /users/{id}` (`users:update`, can reassign roles by deleting/inserting linking table).

#### 5.1.2 Students Module

- **Table:** `eb_students` (UUID, `lead_id` FK to `leadslist`, `full_name`, `email`, `phone`, DOB, nationality, passport info, education level/details JSONB, preferred programs/countries JSONB, `assigned_counselor_id`, `assigned_processor_id`, timestamps).
- **Relationships:** Cases, `counselor`, `processor` (selectin loads).
- **Search:** ILIKE on `full_name`, `email`, `phone`.
- **Endpoints:** list (`?counselor_id`, `?search`), get, create (`students:create`), update (`students:update`).

#### 5.1.3 Cases Module

- **Table:** `eb_cases` (UUID, `student_id`, `case_type`, `current_stage`, `priority`, assigned staff IDs, `target_intake`, `notes`, `is_active`, `closed_at`, `close_reason`, timestamps).
- **Stages:** `initial_consultation`, `documents_pending`, `documents_collected`, `university_shortlisted`, `applied`, `offer_received`, `offer_accepted`, `visa_processing`, `visa_approved`, `visa_rejected`, `travel_booked`, `completed`, `on_hold`, `cancelled`.
- **Validation:** Stage must be in `VALID_STAGES`; invalid stage triggers `BadRequestError`.
- **Close flow:** Setting `is_active=false` auto-sets `closed_at`.
- **Events:** Stage changes log `case.stage_changed`; other updates log `case.updated`.
- **Endpoints:** list (`?is_active`, `?counselor_id`, `?stage`), get, create (`cases:create`), update (`cases:update`).

#### 5.1.4 Applications Module

- **Table:** `eb_applications` (UUID, `case_id`, `university_name`, `university_country`, `program_name`, `program_level`, `status`, `submitted_at`, `response_received_at`, `offer_deadline`, `offer_details` JSONB, `notes`, timestamps).
- **Offer JSON:** `{ offer_status, tuition_fee: { amount, currency }, scholarship: { amount, percentage }, acceptance_deadline, conditions: [], documents_required: [] }`.
- **Endpoints:** list (`?case_id`), get, create (`applications:create`), update (`applications:update`).

#### 5.1.5 Documents Module

- **Table:** `eb_documents` (UUID `id`, `entity_type`, `entity_id`, `document_type`, `file_name`, `file_key`, `file_size_bytes`, `mime_type`, `uploaded_by`, `is_verified`, `verified_by`, `verified_at`, `notes`, `created_at`).
- **Polymorphic:** `entity_type` indicates `student`, `case`, `application`, `user`.
- **Verification:** `PATCH /documents/{id}/verify` toggles `is_verified`, sets `verified_by`, `verified_at`.
- **Endpoints:** list (`?entity_type`, `?entity_id`), create (`documents:create`), verify (`documents:update`).

#### 5.1.6 Tasks Module

- **Table:** `eb_tasks` (UUID, polymorphic `entity_type`/`entity_id`, `title`, `description`, `task_type`, assigned/created by `eb_users`, `due_at`, `priority`, `status`, timestamps).
- **Lifecycle:** Status update to `completed` sets `completed_at` automatically.
- **Sort:** `due_at ASC NULLS LAST`, `created_at DESC`.
- **Endpoints:** list (`?assigned_to`, `?status`, `?entity_type`, `?entity_id`), `GET /tasks/my` (assigned to current user), get, create (`tasks:create`, sets `created_by`), update (`tasks:update`).

#### 5.1.7 Approvals Module

- **Tables:** `eb_action_drafts` (action tracking with JSON payload & metadata) and `eb_action_runs` (executions for each draft).
- **Flow:** Drafts start `pending_approval`, reviewers `approve`/`reject`; invalid transitions raise `BadRequestError`.
- **Endpoints:** list (`?status`), get, `POST /approvals/{id}/review` (requires `approvals:review`).

#### 5.1.8 Events Module (Read-Only)

- **Table:** `eb_events` (immutable audit log: `event_type`, `actor_type`, `actor_id`, `entity_type`, `entity_id`, `metadata`, `created_at`).
- **Endpoints:** `GET /events` with filters `entity_type`, `entity_id`, `event_type`, ordered by `created_at DESC`.

### 5.2 Read-Only Modules (13 modules)

#### 5.2.1 Leads

- Tables: `leadslist` (~40+ columns) and `lead_info` (JSON fields, `interest_embedding` vector, `profile_text`, `fcm_token`).
- Fields: `id`, `name`, `email`, `phone`/`phone_norm`, `source`, `status`, `lead_tab` enum (`student`, `job`), `assigned_to`, `draft_status`, `country_preference` array, `is_registered`, `user_id`, `finder_type`, `is_premium_jobs`, `is_premium_courses`, `changes_history` JSONB, etc.
- Search: ILIKE on `name`, `email`, `phone_norm`.
- Schemas: `LeadOut`, `LeadInfoOut`, `LeadDetailOut`, `LeadSummaryOut`.

#### 5.2.2 Courses

- Table `courses` (68+ columns) and `university_courses` (4,017 rows, mirrored with `source_key`, `university_image`, international tuition fees).
- Columns include program identifying data, fees (`application_fee`, `tuition_fee`, `deposit_amount` stored as text), requirements (`english_proficiency`, `minimum_percentage`, `age_limit`, `academic_gap`, `max_backlogs`, `work_experience_requirement`), structured blobs (`required_subjects`, `intakes`, `links`, `media_links`).
- Search: `embedding` (VECTOR with HNSW), `search_text`, `search_vector` (tsvector), `domain`, `keywords`, `domain_tags` arrays, normalized fields (`program_level_normalized`, `english_proficiency_normalized_v2`).
- Endpoints: list with filters, search by `q`, `GET /course/{id}`.

#### 5.2.3 Geography

- Tables: `countries` (10 rows, includes `cities` JSONB, `top_attractions`, `commission`), `cities` (152 rows, includes `universities` JSONB), `universities` (242 rows), `campuses` (50 rows with `facilities`, `contacts`, `courses`).
- Endpoints: `/countries`, `/countries/{id}`, `/cities`, `/cities/{id}`, `/universities`, `/universities/{id}`, `/campuses`, `/campuses/{id}`.

#### 5.2.4 Other Read-Only Modules

- **Profiles:** `profiles` (21 rows, `diplay_name` typo, `profilepicture`, `user_type`, `designation`, `countries`, `callerId`).
- **Intakes:** `intakes` table (26 entries, JSON fields for universities/courses/fee info).
- **Jobs:** `job_profiles`, `jobs` (13 entries), `applied_jobs` (35), `jobs_countries` (14).
- **Call Events:** 17,410 rows storing `event_type`, `call_uuid`, caller/agent numbers (normalized), `duration`, `recording_url`, `call_date` with filters.
- **Chat:** `chat_conversations` (5,228 rows) + `chat_messages` (243 rows, includes `course_deatails` typo). Default pagination 50 messages per page.
- **Payments:** `payments` (119 rows) capturing amounts, currency, status, method, transaction IDs, `payment_details` JSONB.
- **Attendance:** `attendance` (300 rows) storing check-in/out times as TEXT, `attendance_status`, `employee_id` FK to `profiles`.
- **IG Sessions:** `conversation_sessions` (8), statuses, `messages` JSONB, `extracted_data`, `conversation_stage` (greeting → qualification → follow_up → handoff), `dm_templates` (3 entries with triggers, prompts, qualification schema).
- **Notifications:** `eb_notifications` with read tracking; bulk `POST /read-all` updates `is_read`.
- **Workflows:** `eb_workflow_definitions` (stages/transitions JSONB) and `eb_workflow_instances` (current stage, `history`).
- **AI Artifacts:** `eb_ai_artifacts` captures AI outputs (`artifact_type`, `model_used`, tokens, output JSONB, confidence). `POST` endpoint logs artifacts.
- **Policies:** `eb_policies` (title, category, content, department, `is_active`, auto-incremented `version`, embedding vector for RAG). Full CRUD available.

### 5.3 Employee Automation Module

Nine tables already exist but no endpoints yet:
1. `eb_file_ingestions` – pipeline metadata for uploads/email/call recordings, statuses, parsed data.
2. `eb_call_analyses` – call_event FK, transcription, sentiment, quality, professionalism, summary, topics, action items.
3. `eb_employee_metrics` – aggregated daily/weekly/monthly metrics (calls, leads, documents, tasks, performance).
4. `eb_performance_reviews` – review metadata, AI summaries, comparison data.
5. `eb_employee_goals` – track goals with `tracking_query`.
6. `eb_work_logs` – activity timelines referencing events.
7. `eb_employee_patterns` – patterns with confidence scores.
8. `eb_employee_schedules` – schedule definitions per day/shift.
9. `eb_training_records` – training status and certificates.

### 5.4 Core Infrastructure

#### 5.4.1 Pagination

- `PaginatedResponse[T]` returns `items`, `total`, `page`, `size`, `pages`.
- Defaults: `page_size=20`, `max=100`.
- Utilities `paginate(db, query, page, size)` and `paginate_metadata(total, page, size)` compute offsets.

#### 5.4.2 Event Logging

- `log_event` must run before commits, capturing `event_type` (e.g., `student.created`, `case.stage_changed`, `auth.login_failed`), actor info, metadata.
- Stored in `eb_events`.

#### 5.4.3 Error Handling

- Custom errors return consistent payloads: `{ error: true, status_code, detail, request_id }`.
- Exceptions: `NotFoundError`, `ForbiddenError`, `ConflictError`, `BadRequestError`.

#### 5.4.4 Rate Limiting

- Redis-backed `limit_key` increments with expiration.
- Applies to login (10/min) and token refresh (60/min).

#### 5.4.5 Middleware

- `RequestIdMiddleware` adds `X-Request-ID`, logs method/path/status/duration.
- CORS configured (`allow_origins=[* `allow_origins=["*"]`, `allow_credentials=True`.

#### 5.4.6 Health Probes

- `GET /health` always returns OK (liveness).
- `GET /ready` runs `SELECT 1` against Postgres and `PING` Redis (readiness).

---

## PART 6 — DATABASE (Complete Schema)

### 6.1 Statistics

- 73 public tables, 260+ indexes, 65 triggers, 83 Row-Level Security policies.
- 47 foreign key relationships.
- Largest tables: `call_events` (17,410 rows), `chat_conversations` (5,228), `university_courses` (4,017), `courses` (2,813), `leadslist` (2,111).
- 23 tables currently empty (mostly automation/utility tables without data yet).

### 6.2 Enum Types

- `leadtab`: `student`, `job`.
- `module_type`: e.g., `notification`, `chat`, `application`.
- `application_status_enum`: `applied`, `not_applied`, `pending`, `accepted`, `rejected` (used in job application flows).

### 6.3 Key Indexes

- **Vector (HNSW):** `courses.embedding`, `university_courses.embedding`, `lead_info.interest_embedding` (using `vector_cosine_ops`).
- **Full-text (GIN):** `courses.search_vector` (tsvector), trigram indexes on `program_name`, `university`, `field_of_study`.
- **Composite:** `(employee_id, period_type, period_start)`, `(user_id, status)`, `(assigned_to, status)`, `(entity_type, entity_id)`.
- **Performance:** `phone_norm` on `leadslist` + `call_events`, `created_at` on major audit tables.

### 6.4 RLS Policies

- **Open tables:** `profiles`, `leadslist`, `courses`, `countries`, `cities`, `universities`, `campuses` (for legacy Flutter compatibility).
- **Authenticated-only:** All `eb_*` tables require JWT auth.
- **User-scoped:** `applied_courses`, `user_push_tokens`, `eb_notifications` restrict rows to matching `user_id`.
- **Immutable:** `eb_events` disallows UPDATE/DELETE via policies.

### 6.5 Triggers (65 total)

- **Lead management:** Round-robin counselor assignment, fresh lead enforcement, duplicate lead detection/blocking.
- **Sync:** Bidirectional sync between `lead_info` and `leadslist`, automatic country enrichment.
- **Audit:** `eb_log_event()` invoked on core table CUD.
- **Automation:** Case progression triggers, auto-create case when student inserted, notify on application status transitions.
- **Search:** On insert/update, `courses.search_vector` rebuilt via triggers.
- **Normalization:** Phone number normalization, timestamp updates.

### 6.6 Known Schema Typos (must preserve)

- `profiles.diplay_name` (legacy typo used by Flutter).
- `lead_info.work_expierience` (typo, preserved for compatibility).
- `chat_messages.course_deatails` (typo in column name retained for chat payloads).

---

## PART 7 — THIRD-PARTY INTEGRATIONS

| Service | Purpose | Config / Keys | Used By |
|---|---|---|---|
| Supabase | DB, Auth, Storage, Realtime, Edge Functions | Project `ebgzlzemrargfahwokti` (ap-south-1) | Frontend + Backend |
| Firebase | FCM push notifications | Android: `com.empireo.app`, iOS: `com.example.empireo` | Frontend |
| Google Sign-In | OAuth | 4 client IDs (web, android debug/release, iOS) | Frontend |
| Apple Sign-In | OAuth (iOS) | `sign_in_with_apple` package configuration | Frontend |
| Razorpay | Payments (India) | Live key `rzp_live_RytUd5wRmRGjzw`, secret `R3WUgMfwvPMFlmgt831FP7T2` | Frontend |
| Google/Apple IAP | In-app purchases | StoreKit 2 + Google Play Billing configs | Frontend |
| OpenAI GPT-4 | AI recommendations, resume parsing, profile parsing | Key `sk-proj-EbYjNvml5M01iqR1Mfz_...` | Frontend + Backend |
| Google Places | University imagery | `AIzaSyBTGn0b062gcIMePz-1dqrW2bYFWuacdNs` | Frontend |
| AWS S3 | File storage (configured but unused) | Credentials in `.env` | Backend |
| Redis | Cache, rate limiting, Celery broker | `localhost:6379` inside Docker | Backend |

---

## PART 8 — USER JOURNEYS

### Student (Course Seeker)

1. Download app / visit web.
2. Browse as guest or sign up (email/Google/Apple + OTP).
3. Verify email via OTP or OAuth.
4. Upload resume (AI parser) or fill profile manually (6 sections).
5. Search courses (text, voice, AI) with 15+ filters.
6. View eligibility match scores, no-language-test options.
7. Save courses for later.
8. Apply to courses (tracks in database, statuses updated).
9. Track applications, chat with counselor.
10. Pay for premium features (Razorpay, IAP).
11. Build resume with AI + PDF export.

### Job Seeker

1. Sign up/Login via Supabase.
2. Select Job Finder path.
3. Search jobs (filters include salary, location, type, experience).
4. Use AI assistant for recommendations.
5. Save/apply to jobs.
6. Track applications and chat with staff.

### Counselor (Staff)

1. JWT login.
2. `GET /students?counselor_id=me` to review caseload.
3. `GET /cases?counselor_id=me` to monitor progress.
4. `PATCH /cases/{id}` to transition stages with `case.stage_changed` events.
5. `POST /tasks` for follow-ups.
6. `POST /applications` to create application records.
7. `PATCH /documents/{id}/verify` for verifications.
8. All actions emit audit logs.

### Processor (Staff)

1. JWT login.
2. `GET /cases?processor_id=me`.
3. `PATCH /applications/{id}` for updates.
4. Manage documents and verify assets.
5. Update case stages and create tasks.
6. Escalate via approvals when required.

---

## PART 9 — CURRENT STATE & ROADMAP

### Complete

- **Flutter app:** 508 files, 120+ routes, course/job finder, profile, chat, resume builder, payments, notifications, guest mode, AI assistants.
- **Backend:** 79+ endpoints, 31 modules, JWT authentication, RBAC, audit logging, approvals, paginated helpers, error handling.
- **Database:** 73 tables, 260+ indexes, 65 triggers, 83 RLS policies.

### Needs Work

1. 13 backend modules still inline-query only; need service layers.
2. Employee automation tables exist but lack API/business logic.
3. Celery workers are placeholders (notifications/document processing need implementation).
4. OpenAI backend integration configured but unused.
5. S3 uploads configured, not wired.
6. Alembic migrations not initialized.
7. Tests pending (unit/integration).
8. WebSocket layer not built yet.
9. 14 utility tables missing ORM models.

### AI Company OS Roadmap

- **Copilot:** AI email summaries, response drafts, lead scoring.
- **Department Copilots:** Counselor next-best-action, processor email drafts.
- **Controlled Autopilot:** Auto follow-ups, low-risk stage transitions.
- **High Automation:** AI intake qualification, auto document validation.
- All AI actions flow through `eb_action_drafts` → review/approve → `eb_action_runs` → logs.

---

## VERIFICATION STEPS

1. `ls -la EMPIREO_COMPLETE_DOCUMENTATION.md` (confirm file exists).
2. `wc -l EMPIREO_COMPLETE_DOCUMENTATION.md` (should exceed 800 lines).
3. `grep "## PART" EMPIREO_COMPLETE_DOCUMENTATION.md` (ensure all PART sections exist).

