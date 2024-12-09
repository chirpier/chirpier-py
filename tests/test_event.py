"""This module provides tests for the Event class in the Chirpier SDK."""

import unittest
from chirpier.event import Event


class TestEvent(unittest.TestCase):
    """Tests for the Event class."""

    def test_valid_event(self):
        """Tests that a valid Event instance is correctly identified."""
        event = Event("123e4567-e89b-12d3-a456-426614174000",
                      "test_stream", 42.0)
        self.assertTrue(event.is_valid())

    def test_invalid_event(self):
        """Tests that an invalid Event instance is correctly identified."""
        event = Event("", "test_stream", 42.0)
        self.assertFalse(event.is_valid())


if __name__ == '__main__':
    unittest.main()
