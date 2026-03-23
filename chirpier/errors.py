"""This module provides error classes for the Chirpier SDK."""

from __future__ import annotations


class ChirpierError(Exception):
    """
    Custom exception class for Chirpier SDK errors.

    This exception is raised for SDK-specific errors such as initialization
    failures, queue overflow, or configuration issues.

    The error message is available via str(exception) or exception.args[0].
    """

    pass  # No need for custom __init__, Exception handles it perfectly
