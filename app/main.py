from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.core.middleware import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# Register routers
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.leads.router import router as leads_router
from app.modules.students.router import router as students_router
from app.modules.cases.router import router as cases_router
from app.modules.applications.router import router as applications_router
from app.modules.documents.router import router as documents_router
from app.modules.conversations.router import router as conversations_router
from app.modules.tasks.router import router as tasks_router
from app.modules.events.router import router as events_router
from app.modules.approvals.router import router as approvals_router
from app.modules.courses.router import router as courses_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(leads_router, prefix="/api/v1/leads", tags=["Leads"])
app.include_router(students_router, prefix="/api/v1/students", tags=["Students"])
app.include_router(cases_router, prefix="/api/v1/cases", tags=["Cases"])
app.include_router(applications_router, prefix="/api/v1/applications", tags=["Applications"])
app.include_router(documents_router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(conversations_router, prefix="/api/v1/conversations", tags=["Conversations"])
app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(events_router, prefix="/api/v1/events", tags=["Events"])
app.include_router(approvals_router, prefix="/api/v1/approvals", tags=["Approvals"])
app.include_router(courses_router, prefix="/api/v1/courses", tags=["Courses"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.APP_NAME}
