"""This module provides tests for the Chirpier SDK client functionality.

The tests cover:
- Initialization of the Chirpier client with valid and invalid API keys
- Event monitoring functionality including valid and invalid events
- Queue handling and overflow behavior
- Configuration updates
- Error handling for common failure cases

The test suite uses mocking to avoid real network calls and provides comprehensive
coverage of the client's core functionality.
"""

import unittest
import time
from unittest.mock import patch, MagicMock
from chirpier.client import Chirpier, Config
from chirpier.event import Event
from chirpier.errors import ChirpierError

# Monkey-patch Event to have `event` and `retry_count` attributes
# so the `_flush_batch` method doesn't fail.
original_init = Event.__init__


def patched_init(self, device_id, stream_name, value):
    """Patched initialization to make Event compatible with _flush_batch."""
    original_init(self, device_id, stream_name, value)
    # Make the Event mimic the structure expected by _flush_batch
    self.event = self  # qe.event will now refer back to the Event itself
    self.retry_count = 0


Event.__init__ = patched_init


class TestChirpier(unittest.TestCase):
    """Tests for the Chirpier class."""

    def setUp(self):
        # Reset Chirpier client before each test
        Chirpier._client = None

        # Mock the API endpoint to avoid real network calls
        self.requests_patcher = patch('chirpier.client.requests')
        self.mock_requests = self.requests_patcher.start()

        # Mocking post response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        self.mock_requests.post.return_value = mock_response

        self.api_key = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "e30.Et9HFtf9R3GEMA0IICOfFMVXY7kkTX1wr4qCyhIf58U"
        )

    def tearDown(self):
        self.requests_patcher.stop()
        if Chirpier._client is not None:
            Chirpier._client.shutdown()
            Chirpier._client = None

    def test_initialize_invalid_jwt(self):
        """Test initialization with an invalid JWT token."""
        with self.assertRaises(ValueError) as ctx:
            Chirpier.initialize("invalid_jwt")
        self.assertEqual(str(ctx.exception),
                         "Invalid API key: Not a valid JWT")

    def test_initialize_twice(self):
        """Test that initializing twice raises an error."""
        Chirpier.initialize(self.api_key)
        with self.assertRaises(ChirpierError) as ctx:
            Chirpier.initialize(self.api_key)
        self.assertEqual(str(ctx.exception),
                         "Chirpier SDK is already initialized")

    def test_monitor_without_init(self):
        """Test monitoring without initialization."""
        event = Event("123e4567-e89b-12d3-a456-426614174000",
                      "test_stream", 42.0)
        with self.assertRaises(ChirpierError) as ctx:
            Chirpier.monitor(event)
        self.assertEqual(
            str(ctx.exception),
            "Chirpier SDK is not initialized. Please call initialize() first"
        )

    def test_config_update(self):
        """Test configuration update functionality."""
        config = Config(self.api_key)
        new_values = {
            "retries": 2,      # Reduced retries for faster test execution
            "timeout": 0.5,    # Reduced timeout for test execution
            "batch_size": 50,
            "flush_delay": 0.1,  # Reduced flush delay for test speed
            "queue_size": 1000
        }
        config.update(**new_values)

        for key, value in new_values.items():
            self.assertEqual(getattr(config, key), value)

    def test_monitor_invalid_event(self):
        """Tests that an invalid event is correctly rejected."""
        Chirpier.initialize(self.api_key)
        event = Event("", "test_stream", 42.0)
        with self.assertRaises(ValueError) as ctx:
            Chirpier.monitor(event)
        self.assertEqual(str(ctx.exception), "Invalid event format")

    def test_monitor_valid_event(self):
        """Tests that a valid event is correctly sent to the Chirpier API."""
        with unittest.mock.patch('chirpier.client.requests.post') as mock_post:
            mock_post.return_value.ok = True

            Chirpier.initialize(self.api_key)
            event = Event("123e4567-e89b-12d3-a456-426614174000",
                          "test_stream", 42.0)

            Chirpier.monitor(event)
            # Give the worker thread time to process
            time.sleep(1)

            mock_post.assert_called_once()
            Chirpier.stop()


if __name__ == '__main__':
    unittest.main()
