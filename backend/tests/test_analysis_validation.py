"""Regression tests for transcript analysis request validation."""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException
from app.api.analysis import validate_transcript_request


class TestTranscriptRequestValidation(unittest.TestCase):
    def test_valid_request_trims_transcript_and_preserves_optional_fields(self):
        result = validate_transcript_request({
            "transcript": "  Hello there.  ",
            "call_id": "call-123",
            "caller_number": "+911234567890",
        })
        self.assertEqual(result, ("Hello there.", "call-123", "+911234567890"))

    def test_transcript_must_be_string(self):
        with self.assertRaises(HTTPException) as raised:
            validate_transcript_request({"transcript": 12345})
        self.assertEqual(raised.exception.status_code, 400)

    def test_transcript_too_short_is_rejected(self):
        with self.assertRaises(HTTPException) as raised:
            validate_transcript_request({"transcript": "  hi "})
        self.assertEqual(raised.exception.status_code, 400)

    def test_transcript_over_limit_is_rejected(self):
        with self.assertRaises(HTTPException) as raised:
            validate_transcript_request({"transcript": "x" * 10001})
        self.assertEqual(raised.exception.status_code, 413)

    def test_caller_number_type_and_length_are_validated(self):
        for value in (123, "x" * 33):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(HTTPException) as raised:
                    validate_transcript_request({"transcript": "Hello there", "caller_number": value})
                self.assertEqual(raised.exception.status_code, 400)

    def test_call_id_type_and_length_are_validated(self):
        for value in (123, "x" * 101):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(HTTPException) as raised:
                    validate_transcript_request({"transcript": "Hello there", "call_id": value})
                self.assertEqual(raised.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
