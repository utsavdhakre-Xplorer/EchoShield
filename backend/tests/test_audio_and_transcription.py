"""Tests for audio processing, features, transcription fallback, and database mock."""
import unittest
import os
import sys
import tempfile
import numpy as np
import scipy.io.wavfile as wav
import asyncio

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.transcription import transcribe_audio, _transcribe_sync
from app.ml.audio_features import extract_audio_features
from app.core.mock_db import MockCallLog, clear_mock_db, _call_logs_db


class TestAudioAndTranscription(unittest.TestCase):

    def setUp(self):
        clear_mock_db()

    def test_transcription_empty_and_missing_audio_no_fake_scam(self):
        """Missing or empty audio must never return fake scam transcripts."""
        # Non-existent file
        res_missing = asyncio.run(transcribe_audio("nonexistent_audio_file.wav"))
        self.assertEqual(res_missing, "")

        # Empty 0-byte file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            res_empty = asyncio.run(transcribe_audio(tmp_path))
            self.assertEqual(res_empty, "")
            # Ensure fake scam phrases are NEVER present
            self.assertNotIn("warrant", res_empty.lower())
            self.assertNotIn("arrest", res_empty.lower())
            self.assertNotIn("account will be blocked", res_empty.lower())
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_audio_features_silence_not_flagged_as_synthetic(self):
        """Pure silence or near-zero amplitude must not be flagged as a synthetic voice anomaly."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            silence = np.zeros(16000, dtype=np.int16)
            wav.write(tmp.name, 16000, silence)
            tmp_path = tmp.name

        try:
            feats = extract_audio_features(tmp_path)
            self.assertEqual(feats["synthetic_voice_probability"], 0.0)
            self.assertFalse(feats.get("is_speech_present", True))
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_mock_call_log_save_upsert_and_transcript_accumulation(self):
        """MockCallLog.save() must correctly insert new records and update transcripts across chunks."""
        async def run_db_test():
            log = MockCallLog(user_id="user_123")
            log.transcript = "Chunk 1: Hello."
            log.audio_chunks_received = 1
            await log.save()

            # Verify saved
            self.assertIn(log.id, _call_logs_db)
            saved = await MockCallLog.get(log.id)
            self.assertIsNotNone(saved)
            self.assertEqual(saved.transcript, "Chunk 1: Hello.")
            self.assertEqual(saved.audio_chunks_received, 1)

            # Update with chunk 2
            log.transcript = "Chunk 1: Hello. Chunk 2: Goodbye."
            log.audio_chunks_received = 2
            await log.save()

            saved_again = await MockCallLog.get(log.id)
            self.assertEqual(saved_again.transcript, "Chunk 1: Hello. Chunk 2: Goodbye.")
            self.assertEqual(saved_again.audio_chunks_received, 2)

        asyncio.run(run_db_test())


if __name__ == "__main__":
    unittest.main()
