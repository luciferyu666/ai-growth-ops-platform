import json
import logging
import time
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.db import get_engine
from app.routers.proposal import router as proposal_router
from app.routers.workspace import router as workspace_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proposal_router)
app.include_router(workspace_router)

logger = logging.getLogger("app.requests")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    request_id = request.headers.get("x-request-id") or str(uuid4())
    route = request.url.path
    logger.info(
        json.dumps(
            {
                "level": "info",
                "message": "request.start",
                "request_id": request_id,
                "method": request.method,
                "route": route,
            }
        )
    )
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception(
            json.dumps(
                {
                    "level": "error",
                    "message": "request.failed",
                    "request_id": request_id,
                    "method": request.method,
                    "route": route,
                    "error": exc.__class__.__name__,
                    "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                }
            )
        )
        raise

    response.headers["x-request-id"] = request_id
    logger.info(
        json.dumps(
            {
                "level": "info",
                "message": "request.done",
                "request_id": request_id,
                "method": request.method,
                "route": route,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            }
        )
    )
    return response


@app.get("/health", tags=["system"])
async def health() -> dict[str, bool | str]:
    return {
        "status": "ok",
        "service": "api",
        "environment": settings.app_env,
        "database_configured": bool(settings.database_url),
        "redis_configured": bool(settings.redis_url),
    }


@app.get("/health/deep", tags=["system"])
def deep_health(response: Response) -> dict[str, Any]:
    checks: dict[str, dict[str, str]] = {}

    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1")).scalar_one()
        checks["database"] = {"status": "ok"}
    except SQLAlchemyError as exc:
        checks["database"] = {"status": "error", "detail": exc.__class__.__name__}

    try:
        redis_client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        redis_client.ping()
        checks["redis"] = {"status": "ok"}
    except RedisError as exc:
        checks["redis"] = {"status": "error", "detail": exc.__class__.__name__}

    is_ok = all(check["status"] == "ok" for check in checks.values())
    if not is_ok:
        response.status_code = 503

    return {
        "status": "ok" if is_ok else "degraded",
        "service": "api",
        "environment": settings.app_env,
        "checks": checks,
    }
