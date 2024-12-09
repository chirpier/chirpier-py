"""
This module provides the main entry point for the Chirpier SDK.

It exports the Client, Chirpier, Event, and ChirpierError classes.
"""

from .client import Client, Chirpier
from .event import Event
from .errors import ChirpierError

__all__ = ['Client', 'Chirpier', 'Event', 'ChirpierError']
