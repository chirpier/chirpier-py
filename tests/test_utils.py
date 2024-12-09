"""This module provides tests for the utility functions in the Chirpier SDK."""

import unittest
from chirpier.utils import is_valid_jwt


class TestUtils(unittest.TestCase):
    """Tests for the utility functions."""

    def test_valid_jwt(self):
        """Tests that a valid JWT is correctly identified."""
        valid_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        self.assertTrue(is_valid_jwt(valid_jwt))

    def test_invalid_jwt(self):
        """Tests that an invalid JWT is correctly identified."""
        invalid_jwt = "invalid.jwt.token"
        self.assertFalse(is_valid_jwt(invalid_jwt))


if __name__ == '__main__':
    unittest.main()
