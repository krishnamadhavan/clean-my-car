"""ORM models package — import models so metadata is complete for Alembic."""

from app.models.city import City
from app.models.ops_operator import OpsOperator
from app.models.ops_refresh_token import OpsRefreshToken
from app.models.otp_challenge import OtpChallenge
from app.models.pricing import CityInteriorPrice, CityPricing, CitySizePrice
from app.models.refresh_token import RefreshToken
from app.models.society import Society
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleMake, VehicleModel, VehicleSizeTier
from app.models.waitlist import WaitlistEntry, WaitlistStatus

__all__ = [
    "City",
    "CityInteriorPrice",
    "CityPricing",
    "CitySizePrice",
    "OpsOperator",
    "OpsRefreshToken",
    "OtpChallenge",
    "RefreshToken",
    "Society",
    "User",
    "Vehicle",
    "VehicleMake",
    "VehicleModel",
    "VehicleSizeTier",
    "WaitlistEntry",
    "WaitlistStatus",
]
