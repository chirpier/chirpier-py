"""This module provides utility functions for the Chirpier SDK."""

import base64


def is_valid_jwt(token):
    """
    Validates a JWT token by checking its structure and attempting to decode its parts.

    Args:
        token (str): The JWT token to validate.

    Returns:
        bool: True if the token is a valid JWT, False otherwise.
    """
    parts = token.split('.')
    if len(parts) != 3:
        return False

    try:
        base64.urlsafe_b64decode(parts[0] + '==')
        base64.urlsafe_b64decode(parts[1] + '==')
    except (TypeError, ValueError):
        return False

    return True
