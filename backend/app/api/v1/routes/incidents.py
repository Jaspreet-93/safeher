import uuid

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.incident import (
    ContactAckResponse,
    IncidentDetailResponse,
    SOSCancelRequest,
    SOSResolveRequest,
    SOSTriggerRequest,
)
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["Emergency Incidents & SOS"])


@router.post("/sos", response_model=IncidentDetailResponse, status_code=status.HTTP_201_CREATED)
async def trigger_sos(
    req: SOSTriggerRequest,
    x_idempotency_key: str | None = Header(None, alias="X-Idempotency-Key"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> IncidentDetailResponse:
    """
    Triggers an emergency SOS incident.
    Guaranteed idempotent via X-Idempotency-Key header.
    Starts grace period countdown before dispatching external alerts.
    """
    idempotency_key = x_idempotency_key or f"auto-{current_user.id}-{uuid.uuid4()}"
    incident = await IncidentService.trigger_sos(
        db, current_user, req, idempotency_key=idempotency_key
    )
    return await IncidentService.get_incident_status(db, current_user, incident.id)


@router.post("/{incident_id}/activate", response_model=IncidentDetailResponse)
async def activate_sos(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> IncidentDetailResponse:
    """Activates incident after grace countdown ends, enqueuing and dispatching notifications."""
    incident = await IncidentService.activate_incident(db, current_user, incident_id)
    return await IncidentService.get_incident_status(db, current_user, incident.id)


@router.post("/{incident_id}/cancel", response_model=IncidentDetailResponse)
async def cancel_sos(
    incident_id: uuid.UUID,
    req: SOSCancelRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> IncidentDetailResponse:
    """Cancels incident within grace window, preventing any SMS or notification dispatch."""
    incident = await IncidentService.cancel_incident(db, current_user, incident_id, req)
    return await IncidentService.get_incident_status(db, current_user, incident.id)


@router.post("/{incident_id}/resolve", response_model=IncidentDetailResponse)
async def resolve_sos(
    incident_id: uuid.UUID,
    req: SOSResolveRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> IncidentDetailResponse:
    """Resolves an active emergency incident once safety is established."""
    incident = await IncidentService.resolve_incident(db, current_user, incident_id, req)
    return await IncidentService.get_incident_status(db, current_user, incident.id)


@router.get("/{incident_id}/status", response_model=IncidentDetailResponse)
async def get_sos_status(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> IncidentDetailResponse:
    """Returns real-time per-contact delivery receipts and incident status."""
    return await IncidentService.get_incident_status(db, current_user, incident_id)


@router.post("/ack/{token}", response_model=ContactAckResponse)
async def acknowledge_sos_alert(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> ContactAckResponse:
    """Public endpoint: Allows an emergency contact to acknowledge safety alert from SMS link."""
    return await IncidentService.acknowledge_alert(db, ack_token=token)
