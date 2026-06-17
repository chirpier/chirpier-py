"""Public API exports for chirrop-py."""

from .client import (
    Client,
    ChirrOp,
    Config,
    flush,
    initialize,
    log_event,
    new_client,
    stop,
)
from .errors import (
    ChirrOpError,
    ChirrOpForbiddenError,
    ChirrOpInternalServerError,
    ChirrOpNonRetryableError,
    ChirrOpNotFoundError,
    ChirrOpServiceUnavailableError,
    ChirrOpUnauthorizedError,
)
from .log import Log

__all__ = [
    "Client",
    "ChirrOp",
    "Config",
    "Log",
    "ChirrOpError",
    "ChirrOpNonRetryableError",
    "ChirrOpUnauthorizedError",
    "ChirrOpForbiddenError",
    "ChirrOpNotFoundError",
    "ChirrOpInternalServerError",
    "ChirrOpServiceUnavailableError",
    "initialize",
    "log_event",
    "new_client",
    "flush",
    "stop",
]

__version__ = "0.4.0"
