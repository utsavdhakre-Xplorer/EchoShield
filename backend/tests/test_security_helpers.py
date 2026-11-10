"""Regression tests for EchoShield password and JWT security helpers."""
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from datetime import timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    get_current_user,
)


class TestSecurityHelpers(unittest.TestCase):
    def test_password_hash_is_not_plaintext_and_verifies(self):
        password = "SecurePass123!"
        hashed = hash_password(password)
        self.assertNotEqual(hashed, password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPass123!", hashed))

    def test_password_hash_uses_unique_salts(self):
        password = "SecurePass123!"
        self.assertNotEqual(hash_password(password), hash_password(password))

    def test_short_password_rejected(self):
        with self.assertRaises(ValueError):
            hash_password("short")

    def test_malformed_hash_returns_false(self):
        self.assertFalse(verify_password("some-password", "not-a-valid-bcrypt-hash"))

    def test_access_token_round_trip(self):
        token = create_access_token({"sub": "user-123"})
        payload = decode_token(token)
        self.assertEqual(payload["sub"], "user-123")
        self.assertIn("exp", payload)

    def test_expired_token_rejected(self):
        token = create_access_token({"sub": "user-123"}, expires_delta=timedelta(seconds=-1))
        with self.assertRaises(HTTPException) as raised:
            decode_token(token)
        self.assertEqual(raised.exception.status_code, 401)

    def test_invalid_token_rejected(self):
        with self.assertRaises(HTTPException) as raised:
            decode_token("not.a.valid.token")
        self.assertEqual(raised.exception.status_code, 401)


class TestCurrentUserDependency(unittest.IsolatedAsyncioTestCase):
    async def test_database_unavailable_returns_503(self):
        token = create_access_token({"sub": "user-123"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with patch("app.core.database.User", None):
            with self.assertRaises(HTTPException) as raised:
                await get_current_user(credentials)
        self.assertEqual(raised.exception.status_code, 503)

    async def test_missing_user_returns_404(self):
        class FakeUser:
            @staticmethod
            async def get(user_id):
                return None

        token = create_access_token({"sub": "missing-user"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with patch("app.core.database.User", FakeUser):
            with self.assertRaises(HTTPException) as raised:
                await get_current_user(credentials)
        self.assertEqual(raised.exception.status_code, 404)

    async def test_disabled_user_returns_403(self):
        class FakeUser:
            @staticmethod
            async def get(user_id):
                return SimpleNamespace(is_active=False)

        token = create_access_token({"sub": "disabled-user"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with patch("app.core.database.User", FakeUser):
            with self.assertRaises(HTTPException) as raised:
                await get_current_user(credentials)
        self.assertEqual(raised.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
