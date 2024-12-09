"""This module provides error classes for the Chirpier SDK."""


class ChirpierError(Exception):
    """
    Custom exception class for Chirpier errors.

    Attributes:
        message (str): The error message.
    """

    def __init__(self, message):
        """
        Initializes a ChirpierError instance.

        Args:
            message (str): The error message.
        """
        super().__init__(message)
        self.message = message
