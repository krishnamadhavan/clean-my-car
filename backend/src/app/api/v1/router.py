"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    app_meta,
    auth,
    content,
    dashboard,
    health,
    location,
    notification,
    payment,
    pricing,
    profile,
    schedule,
    subscription,
    support,
    vehicle,
    waitlist,
    wash,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(location.router)
api_router.include_router(waitlist.router)
api_router.include_router(vehicle.router)
api_router.include_router(pricing.router)
api_router.include_router(subscription.router)
api_router.include_router(payment.router)
api_router.include_router(schedule.router)
api_router.include_router(wash.router)
api_router.include_router(dashboard.router)
api_router.include_router(notification.router)
api_router.include_router(content.router)
api_router.include_router(support.router)
api_router.include_router(app_meta.router)
api_router.include_router(webhooks.router)
