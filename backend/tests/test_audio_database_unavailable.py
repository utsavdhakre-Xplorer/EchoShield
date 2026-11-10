"""Regression tests for audio endpoints when database persistence is unavailable."""
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
from app.api.audio import (
    stream_audio_chunk,
    analyze_uploaded_audio,
    _read_bounded_audio_upload,
)


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


class TestBoundedAudioUpload(unittest.IsolatedAsyncioTestCase):
    async def test_reads_upload_in_bounded_chunks(self):
        class FakeUpload:
            def __init__(self):
                self.chunks = [b"abcd", b"ef", b""]

            async def read(self, size):
                self.asserted_size = size
                return self.chunks.pop(0)

        upload = FakeUpload()
        with patch("app.api.audio.UPLOAD_READ_CHUNK_BYTES", 4):
            result = await _read_bounded_audio_upload(upload)
        self.assertEqual(result, b"abcdef")
        self.assertEqual(upload.asserted_size, 4)

    async def test_rejects_upload_above_configured_limit(self):
        class FakeUpload:
            def __init__(self):
                self.chunks = [b"123456", b"78901"]

            async def read(self, size):
                return self.chunks.pop(0) if self.chunks else b""

        with patch("app.api.audio.MAX_AUDIO_UPLOAD_BYTES", 10), \
             patch("app.api.audio.UPLOAD_READ_CHUNK_BYTES", 6):
            with self.assertRaises(HTTPException) as raised:
                await _read_bounded_audio_upload(FakeUpload())
        self.assertEqual(raised.exception.status_code, 413)


if __name__ == "__main__":
    unittest.main()
