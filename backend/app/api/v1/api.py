from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    consent,
    contacts,
    health,
    incidents,
    places,
    users,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(consent.router)
api_router.include_router(contacts.router)
api_router.include_router(incidents.router)
api_router.include_router(webhooks.router)
api_router.include_router(places.router)
