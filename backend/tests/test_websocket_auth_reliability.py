"""Regression coverage for WebSocket authentication availability behavior."""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import create_access_token
from app.api.ws_audio import ws_analyze


class FakeWebSocket:
    def __init__(self):
        self.close_code = None
        self.close_reason = None

    async def close(self, code, reason):
        self.close_code = code
        self.close_reason = reason


class TestWebSocketAuthReliability(unittest.IsolatedAsyncioTestCase):
    async def test_database_unavailable_closes_with_retryable_code(self):
        websocket = FakeWebSocket()
        token = create_access_token({"sub": "user-123"})
        with patch("app.core.database.User", None):
            await ws_analyze(websocket, token=token)
        self.assertEqual(websocket.close_code, 1013)
        self.assertEqual(websocket.close_reason, "Database unavailable")

    async def test_user_lookup_database_error_closes_with_retryable_code(self):
        class FailingUser:
            @staticmethod
            async def get(user_id):
                raise RuntimeError("private db message")

        websocket = FakeWebSocket()
        token = create_access_token({"sub": "user-123"})
        with patch("app.core.database.User", FailingUser):
            await ws_analyze(websocket, token=token)
        self.assertEqual(websocket.close_code, 1013)
        self.assertEqual(websocket.close_reason, "Database temporarily unavailable")

    async def test_disabled_account_closes_with_auth_code(self):
        class DisabledUser:
            @staticmethod
            async def get(user_id):
                return type("UserStub", (), {"is_active": False})()

        websocket = FakeWebSocket()
        token = create_access_token({"sub": "user-123"})
        with patch("app.core.database.User", DisabledUser):
            await ws_analyze(websocket, token=token)
        self.assertEqual(websocket.close_code, 4001)
        self.assertEqual(websocket.close_reason, "User account is invalid or disabled")


if __name__ == "__main__":
    unittest.main()
