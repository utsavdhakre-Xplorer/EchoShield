"""Regression tests for auth endpoints when persistence or accounts are unavailable."""
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
from app.api.auth import get_call_history, login
from app.models.user import UserLogin


class TestAuthEndpointReliability(unittest.IsolatedAsyncioTestCase):
    async def test_call_history_returns_service_unavailable_without_database(self):
        user = SimpleNamespace(id="user-123")
        with patch("app.core.database.CallLog", None):
            with self.assertRaises(HTTPException) as raised:
                await get_call_history(user)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Database is unavailable")

    async def test_login_rejects_disabled_account(self):
        disabled_user = SimpleNamespace(
            is_active=False,
            hashed_password="hash",
            last_login=None,
        )

        class FakeUser:
            @staticmethod
            async def find_one(query):
                return disabled_user

        credentials = UserLogin(email="user@example.com", password="ValidPass123")
        with patch("app.core.database.User", FakeUser), \
             patch("app.api.auth.verify_password", return_value=True):
            with self.assertRaises(HTTPException) as raised:
                await login(credentials)
        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(raised.exception.detail, "User account is disabled")
        self.assertIsNone(disabled_user.last_login)


if __name__ == "__main__":
    unittest.main()
