"""This module provides tests for the Chirpier SDK client functionality."""

import unittest
from chirpier.client import Client
from chirpier.event import Event
from chirpier.errors import ChirpierError


class TestClient(unittest.TestCase):
    """Tests for the Client class."""

    def setUp(self):
        self.client = Client("valid.jwt.token")

    def tearDown(self):
        self.client.stop()

    def test_monitor_valid_event(self):
        """Tests that a valid event is correctly sent to the Chirpier API."""
        event = Event("123e4567-e89b-12d3-a456-426614174000",
                      "test_stream", 42.0)
        try:
            self.client.monitor(event)
        except ChirpierError:
            self.fail("monitor() raised ChirpierError unexpectedly!")

    def test_monitor_invalid_event(self):
        """Tests that an invalid event is correctly rejected by the Chirpier API."""
        event = Event("", "test_stream", 42.0)
        with self.assertRaises(ChirpierError):
            self.client.monitor(event)


if __name__ == '__main__':
    unittest.main()
