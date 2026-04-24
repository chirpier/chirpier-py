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


class ChirpierNonRetryableError(ChirpierError):
    """Raised when an ingest response should not be retried."""


class ChirpierUnauthorizedError(ChirpierNonRetryableError):
    """Raised when the API rejects a request with HTTP 401."""


class ChirpierForbiddenError(ChirpierNonRetryableError):
    """Raised when the API rejects a request with HTTP 403."""


class ChirpierNotFoundError(ChirpierNonRetryableError):
    """Raised when the API rejects a request with HTTP 404."""


class ChirpierInternalServerError(ChirpierNonRetryableError):
    """Raised when the API rejects a request with HTTP 500."""


class ChirpierServiceUnavailableError(ChirpierNonRetryableError):
    """Raised when the API rejects a request with HTTP 503."""
