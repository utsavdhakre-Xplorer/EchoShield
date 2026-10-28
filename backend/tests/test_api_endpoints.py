"""Tests for REST API endpoints and error validation."""
import unittest
import os
import sys
import io

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, get_current_user
from app.core.mock_db import MockUser, clear_mock_db
import app.core.database as database


class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize mock database models
        database.User = MockUser
        database.CallLog = database.MockCallLog
        cls.client = TestClient(app)

    def setUp(self):
        clear_mock_db()

    def _get_auth_headers(self):
        user = MockUser(user_id="test_user_1", email="test@example.com", username="testuser")
        import asyncio
        asyncio.run(user.insert())
        token = create_access_token({"sub": "test_user_1"})
        return {"Authorization": f"Bearer {token}"}

    def test_health_check(self):
        """GET /health must return ok status."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "EchoShield")

    def test_analyze_transcript_benign(self):
        """POST /analyze with benign text must return LOW threat level."""
        headers = self._get_auth_headers()
        payload = {"transcript": "Hello, I am calling to confirm our lunch reservation tomorrow."}
        response = self.client.post("/analyze", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["threat_level"], "LOW")
        self.assertEqual(data["overall_threat_score"], 0.0)
        self.assertFalse(data["alert_required"])
        self.assertIn("threat_factors", data)

    def test_analyze_transcript_scam(self):
        """POST /analyze with scam text must return CRITICAL threat level and alert required."""
        headers = self._get_auth_headers()
        payload = {
            "transcript": "This is the IRS. A warrant has been issued for your arrest. Go to a bitcoin atm and transfer funds now."
        }
        response = self.client.post("/analyze", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["threat_level"], ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(data["overall_threat_score"], 0.80)
        self.assertTrue(data["alert_required"])
        self.assertGreater(len(data["urgency_phrases_found"]), 0)

    def test_stream_audio_empty_rejected(self):
        """POST /stream-audio with 0-byte or empty file must return 400 Bad Request."""
        headers = self._get_auth_headers()
        files = {"audio": ("empty.wav", b"", "audio/wav")}
        response = self.client.post("/stream-audio", files=files, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Empty or invalid audio data", response.json()["detail"])

    def test_analyze_audio_empty_rejected(self):
        """POST /analyze-audio with 0-byte or empty file must return 400 Bad Request."""
        headers = self._get_auth_headers()
        files = {"audio": ("empty.wav", b"", "audio/wav")}
        response = self.client.post("/analyze-audio", files=files, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Empty or invalid audio data", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
