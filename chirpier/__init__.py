"""Public API exports for chirpier-py."""

from .client import (
    Client,
    Chirpier,
    Config,
    flush,
    initialize,
    log_event,
    new_client,
    stop,
)
from .errors import (
    ChirpierError,
    ChirpierForbiddenError,
    ChirpierInternalServerError,
    ChirpierNonRetryableError,
    ChirpierNotFoundError,
    ChirpierServiceUnavailableError,
    ChirpierUnauthorizedError,
)
from .log import Log

__all__ = [
    "Client",
    "Chirpier",
    "Config",
    "Log",
    "ChirpierError",
    "ChirpierNonRetryableError",
    "ChirpierUnauthorizedError",
    "ChirpierForbiddenError",
    "ChirpierNotFoundError",
    "ChirpierInternalServerError",
    "ChirpierServiceUnavailableError",
    "initialize",
    "log_event",
    "new_client",
    "flush",
    "stop",
]

__version__ = "0.0.6"
