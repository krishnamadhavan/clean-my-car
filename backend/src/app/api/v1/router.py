"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, location, profile

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(location.router)
