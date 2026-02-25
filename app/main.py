from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.core.logging_config import setup_logging
from app.core.middleware import RequestIdMiddleware, BodySizeLimitMiddleware
from app.core.exceptions import http_exception_handler, unhandled_exception_handler, validation_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure structured logging
    setup_logging(settings.LOG_LEVEL)
    # Startup: verify DB connection
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    print(f"[{settings.APP_NAME}] Database connected. Server ready.")
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracing
app.add_middleware(RequestIdMiddleware)

# Reject bodies larger than 10 MB
app.add_middleware(BodySizeLimitMiddleware, max_body_size=10 * 1024 * 1024)

# Global error handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Mount all routers
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.students.router import router as students_router
from app.modules.cases.router import router as cases_router
from app.modules.applications.router import router as applications_router
from app.modules.documents.router import router as documents_router
from app.modules.tasks.router import router as tasks_router
from app.modules.events.router import router as events_router
from app.modules.approvals.router import router as approvals_router
from app.modules.notifications.router import router as notifications_router
from app.modules.workflows.router import router as workflows_router
from app.modules.leads.router import router as leads_router
from app.modules.courses.router import router as courses_router
from app.modules.profiles.router import router as profiles_router
from app.modules.intakes.router import router as intakes_router
from app.modules.jobs.router import router as jobs_router
from app.modules.call_events.router import router as call_events_router
from app.modules.chat.router import router as chat_router
from app.modules.payments.router import router as payments_router, webhook_router as payments_webhook_router
from app.modules.attendance.router import router as attendance_router
from app.modules.ig_sessions.router import router as ig_sessions_router
from app.modules.geography.router import router as geography_router
from app.modules.ai_artifacts.router import router as ai_artifacts_router
from app.modules.policies.router import router as policies_router
from app.modules.employee_automation.router import router as employee_automation_router
from app.modules.freelance.router import router as freelance_router
from app.modules.push_tokens.router import router as push_tokens_router
from app.modules.saved_items.router import router as saved_items_router
from app.modules.search.router import router as search_router
from app.modules.utility.router import router as utility_router
from app.modules.analytics.router import router as analytics_router
from app.modules.ai_copilot.router import router as ai_copilot_router
from app.modules.ws.router import router as ws_router
from app.core.rbac import include_router_with_default

API_PREFIX = "/api/v1"

# Auth router is special (login/refresh) — do not add global read requirement
app.include_router(auth_router, prefix=API_PREFIX)

# Include routers with a default 'read' permission enforced at router level.
include_router_with_default(app, users_router, prefix=API_PREFIX, resource="users")
include_router_with_default(app, students_router, prefix=API_PREFIX, resource="students")
include_router_with_default(app, cases_router, prefix=API_PREFIX, resource="cases")
include_router_with_default(app, applications_router, prefix=API_PREFIX, resource="applications")
include_router_with_default(app, documents_router, prefix=API_PREFIX, resource="documents")
include_router_with_default(app, tasks_router, prefix=API_PREFIX, resource="tasks")
include_router_with_default(app, events_router, prefix=API_PREFIX, resource="events")
include_router_with_default(app, approvals_router, prefix=API_PREFIX, resource="approvals")
include_router_with_default(app, notifications_router, prefix=API_PREFIX, resource="notifications")
include_router_with_default(app, workflows_router, prefix=API_PREFIX, resource="workflows")
include_router_with_default(app, leads_router, prefix=API_PREFIX, resource="leads")
include_router_with_default(app, courses_router, prefix=API_PREFIX, resource="courses")
include_router_with_default(app, profiles_router, prefix=API_PREFIX, resource="profiles")
include_router_with_default(app, intakes_router, prefix=API_PREFIX, resource="intakes")
include_router_with_default(app, jobs_router, prefix=API_PREFIX, resource="jobs")
include_router_with_default(app, call_events_router, prefix=API_PREFIX, resource="call_events")
include_router_with_default(app, chat_router, prefix=API_PREFIX, resource="chat")
include_router_with_default(app, payments_router, prefix=API_PREFIX, resource="payments")
include_router_with_default(app, attendance_router, prefix=API_PREFIX, resource="attendance")
include_router_with_default(app, ig_sessions_router, prefix=API_PREFIX, resource="ig_sessions")
include_router_with_default(app, geography_router, prefix=API_PREFIX, resource="geography")
include_router_with_default(app, ai_artifacts_router, prefix=API_PREFIX, resource="ai_artifacts")
include_router_with_default(app, policies_router, prefix=API_PREFIX, resource="policies")
include_router_with_default(app, employee_automation_router, prefix=API_PREFIX, resource="employee_automation")
include_router_with_default(app, freelance_router, prefix=API_PREFIX, resource="freelance")
include_router_with_default(app, push_tokens_router, prefix=API_PREFIX, resource="push_tokens")
include_router_with_default(app, saved_items_router, prefix=API_PREFIX, resource="saved_items")
include_router_with_default(app, search_router, prefix=API_PREFIX, resource="search")
include_router_with_default(app, utility_router, prefix=API_PREFIX, resource="utility")
include_router_with_default(app, analytics_router, prefix=API_PREFIX, resource="analytics")
include_router_with_default(app, ai_copilot_router, prefix=API_PREFIX, resource="ai_copilot")

# Payments webhook router — no RBAC dependency (Razorpay verifies via HMAC signature)
app.include_router(payments_webhook_router, prefix=API_PREFIX)

# WebSocket router — no RBAC dependency (auth is handled via token in URL path)
app.include_router(ws_router, prefix=API_PREFIX)


@app.get("/health")
async def health():
    """Liveness probe -- always returns 200 if the process is running."""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/ready")
async def ready():
    """Readiness probe -- checks DB and Redis connectivity."""
    checks = {}
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )
