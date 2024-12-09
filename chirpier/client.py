"""This module provides a client for sending events to the Chirpier API."""

import threading
import time
try:
    import requests
except ImportError as exc:
    raise ImportError(
        "requests package is required. Please install it with 'pip install requests'"
    ) from exc

from .event import Event
from .errors import ChirpierError
from .utils import is_valid_jwt


class Client:
    """Client for sending events to the Chirpier API."""

    def __init__(self, api_key: str, api_endpoint: str = "https://events.chirpier.co/v1.0/events",
                 retries: int = 1, timeout: int = 10, batch_size: int = 50, flush_delay: float = 0.5):
        if not api_key or not is_valid_jwt(api_key):
            raise ChirpierError("Invalid API key: Not a valid JWT")

        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.retries = retries
        self.timeout = timeout
        self.batch_size = batch_size
        self.flush_delay = flush_delay
        self.event_queue = []
        self.queue_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def monitor(self, event: Event) -> None:
        """Add an event to the monitoring queue."""
        if not event.is_valid():
            raise ChirpierError(
                "Invalid event format. Must include group_id, stream_name, and numeric value")

        with self.queue_lock:
            self.event_queue.append(event)
            if len(self.event_queue) >= self.batch_size:
                self.flush_events()

    def stop(self) -> None:
        """Stop the monitoring thread and flush remaining events."""
        self.stop_event.set()
        self.thread.join()
        self.flush_events()

    def run(self) -> None:
        """Run the monitoring thread."""
        while not self.stop_event.is_set():
            time.sleep(self.flush_delay)
            self.flush_events()

    def flush_events(self) -> None:
        """Flush queued events to the API."""
        with self.queue_lock:
            if not self.event_queue:
                return
            events = self.event_queue[:]
            self.event_queue.clear()

        try:
            self.send_events(events)
        except ChirpierError as e:
            with self.queue_lock:
                self.event_queue.extend(events)
            print(f"Failed to send events: {e}")

    def send_events(self, events: list[Event]) -> None:
        """Send events to the API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        for attempt in range(self.retries + 1):
            try:
                response = requests.post(
                    self.api_endpoint,
                    json=[event.to_dict() for event in events],
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                print(f"Successfully sent {len(events)} events")
                return
            except requests.RequestException as e:
                if attempt == self.retries:
                    raise ChirpierError(
                        "Failed to send request after retries") from e
                time.sleep(2 ** attempt)


class Chirpier:
    """Manager for the global Chirpier client."""
    _client = None

    @classmethod
    def initialize(cls, api_key: str, api_endpoint: str = None) -> None:
        """Initialize the global Chirpier client."""
        if cls._client is not None:
            raise ChirpierError("Chirpier SDK is already initialized")
        cls._client = Client(api_key, api_endpoint)

    @classmethod
    def monitor(cls, event: Event) -> None:
        """Monitor an event using the global client."""
        if cls._client is None:
            raise ChirpierError(
                "Chirpier SDK is not initialized. Please call initialize() first")
        cls._client.monitor(event)

    @classmethod
    def stop(cls) -> None:
        """Stop the global client."""
        if cls._client is not None:
            cls._client.stop()
            cls._client = None

# Usage
# Chirpier.initialize(api_key)
# Chirpier.monitor(event)
# Chirpier.stop()
