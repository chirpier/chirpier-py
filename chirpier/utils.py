"""Utility helpers for the Chirpier SDK."""

from __future__ import annotations

import os


def is_valid_api_key(token: str) -> bool:
    """Validate that an API key uses the expected Chirpier prefix."""
    return (
        isinstance(token, str) and token.startswith("chp_") and len(token) > len("chp_")
    )


def _read_dotenv_value(key: str, path: str = ".env") -> str | None:
    try:
        with open(path, "r", encoding="utf-8") as dotenv_file:
            for raw_line in dotenv_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                env_key, env_value = line.split("=", 1)
                if env_key.strip() != key:
                    continue
                value = env_value.strip().strip('"').strip("'")
                return value or None
    except FileNotFoundError:
        return None
    return None


def resolve_api_key(provided_key: str | None) -> str | None:
    """Resolve API key with precedence: provided -> env -> .env."""
    if isinstance(provided_key, str):
        key = provided_key.strip()
        if key:
            return key

    env_key = os.getenv("CHIRPIER_API_KEY", "").strip()
    if env_key:
        return env_key

    dotenv_key = _read_dotenv_value("CHIRPIER_API_KEY")
    return (
        dotenv_key.strip()
        if isinstance(dotenv_key, str) and dotenv_key.strip()
        else None
    )
