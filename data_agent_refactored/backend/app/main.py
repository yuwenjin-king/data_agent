import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.metrics import record_request, render_prometheus
from app.schemas.common import ApiResponse

setup_logging(level=settings.LOG_LEVEL)

logger = logging.getLogger("app.main")


def seed_admin_user() -> None:
    """Seed a superuser from ADMIN_USERNAME/ADMIN_PASSWORD when auth is enabled."""
    if not settings.AUTH_ENABLED or not settings.ADMIN_PASSWORD:
        return
    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.models.user import User

    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add(
                User(
                    username=settings.ADMIN_USERNAME,
                    hashed_password=hash_password(settings.ADMIN_PASSWORD),
                    is_active=1,
                    is_superuser=1,
                )
            )
            db.commit()
            logger.info("auth.admin_seeded", extra={"username": settings.ADMIN_USERNAME})
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("app.startup", extra={"app": settings.APP_NAME, "version": settings.APP_VERSION})
    seed_admin_user()
    yield
    logger.info("app.shutdown", extra={"app": settings.APP_NAME, "version": settings.APP_VERSION})


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Data Agent API - 智能数据分析师",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Count every request by method + status for the /metrics endpoint."""
    response = await call_next(request)
    record_request(request.method, response.status_code)
    return response


app.include_router(api_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(code=exc.status_code, message=str(exc.detail)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=ApiResponse(code=422, message="validation error", data=exc.errors()).model_dump(),
    )


@app.get("/")
async def root():
    return {
        "message": "Welcome to Data Agent API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus-format metrics (always open, outside /api/v1 auth)."""
    return PlainTextResponse(render_prometheus(), media_type="text/plain; version=0.0.4")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
