"""
core/security.py

Cryptographic utilities for password hashing and JWT token generation/validation.

This module is the single authoritative source for security operations.
No other module should import from bcrypt or python-jose directly.

Password hashing:
    Uses the bcrypt library directly (avoiding passlib's version-detection bug
    with bcrypt >= 4.x that removed the __about__ attribute).

JWT:
    Uses python-jose with HS256 signing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from core.config import settings


# ─────────────────────────────────────────────────────────────────────────────
# Password hashing (using bcrypt directly)
# ─────────────────────────────────────────────────────────────────────────────

_BCRYPT_ROUNDS = 12
_ALGORITHM = "HS256"
_DEFAULT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def get_password_hash(password: str) -> str:
    """Return the bcrypt hash of the given plaintext password."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plaintext password matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# JWT token utilities
# ─────────────────────────────────────────────────────────────────────────────


def create_access_token(
    data: dict[str, Any],
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Encode a signed JWT access token.

    Args:
        data: Claims to embed (e.g. ``{"sub": "42"}``).
        expires_delta: Override the default TTL.

    Returns:
        A compact JWT string.
    """
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=_DEFAULT_EXPIRE_MINUTES)
    )
    payload = {**data, "exp": expire, "iat": datetime.now(tz=timezone.utc)}
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a signed JWT token.

    Raises:
        JWTError: If the token is malformed, expired, or has an invalid signature.

    Returns:
        The decoded claims dictionary.
    """
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
    except JWTError:
        raise
