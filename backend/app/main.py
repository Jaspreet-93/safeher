import time
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.errors import (
    SafeHerException,
    global_exception_handler,
    safeher_exception_handler,
)
from app.core.logging import logger


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        f"Starting {settings.APP_NAME} backend in [{settings.APP_ENV}] mode (debug={settings.DEBUG})."
    )
    yield
    logger.info(f"Shutting down {settings.APP_NAME} backend gracefully.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Scalable, Privacy-First Women Safety Platform API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)


# ------------------------------------------------------------------------------
# Security Headers & Request Correlation Middleware
# ------------------------------------------------------------------------------
@app.middleware("http")
async def correlation_and_security_middleware(request: Request, call_next: Callable) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response


# ------------------------------------------------------------------------------
# CORS Middleware
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# ------------------------------------------------------------------------------
# Exception Handlers
# ------------------------------------------------------------------------------
app.add_exception_handler(SafeHerException, safeher_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# ------------------------------------------------------------------------------
# Route Registration
# ------------------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    return JSONResponse(
        content={
            "app": settings.APP_NAME,
            "status": "online",
            "docs_url": "/docs",
            "api_version": "v1",
            "health": f"{settings.API_V1_PREFIX}/health",
        }
    )
