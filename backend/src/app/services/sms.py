"""SMS delivery abstraction for OTP.

v1 uses a logging provider. Swap for MSG91 / Twilio / etc. without changing callers.
"""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class SmsSender(Protocol):
    async def send_otp(self, phone: str, otp: str) -> None: ...


class LoggingSmsSender:
    """Development / default sender — logs OTP (never use logs as production channel)."""

    async def send_otp(self, phone: str, otp: str) -> None:
        logger.info("OTP for %s: %s", phone, otp)


def get_sms_sender() -> SmsSender:
    return LoggingSmsSender()
