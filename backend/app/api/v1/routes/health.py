from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    timestamp: datetime
    version: str
    integrations: dict[str, str]
    emergency_fallback_number: str


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health() -> HealthResponse:
    """Liveness check endpoint providing system status and integration modes."""
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
        integrations={
            "sms": f"[{settings.SMS_PROVIDER.upper()}]",
            "push": f"[{settings.PUSH_PROVIDER.upper()}]",
            "email": f"[{settings.EMAIL_PROVIDER.upper()}]",
            "maps": f"[{settings.MAPS_PROVIDER.upper()}]",
            "payments": f"[{settings.PAYMENTS_PROVIDER.upper()}]",
            "llm": f"[{settings.LLM_PROVIDER.upper()}]",
        },
        emergency_fallback_number=settings.EMERGENCY_NUMBER_PRIMARY,
    )


@router.get("/ready", tags=["Health"])
async def get_ready() -> dict[str, Any]:
    """Readiness probe endpoint for container orchestrators."""
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "configured",
        "redis": "configured",
    }
