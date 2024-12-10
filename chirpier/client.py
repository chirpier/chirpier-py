"""This module provides a client for sending events to the Chirpier API."""

import threading
import time
try:
    import requests
    from queue import Queue
except ImportError as exc:
    raise ImportError(
        "requests package is required. Please install it with 'pip install requests'"
    ) from exc

from .event import Event
from .errors import ChirpierError
from .utils import is_valid_jwt


class Config:
    """Configuration for the Chirpier client."""

    def __init__(self,
                 api_key: str,
                 api_endpoint: str = "https://events.chirpier.co/v1.0/events",
                 batch_size: int = 50,
                 flush_delay: float = 0.5):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.retries = 5
        self.timeout = 10
        self.batch_size = batch_size
        self.flush_delay = flush_delay

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "api_key": self.api_key,
            "api_endpoint": self.api_endpoint,
            "retries": self.retries,
            "timeout": self.timeout,
            "batch_size": self.batch_size,
            "flush_delay": self.flush_delay
        }

    def update(self, **kwargs) -> None:
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class Client:
    """Client for sending events to the Chirpier API."""

    def __init__(self, config: Config):
        if not config.api_key or not is_valid_jwt(config.api_key):
            raise ChirpierError("Invalid API key: Not a valid JWT")

        self.config = config
        self.event_queue = Queue()
        self.queue_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def monitor(self, event: Event) -> None:
        """Add an event to the monitoring queue."""
        if not event.is_valid():
            raise ChirpierError("Invalid event format")
        self.event_queue.put(event)

    def stop(self) -> None:
        """Stop the monitoring thread and flush remaining events."""
        self.stop_event.set()
        self.thread.join()
        self.flush_events()

    def run(self) -> None:
        """Run the monitoring thread."""
        while not self.stop_event.is_set():
            time.sleep(self.config.flush_delay)
            self.flush_events()

    def flush_events(self) -> None:
        """Flush queued events to the API."""
        events = []
        while not self.event_queue.empty():
            events.append(self.event_queue.get())

        if not events:
            return

        try:
            self.send_events(events)
        except ChirpierError as e:
            # Put events back in queue
            for event in events:
                self.event_queue.put(event)
            print(f"Failed to send events: {e}")

    def send_events(self, events: list[Event]) -> None:
        """Send events to the API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key.strip()}"
        }
        for attempt in range(self.config.retries + 1):
            try:
                response = requests.post(
                    self.config.api_endpoint,
                    json=[event.to_dict() for event in events],
                    headers=headers,
                    timeout=self.config.timeout
                )
                if not response.ok:
                    raise requests.RequestException(
                        f"Request failed with status code {response.status_code}")
                print(f"Successfully sent {len(events)} events")
                break
            except requests.RequestException as e:
                print("Request failed")
                if attempt == self.config.retries:
                    raise ChirpierError(
                        f"Failed to send request after retries: {str(e)}") from e
                # Cap exponential backoff at 30 seconds
                time.sleep(min(2 ** attempt, 30))


class Chirpier:
    """Manager for the global Chirpier client."""
    _client = None

    @classmethod
    def initialize(cls, api_key: str,
                   api_endpoint: str = "https://events.chirpier.co/v1.0/events") -> None:
        """Initialize the global Chirpier client."""
        if cls._client is not None:
            raise ChirpierError("Chirpier SDK is already initialized")
        cls._client = Client(Config(api_key, api_endpoint))

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
