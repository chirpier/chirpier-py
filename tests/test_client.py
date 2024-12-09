"""This module provides tests for the Chirpier SDK client functionality."""

import unittest
from unittest.mock import patch
from chirpier.client import Chirpier
from chirpier.event import Event
from chirpier.errors import ChirpierError


class TestChirpier(unittest.TestCase):
    """Tests for the Chirpier class."""

    def setUp(self):
        # Mock the API endpoint to avoid real network calls
        self.patcher = patch('chirpier.client.requests')
        self.mock_requests = self.patcher.start()
        self.mock_requests.post.return_value.status_code = 200
        Chirpier.initialize(
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.Et9HFtf9R3GEMA0IICOfFMVXY7kkTX1wr4qCyhIf58U")

    def tearDown(self):
        self.patcher.stop()
        Chirpier.stop()

    def test_monitor_valid_event(self):
        """Tests that a valid event is correctly sent to the Chirpier API."""
        event = Event("123e4567-e89b-12d3-a456-426614174000",
                      "test_stream", 42.0)
        try:
            Chirpier.monitor(event)
        except ChirpierError:
            self.fail("monitor() raised ChirpierError unexpectedly!")

    def test_monitor_invalid_event(self):
        """Tests that an invalid event is correctly rejected by the Chirpier API."""
        event = Event("", "test_stream", 42.0)
        with self.assertRaises(ChirpierError):
            Chirpier.monitor(event)


if __name__ == '__main__':
    unittest.main()
