"""This module provides utility functions for the Chirpier SDK."""

import base64
import json


def is_valid_jwt(token):
    """
    Validates a JWT token by checking its structure and decoding its parts.

    Args:
        token (str): The JWT token to validate.

    Returns:
        bool: True if the token is a valid JWT, False otherwise.
    """
    if not isinstance(token, str):
        return False

    parts = token.split('.')
    if len(parts) != 3:
        return False

    try:
        # Validate header and payload are valid base64 and JSON
        for part in parts[:2]:
            # Add padding if needed
            padding = 4 - (len(part) % 4)
            if padding != 4:
                part += '=' * padding

            # Decode base64
            decoded = base64.urlsafe_b64decode(part)

            # Verify it's valid JSON
            json.loads(decoded)

        # Verify signature is valid base64
        sig_padding = 4 - (len(parts[2]) % 4)
        if sig_padding != 4:
            parts[2] += '=' * sig_padding
        base64.urlsafe_b64decode(parts[2])

    except (TypeError, ValueError, json.JSONDecodeError):
        return False

    return True
