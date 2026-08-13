"""ORM models package — import models so metadata is complete for Alembic."""

from app.models.city import City
from app.models.device import UserDevice
from app.models.notification import NotificationPreferences, NotificationTemplate
from app.models.ops_operator import OpsOperator
from app.models.ops_refresh_token import OpsRefreshToken
from app.models.otp_challenge import OtpChallenge
from app.models.payment import Payment, PaymentKind, PaymentStatus
from app.models.pricing import CityInteriorPrice, CityPricing, CitySizePrice
from app.models.refresh_token import RefreshToken
from app.models.society import Society
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleMake, VehicleModel, VehicleSizeTier
from app.models.waitlist import WaitlistEntry, WaitlistStatus
from app.models.wash import Wash, WashStatus

__all__ = [
    "City",
    "CityInteriorPrice",
    "CityPricing",
    "CitySizePrice",
    "NotificationPreferences",
    "NotificationTemplate",
    "OpsOperator",
    "OpsRefreshToken",
    "OtpChallenge",
    "Payment",
    "PaymentKind",
    "PaymentStatus",
    "RefreshToken",
    "Society",
    "Subscription",
    "SubscriptionStatus",
    "User",
    "UserDevice",
    "Vehicle",
    "VehicleMake",
    "VehicleModel",
    "VehicleSizeTier",
    "WaitlistEntry",
    "WaitlistStatus",
    "Wash",
    "WashStatus",
]
