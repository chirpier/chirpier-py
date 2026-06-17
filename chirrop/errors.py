"""This module provides error classes for the ChirrOp SDK."""

from __future__ import annotations


class ChirrOpError(Exception):
    """
    Custom exception class for ChirrOp SDK errors.

    This exception is raised for SDK-specific errors such as initialization
    failures, queue overflow, or configuration issues.

    The error message is available via str(exception) or exception.args[0].
    """

    pass  # No need for custom __init__, Exception handles it perfectly


class ChirrOpNonRetryableError(ChirrOpError):
    """Raised when an ingest response should not be retried."""


class ChirrOpUnauthorizedError(ChirrOpNonRetryableError):
    """Raised when the API rejects a request with HTTP 401."""


class ChirrOpForbiddenError(ChirrOpNonRetryableError):
    """Raised when the API rejects a request with HTTP 403."""


class ChirrOpNotFoundError(ChirrOpNonRetryableError):
    """Raised when the API rejects a request with HTTP 404."""


class ChirrOpInternalServerError(ChirrOpNonRetryableError):
    """Raised when the API rejects a request with HTTP 500."""


class ChirrOpServiceUnavailableError(ChirrOpNonRetryableError):
    """Raised when the API rejects a request with HTTP 503."""
