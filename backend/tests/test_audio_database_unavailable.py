"""Regression tests for audio endpoints when database persistence is unavailable."""
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
from app.api.audio import stream_audio_chunk, analyze_uploaded_audio


class TestAudioDatabaseUnavailable(unittest.IsolatedAsyncioTestCase):
    async def test_stream_audio_returns_503_without_database(self):
        with patch("app.core.database.CallLog", None):
            with self.assertRaises(HTTPException) as raised:
                await stream_audio_chunk(
                    audio=object(),
                    current_user=SimpleNamespace(id="user-123"),
                )
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Database is unavailable")

    async def test_analyze_uploaded_audio_returns_503_without_database(self):
        with patch("app.core.database.CallLog", None):
            with self.assertRaises(HTTPException) as raised:
                await analyze_uploaded_audio(
                    audio=object(),
                    current_user=SimpleNamespace(id="user-123"),
                )
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Database is unavailable")


if __name__ == "__main__":
    unittest.main()
