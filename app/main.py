from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging, get_logger
from app.middleware.audit import AuditMiddleware
from app.mcp import register_all_tools

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    register_all_tools()
    logger.info("startup", env=settings.app_env)
    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        swagger_ui_parameters={"persistAuthorization": True},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AuditMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    if settings.enable_metrics:
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()
