"""This module provides a client for sending events to the Chirpier API."""

import logging
from threading import Thread, Event as ThreadEvent, Lock
import time
try:
    import requests
    from queue import Queue, Full, Empty
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
                 region: str = "eu-west",
                 log_level: int = logging.NOTSET):
        self.api_key = api_key
        self.retries = 10
        self.timeout = 10
        self.batch_size = 350
        self.flush_delay = 0.5
        self.queue_size = 50000
        self.log_level = log_level
        self.api_endpoint = f"https://{region}.chirpier.co/v1.0/events"

        """Set the region, validating it is one of the allowed values."""
        if region not in {"us-west", "eu-west", "asia-southeast"}:
            raise ValueError(
                f"{region} is not a valid region. Please use one of: us-west, eu-west, asia-southeast")

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "api_key": self.api_key,
            "api_endpoint": self.api_endpoint,
            "retries": self.retries,
            "timeout": self.timeout,
            "batch_size": self.batch_size,
            "flush_delay": self.flush_delay,
            "log_level": self.log_level,
            "queue_size": self.queue_size
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
            raise ValueError("Invalid API key: Not a valid JWT")

        self.config = config
        self.event_queue = Queue(maxsize=config.queue_size)
        self.logger = logging.getLogger("chirpier")
        self.logger.setLevel(config.log_level)
        self._terminate_event = ThreadEvent()
        self._worker = Thread(target=self._process_events, daemon=True)
        self._queue_lock = Lock()
        self._worker.start()

    def monitor(self, event: Event) -> None:
        """Queue an event for processing."""
        if not event.is_valid():
            raise ValueError("Invalid event format")

        with self._queue_lock:
            if self.event_queue.full():
                self.logger.debug(
                    "Event queue is full, dropping event: %s", event)
                return
            try:
                self.event_queue.put(
                    event, block=True, timeout=self.config.timeout)
            except Full as exc:
                self.logger.debug(
                    "Event queue put timed out, dropping event: %s", exc)
                return

    def _process_events(self) -> None:
        """Process events from the queue."""
        batch = []

        while not self._terminate_event.is_set() or not self.event_queue.empty():
            try:
                event = self.event_queue.get(timeout=self.config.flush_delay)
                batch.append(event)

                if len(batch) >= self.config.batch_size:
                    self._flush_batch(batch)
            except Empty:
                if batch:
                    self._flush_batch(batch)

    def _flush_batch(self, batch: list[Event]) -> None:
        try:
            # send_events expects a list of Event objects
            self.send_events(batch)
            for _ in batch:
                self.event_queue.task_done()
            self.logger.info(
                "Successfully sent batch of %d events", len(batch))
        except (requests.RequestException, ChirpierError) as exc:
            self.logger.error("Failed to send events: %s", exc)
            # Drop events if failed to send
            for _ in batch:
                self.event_queue.task_done()
        finally:
            batch.clear()

    def shutdown(self) -> None:
        """Gracefully shut down the client."""
        self._terminate_event.set()
        self._worker.join()
        self.event_queue.join()

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
                if response.ok:
                    return
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.config.retries:
                        # Cap exponential backoff at 30 seconds
                        backoff = min(2 ** attempt, 30)
                        if response.status_code == 429 and 'Retry-After' in response.headers:
                            try:
                                backoff = int(response.headers['Retry-After'])
                            except (ValueError, TypeError):
                                pass
                        time.sleep(backoff)
                        continue
                raise requests.RequestException(f"HTTP {response.status_code}")
            except requests.RequestException as e:
                logging.error("Request failed: %s", e)
                if attempt == self.config.retries:
                    logging.error(
                        "Failed to send request after retries: %s", e)
                    raise  # Re-raise to be caught by _flush_batch
                # Cap exponential backoff at 30 seconds
                time.sleep(min(2 ** attempt, 30))


class Chirpier:
    """Manager for the global Chirpier client."""
    _client = None

    @classmethod
    def initialize(cls, api_key: str,
                   region: str = "events",
                   log_level: int = logging.NOTSET) -> None:
        """Initialize the global Chirpier client."""
        if cls._client is not None:
            raise ChirpierError("Chirpier SDK is already initialized")
        cls._client = Client(
            Config(api_key, region, log_level=log_level))

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
            cls._client.shutdown()
            cls._client = None

# Usage
# Chirpier.initialize(api_key)
# Chirpier.monitor(event)
# Chirpier.stop()
