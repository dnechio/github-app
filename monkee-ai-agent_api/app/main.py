from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import connect_db, disconnect_db
from app.api.v1.agents.chat import router as agents_router
from app.api.v1.auth.session import router as auth_router
from app.api.v1.files.router import router as files_router
from app.api.v1.pipelines.router import router as pipelines_router
from app.api.v1.admin.agents import router as admin_agents_router
from app.api.v1.admin.knowledge_bases import router as admin_kbs_router
from app.api.v1.admin.pipelines import router as admin_pipelines_router
from app.api.v1.admin.tools import router as admin_tools_router
from app.api.v1.admin.users import router as admin_users_router
from app.api.v1.admin.monitoring import router as admin_monitoring_router
from app.api.v1.admin.router_config import router as admin_router_config_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(
    title="Monkee AI Agent API",
    version="2.0.0",
    description="Criminal Player AI v2.0 — Backend API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
app.include_router(pipelines_router, prefix="/api/v1")

# Admin routes (require 'admin' group)
app.include_router(admin_agents_router, prefix="/api/v1")
app.include_router(admin_kbs_router, prefix="/api/v1")
app.include_router(admin_pipelines_router, prefix="/api/v1")
app.include_router(admin_tools_router, prefix="/api/v1")
app.include_router(admin_users_router, prefix="/api/v1")
app.include_router(admin_monitoring_router, prefix="/api/v1")
app.include_router(admin_router_config_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
