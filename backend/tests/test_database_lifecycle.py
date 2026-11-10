"""Regression tests for MongoDB client lifecycle reliability."""
import os
import sys
import unittest
from unittest.mock import patch, AsyncMock, Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core import database


class TestDatabaseLifecycle(unittest.IsolatedAsyncioTestCase):
    async def test_failed_beanie_initialization_closes_created_client(self):
        fake_client = type("FakeClient", (), {
            "get_default_database": lambda self: object(),
            "close": Mock(),
        })()

        with patch.object(database, "AsyncIOMotorClient", return_value=fake_client), \
             patch.object(database, "init_beanie", new=AsyncMock(side_effect=RuntimeError("connection failure"))), \
             patch.dict(os.environ, {"ENABLE_MOCK_DB": "false"}):
            await database.connect_db()

        fake_client.close.assert_called_once()
        self.assertIsNone(database.client)
        self.assertFalse(database.db_connected)
        self.assertIsNone(database.User)
        self.assertIsNone(database.CallLog)

    async def test_disconnect_closes_client_and_clears_global_reference(self):
        fake_client = type("FakeClient", (), {"close": Mock()})()
        database.client = fake_client
        database.db_connected = True

        await database.disconnect_db()

        fake_client.close.assert_called_once()
        self.assertIsNone(database.client)
        self.assertFalse(database.db_connected)


if __name__ == "__main__":
    unittest.main()
