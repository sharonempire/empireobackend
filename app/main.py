from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
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

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(students_router, prefix=API_PREFIX)
app.include_router(cases_router, prefix=API_PREFIX)
app.include_router(applications_router, prefix=API_PREFIX)
app.include_router(documents_router, prefix=API_PREFIX)
app.include_router(tasks_router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)
app.include_router(approvals_router, prefix=API_PREFIX)
app.include_router(notifications_router, prefix=API_PREFIX)
app.include_router(workflows_router, prefix=API_PREFIX)
app.include_router(leads_router, prefix=API_PREFIX)
app.include_router(courses_router, prefix=API_PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
