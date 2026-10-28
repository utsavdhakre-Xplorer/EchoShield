"""Tests for threat classifier service."""
import unittest
import os
import sys

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.threat_classifier import classify_threat
from app.models.call_log import ThreatLevel


class TestThreatClassifier(unittest.TestCase):

    def test_unverified_deepfake_does_not_dilute_scam_score(self):
        """When deepfake detection is unverified, scam score must not be penalized."""
        result = classify_threat(
            deepfake_confidence=0.0,
            is_deepfake=False,
            urgency_score=0.95,
            urgency_detected=True,
            deepfake_verified=False,
            tactics_detected=["Legal Intimidation", "Urgent Financial Coercion"],
        )
        self.assertEqual(result["overall_score"], 0.95)
        self.assertEqual(result["threat_level"], ThreatLevel.CRITICAL)
        self.assertTrue(result["alert_required"])
        self.assertIn("Voice authenticity: unverified", result["threat_factors"][1])

    def test_verified_deepfake_escalation_with_scam(self):
        """Verified deepfake combined with scam tactics escalates to CRITICAL."""
        result = classify_threat(
            deepfake_confidence=0.90,
            is_deepfake=True,
            urgency_score=0.75,
            urgency_detected=True,
            deepfake_verified=True,
            tactics_detected=["Account Threat / Freeze"],
        )
        self.assertGreaterEqual(result["overall_score"], 0.90)
        self.assertEqual(result["threat_level"], ThreatLevel.CRITICAL)
        self.assertTrue(result["alert_required"])

    def test_verified_deepfake_in_benign_context_capped(self):
        """Synthetic voice without scam tactics (IVR, notification) is capped at MEDIUM, not CRITICAL."""
        result = classify_threat(
            deepfake_confidence=0.88,
            is_deepfake=True,
            urgency_score=0.0,
            urgency_detected=False,
            deepfake_verified=True,
            tactics_detected=[],
        )
        self.assertLessEqual(result["overall_score"], 0.45)
        self.assertIn(result["threat_level"], [ThreatLevel.LOW, ThreatLevel.MEDIUM])
        self.assertFalse(result["alert_required"])

    def test_safe_conversation(self):
        """Standard conversational call without scam or deepfake must produce LOW threat."""
        result = classify_threat(
            deepfake_confidence=0.05,
            is_deepfake=False,
            urgency_score=0.0,
            urgency_detected=False,
            deepfake_verified=True,
            tactics_detected=[],
        )
        self.assertEqual(result["overall_score"], 0.0)
        self.assertEqual(result["threat_level"], ThreatLevel.LOW)
        self.assertFalse(result["alert_required"])
        self.assertIn("No predatory scam tactics", result["threat_factors"][0])

    def test_threat_factors_contain_explanations(self):
        """Response must include informative threat_factors explanations."""
        result = classify_threat(
            deepfake_confidence=0.0,
            is_deepfake=False,
            urgency_score=0.65,
            urgency_detected=True,
            deepfake_verified=False,
            tactics_detected=["Fake Malware Warning", "Remote Access Takeover"],
        )
        self.assertIn("threat_factors", result)
        self.assertGreater(len(result["threat_factors"]), 1)
        self.assertTrue(any("Remote Access Takeover" in f for f in result["threat_factors"]))


if __name__ == "__main__":
    unittest.main()
