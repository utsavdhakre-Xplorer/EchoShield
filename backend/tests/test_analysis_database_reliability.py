"""Regression tests for analysis endpoints when call-log storage fails."""
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
from app.api.analysis import get_call_logs, get_stats


class FailingCallLog:
    @staticmethod
    def find(query):
        raise RuntimeError("private database detail")


class TestAnalysisDatabaseReliability(unittest.IsolatedAsyncioTestCase):
    async def test_call_logs_returns_503_on_database_query_error(self):
        user = SimpleNamespace(id="user-123")
        with patch("app.core.database.CallLog", FailingCallLog):
            with self.assertRaises(HTTPException) as raised:
                await get_call_logs(limit=20, current_user=user)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Call logs are temporarily unavailable")

    async def test_stats_returns_503_on_database_query_error(self):
        user = SimpleNamespace(id="user-123")
        with patch("app.core.database.CallLog", FailingCallLog):
            with self.assertRaises(HTTPException) as raised:
                await get_stats(current_user=user)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Statistics are temporarily unavailable")


if __name__ == "__main__":
    unittest.main()
