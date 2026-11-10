"""Tests for scam detector and NLP classifier."""
import unittest
import os
import sys
import asyncio
from unittest.mock import patch, AsyncMock

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ml.nlp_classifier import classify_scam, _analyze_contextual_scam_signals
from app.services.scam_detector import detect_scam_tactics


class TestScamAndNLPDetector(unittest.TestCase):

    def test_benign_negative_sentiment_not_flagged(self):
        """Negative sentiment (sadness/frustration) alone must not trigger scam detection."""
        benign_transcripts = [
            "I am feeling so sad today, my dog died and it is raining outside.",
            "I had a terrible headache and could not sleep all night.",
            "I am very unhappy with the food delivery, the pizza was cold and damaged.",
            "Sorry I couldn't make it to our meeting, I have a horrible flu.",
        ]
        for text in benign_transcripts:
            result = asyncio.run(detect_scam_tactics(text))
            self.assertFalse(
                result["urgency_detected"],
                f"False positive on benign negative text: {text}. Result: {result}",
            )
            self.assertEqual(result["urgency_score"], 0.0)
            self.assertEqual(len(result["tactics_detected"]), 0)

    def test_coercive_government_and_legal_scam(self):
        """Government impersonation with arrest threats and bitcoin demand must trigger critical risk."""
        scam_text = (
            "This is officer Davis from the IRS. A warrant has been issued for your arrest. "
            "Your social security number has been suspended. Go to a bitcoin atm and transfer funds now. "
            "Don't hang up or police will be dispatched."
        )
        result = asyncio.run(detect_scam_tactics(scam_text))
        self.assertTrue(result["urgency_detected"])
        self.assertGreaterEqual(result["urgency_score"], 0.85)
        self.assertGreater(len(result["phrases_found"]), 0)
        self.assertIn("Legal Intimidation", result["tactics_detected"])
        self.assertIn("Cryptocurrency Extraction", result["tactics_detected"])

    def test_polite_celebratory_prize_scam(self):
        """Positive sentiment prize scam with payment demand must not be masked as safe."""
        prize_text = (
            "Congratulations! You have been selected as the grand lottery winner of one million dollars! "
            "Please provide your credit card or send a gift card payment to pay the small release fee."
        )
        result = asyncio.run(detect_scam_tactics(prize_text))
        self.assertTrue(result["urgency_detected"])
        self.assertGreaterEqual(result["urgency_score"], 0.70)
        self.assertIn("Prize / Lottery Lure", result["tactics_detected"])

    def test_tech_support_remote_access_scam(self):
        """Tech support impersonation with AnyDesk takeover must trigger high risk."""
        tech_text = (
            "This is Microsoft technical support. A critical virus has been detected on your computer. "
            "Please download anydesk immediately and give me remote access to fix it."
        )
        result = asyncio.run(detect_scam_tactics(tech_text))
        self.assertTrue(result["urgency_detected"])
        self.assertGreaterEqual(result["urgency_score"], 0.85)
        self.assertIn("Remote Access Takeover", result["tactics_detected"])

    def test_credential_harvesting_scam(self):
        """Bank fraud impersonation requesting OTP and CVV must trigger high risk."""
        cred_text = (
            "This is the security division of your bank. Your account will be blocked. "
            "Please verify your identity and give me your one-time password and CVV immediately."
        )
        result = asyncio.run(detect_scam_tactics(cred_text))
        self.assertTrue(result["urgency_detected"])
        self.assertGreaterEqual(result["urgency_score"], 0.80)

    def test_empty_and_short_input_handling(self):
        """Empty or very short input must return 0 scores safely."""
        for empty_text in ["", "   ", "hi", "yes"]:
            result = asyncio.run(detect_scam_tactics(empty_text))
            self.assertFalse(result["urgency_detected"])
            self.assertEqual(result["urgency_score"], 0.0)

            nlp_res = asyncio.run(classify_scam(empty_text))
            self.assertEqual(nlp_res["scam_probability"], 0.0)
            self.assertEqual(nlp_res["label"], "SAFE")


    def test_classifier_only_low_confidence_noise_is_suppressed(self):
        """Low ML-only scores without tactic matches should not become urgency."""
        with patch("app.services.scam_detector._ML_AVAILABLE", True), \
             patch("app.services.scam_detector._ml_classify", new=AsyncMock(return_value={"scam_probability": 0.2297})):
            result = asyncio.run(detect_scam_tactics(
                "Hello, I am calling to confirm our lunch reservation tomorrow."
            ))
        self.assertFalse(result["urgency_detected"])
        self.assertEqual(result["urgency_score"], 0.0)

    def test_explicit_remote_access_tactics_remain_high_risk(self):
        """Explicit tech-support and remote-access matches must dominate ML blending."""
        text = (
            "This is Microsoft technical support. A critical virus has been detected "
            "on your computer. Please download anydesk immediately and give me remote access."
        )
        with patch("app.services.scam_detector._ML_AVAILABLE", True), \
             patch("app.services.scam_detector._ml_classify", new=AsyncMock(return_value={"scam_probability": 0.668})):
            result = asyncio.run(detect_scam_tactics(text))
        self.assertTrue(result["urgency_detected"])
        self.assertGreaterEqual(result["urgency_score"], 0.85)
        self.assertIn("Remote Access Takeover", result["tactics_detected"])


if __name__ == "__main__":
    unittest.main()
