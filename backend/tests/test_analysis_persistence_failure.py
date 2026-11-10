"""Regression coverage for analysis persistence failures."""
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
from app.api.analysis import analyze_transcript


class TestAnalysisPersistenceFailure(unittest.IsolatedAsyncioTestCase):
    async def test_analysis_returns_503_when_call_log_cannot_be_saved(self):
        failing_log = SimpleNamespace(insert=AsyncMock(side_effect=RuntimeError("database write failed")))

        class FakeCallLog:
            def __init__(self, **kwargs):
                self.id = "temporary-id"
                self.insert = failing_log.insert

        scam_result = {
            "urgency_score": 0.2,
            "urgency_detected": False,
            "phrases_found": [],
            "tactics_detected": [],
        }
        threat_result = {
            "threat_level": "LOW",
            "overall_score": 0.2,
            "alert_required": False,
            "threat_factors": [],
        }
        user = SimpleNamespace(id="user-123")

        with patch("app.services.scam_detector.detect_scam_tactics", new=AsyncMock(return_value=scam_result)), \
             patch("app.services.threat_classifier.classify_threat", return_value=threat_result), \
             patch("app.services.negotiator.generate_negotiator_strategy", new=AsyncMock(return_value="Stay cautious.")), \
             patch("app.core.database.CallLog", FakeCallLog):
            with self.assertRaises(HTTPException) as raised:
                await analyze_transcript({"transcript": "Please verify your bank account"}, user)

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(
            raised.exception.detail,
            "Unable to save analysis; database temporarily unavailable",
        )
        failing_log.insert.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
