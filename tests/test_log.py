"""Tests for the Log model."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest
from uuid import UUID, uuid4

from chirpier.log import Log


class TestLog(unittest.TestCase):
    def test_valid_log(self):
        entry = Log(event="request_finished", value=1, agent="api.worker")
        payload = entry.to_dict()
        self.assertEqual(payload["event"], "request_finished")
        self.assertEqual(payload["value"], 1)
        self.assertEqual(payload["agent"], "api.worker")
        parsed = UUID(payload["log_id"])
        self.assertIsInstance(parsed, UUID)
        self.assertEqual(parsed.version, 7)

    def test_preserves_provided_log_id(self):
        log_id = str(uuid4())
        entry = Log(event="request_finished", value=1, log_id=log_id)
        payload = entry.to_dict()
        self.assertEqual(payload["log_id"], log_id)

    def test_agent_whitespace_omitted(self):
        entry = Log(event="request_finished", value=1, agent="   ")
        payload = entry.to_dict()
        self.assertNotIn("agent", payload)

    def test_meta_json_encodable(self):
        entry = Log(event="request_finished", value=1, meta={"path": "/v1.0/logs"})
        payload = entry.to_dict()
        self.assertEqual(payload["meta"]["path"], "/v1.0/logs")

    def test_occurred_at_serialization(self):
        occurred_at = datetime.now(timezone.utc) - timedelta(hours=2)
        entry = Log(event="request_finished", value=1, occurred_at=occurred_at)
        payload = entry.to_dict()
        self.assertTrue(payload["occurred_at"].endswith("Z"))

    def test_invalid_event(self):
        with self.assertRaises(ValueError):
            Log(event="", value=1)

    def test_invalid_meta(self):
        with self.assertRaises(ValueError):
            Log(event="x", value=1, meta=object())

    def test_invalid_log_id(self):
        with self.assertRaises(ValueError):
            Log(event="x", value=1, log_id="not-a-uuid")

    def test_invalid_occurred_at_out_of_range(self):
        with self.assertRaises(ValueError):
            Log(
                event="x",
                value=1,
                occurred_at=datetime.now(timezone.utc) - timedelta(days=31),
            )

        with self.assertRaises(ValueError):
            Log(
                event="x",
                value=1,
                occurred_at=datetime.now(timezone.utc) + timedelta(days=2),
            )


if __name__ == "__main__":
    unittest.main()
