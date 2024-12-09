"""
This module provides the main entry point for the Chirpier SDK.

It exports the Client, ChirpierClientManager, Event, and ChirpierError classes.
"""

from .client import Client, ChirpierClientManager
from .event import Event
from .errors import ChirpierError

__all__ = ['Client', 'ChirpierClientManager', 'Event', 'ChirpierError']
