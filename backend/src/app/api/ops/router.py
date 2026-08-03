"""Ops API v1 router — mounted at ``/api/v1/ops``.

Documented separately at ``/ops/docs`` (see ``app.main``).
Inventory: ``docs/OPS_API_INVENTORY.md``.
"""

from fastapi import APIRouter

from app.api.ops.endpoints import auth, health, location, pricing, users, vehicle, waitlist

ops_router = APIRouter()
ops_router.include_router(health.router)
ops_router.include_router(auth.router)
ops_router.include_router(users.router)
ops_router.include_router(location.router)
ops_router.include_router(waitlist.router)
ops_router.include_router(vehicle.router)
ops_router.include_router(pricing.router)
