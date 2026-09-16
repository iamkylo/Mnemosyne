"""
tests/test_security.py

Unit tests for core/security.py — password hashing and JWT utilities.
"""

from __future__ import annotations


import pytest
from jose import JWTError

from core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from datetime import timedelta


class TestPasswordHashing:
    def test_hash_returns_string(self) -> None:
        hashed = get_password_hash("mysecret")
        assert isinstance(hashed, str)
        assert hashed != "mysecret"

    def test_verify_correct_password(self) -> None:
        hashed = get_password_hash("mysecret")
        assert verify_password("mysecret", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = get_password_hash("mysecret")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self) -> None:
        """bcrypt generates a new salt each call so hashes must differ."""
        h1 = get_password_hash("password123")
        h2 = get_password_hash("password123")
        assert h1 != h2


class TestJWT:
    def test_create_and_decode(self) -> None:
        token = create_access_token({"sub": "42"})
        payload = decode_access_token(token)
        assert payload["sub"] == "42"

    def test_custom_expiry(self) -> None:
        token = create_access_token({"sub": "42"}, expires_delta=timedelta(hours=1))
        payload = decode_access_token(token)
        assert "exp" in payload

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(JWTError):
            decode_access_token("not.a.valid.token")

    def test_tampered_token_raises(self) -> None:
        token = create_access_token({"sub": "42"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_access_token(tampered)

    def test_extra_claims_preserved(self) -> None:
        token = create_access_token({"sub": "99", "role": "admin"})
        payload = decode_access_token(token)
        assert payload["role"] == "admin"
