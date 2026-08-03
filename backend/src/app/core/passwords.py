"""Password hashing for ops operators (stdlib scrypt — no extra dependency)."""

from __future__ import annotations

import hashlib
import hmac
import secrets

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32
_PREFIX = "scrypt"


def hash_password(password: str) -> str:
    """Return a storable password hash: ``scrypt$<salt_hex>$<dk_hex>``."""
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    return f"{_PREFIX}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        prefix, salt_hex, dk_hex = stored.split("$", 2)
    except ValueError:
        return False
    if prefix != _PREFIX:
        return False
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(dk_hex)
    except ValueError:
        return False
    actual = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    return hmac.compare_digest(actual, expected)
