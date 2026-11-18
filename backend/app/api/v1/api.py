from fastapi import APIRouter

from app.api.v1.routes import auth, consent, health, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(consent.router)
