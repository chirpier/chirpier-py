"""Client implementation for sending logs to the Chirpier API."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from queue import Empty, Queue
import random
from threading import Event as ThreadEvent
from threading import Lock, Thread
import time
from typing import ClassVar
from urllib.parse import urlparse

import requests

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
from .utils import is_valid_api_key, resolve_api_key

DEFAULT_API_ENDPOINT = "https://logs.chirpier.co/v1.0/logs"
DEFAULT_SERVICER_ENDPOINT = "https://api.chirpier.co/v1.0"


def classify_log_response_status(status_code: int) -> str:
    if status_code == 429:
        return "retry_after"
    if status_code >= 500:
        if status_code in (500, 503):
            return "non_retryable"
        return "retryable"
    if status_code >= 400:
        return "non_retryable"
    return "success"


def get_response_body_text(response: requests.Response) -> str:
    body = response.text if isinstance(response.text, str) else ""
    return body.strip()


def build_non_retryable_error(status_code: int, body_text: str) -> ChirpierNonRetryableError:
    message = f"HTTP {status_code}"
    if body_text:
        message = f"{message}: {body_text}"

    if status_code == 401:
        return ChirpierUnauthorizedError(message)
    if status_code == 403:
        return ChirpierForbiddenError(message)
    if status_code == 404:
        return ChirpierNotFoundError(message)
    if status_code == 500:
        return ChirpierInternalServerError(message)
    if status_code == 503:
        return ChirpierServiceUnavailableError(message)
    return ChirpierNonRetryableError(message)


@dataclass(slots=True)
class Config:
    """Configuration for Chirpier clients."""

    api_key: str | None = None
    api_endpoint: str = DEFAULT_API_ENDPOINT
    servicer_endpoint: str = DEFAULT_SERVICER_ENDPOINT
    retries: int = 10
    timeout: int | float = 10
    batch_size: int = 500
    flush_delay: float = 0.5
    queue_size: int = 0
    log_level: int = logging.NOTSET

    def __post_init__(self) -> None:
        if self.retries < 0:
            raise ValueError("retries must be non-negative")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.flush_delay < 0:
            raise ValueError("flush_delay must be non-negative")
        if self.queue_size < 0:
            raise ValueError("queue_size must be non-negative")
        if not isinstance(self.api_endpoint, str) or not self.api_endpoint.strip():
            raise ValueError("api_endpoint must be a non-empty string")

        parsed = urlparse(self.api_endpoint)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("api_endpoint must be a valid absolute URL")

        if self.servicer_endpoint is None:
            self.servicer_endpoint = DEFAULT_SERVICER_ENDPOINT

        parsed_servicer = urlparse(self.servicer_endpoint)
        if (
            parsed_servicer.scheme not in ("http", "https")
            or not parsed_servicer.netloc
        ):
            raise ValueError("servicer_endpoint must be a valid absolute URL")


class Client:
    """Standalone client instance for sending logs."""

    def __init__(self, config: Config):
        resolved_key = resolve_api_key(config.api_key)
        if not resolved_key:
            raise ValueError("API key is required")
        if not is_valid_api_key(resolved_key):
            raise ValueError("Invalid API key: must start with 'chp_'")

        config.api_key = resolved_key
        if config.servicer_endpoint is None:
            config.servicer_endpoint = DEFAULT_SERVICER_ENDPOINT
        config.servicer_endpoint = config.servicer_endpoint.rstrip("/")
        self.config = config

        self.log_queue: Queue[Log] = Queue(maxsize=config.queue_size)
        self.logger = logging.getLogger("chirpier")
        self.logger.setLevel(config.log_level)
        self._terminate_event = ThreadEvent()
        self._flush_now_event = ThreadEvent()
        self._idle_event = ThreadEvent()
        self._idle_event.set()
        self._state_lock = Lock()
        self._inflight = 0
        self._queue_lock = Lock()
        self._worker = Thread(target=self._process_logs, daemon=True)
        self._worker.start()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()

    def log(self, entry: Log) -> None:
        """Queue a log entry for async delivery."""
        if not isinstance(entry, Log):
            raise ValueError("entry must be an instance of Log")

        with self._queue_lock:
            self.log_queue.put(entry)
            self._idle_event.clear()

    def flush(self) -> None:
        """Block until currently queued logs are processed."""
        self._flush_now_event.set()
        self.log_queue.join()
        self._idle_event.wait(timeout=self.config.timeout)

    def shutdown(self) -> None:
        """Gracefully shut down the worker after flushing queued logs."""
        self._flush_now_event.set()
        self._terminate_event.set()
        self._worker.join()
        self.log_queue.join()

    def close(self) -> None:
        """Alias for shutdown()."""
        self.shutdown()

    def _process_logs(self) -> None:
        batch: list[Log] = []

        while not self._terminate_event.is_set() or not self.log_queue.empty():
            try:
                poll_timeout = min(self.config.flush_delay, 0.1)
                if poll_timeout <= 0:
                    poll_timeout = 0.1

                entry = self.log_queue.get(timeout=poll_timeout)
                batch.append(entry)

                if len(batch) >= self.config.batch_size:
                    self._flush_batch(batch)
            except Empty:
                if batch and self._flush_now_event.is_set():
                    self._flush_now_event.clear()
                    self._flush_batch(batch)
                elif batch:
                    self._flush_batch(batch)

            if batch and self._flush_now_event.is_set():
                self._flush_now_event.clear()
                self._flush_batch(batch)

        if batch:
            self._flush_batch(batch)

    def _flush_batch(self, batch: list[Log]) -> None:
        with self._state_lock:
            self._inflight += 1
            self._idle_event.clear()

        try:
            self.send_logs(batch)
            self.logger.info("Successfully sent batch of %d logs", len(batch))
        except ChirpierNonRetryableError as exc:
            self.logger.error("Failed to send logs: %s", exc)
        except (requests.RequestException, ChirpierError) as exc:
            self.logger.error("Failed to send logs: %s", exc)
            for entry in batch:
                self.log_queue.put(entry)
        finally:
            for _ in batch:
                self.log_queue.task_done()
            with self._state_lock:
                self._inflight -= 1
                if self.log_queue.unfinished_tasks == 0 and self._inflight == 0:
                    self._idle_event.set()
            batch.clear()

    def send_logs(self, entries: list[Log]) -> None:
        """Send logs to Chirpier with retry and exponential backoff."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

        payload = [entry.to_dict() for entry in entries]

        for attempt in range(self.config.retries + 1):
            try:
                response = requests.post(
                    self.config.api_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.config.timeout,
                )
                if response.ok:
                    return

                status_policy = classify_log_response_status(response.status_code)
                body_text = get_response_body_text(response)

                if status_policy == "non_retryable":
                    raise build_non_retryable_error(response.status_code, body_text)

                if status_policy in ("retry_after", "retryable"):
                    if attempt < self.config.retries:
                        backoff = min(2**attempt, 30) + random.uniform(
                            0, 0.3 * min(2**attempt, 30)
                        )
                        if status_policy == "retry_after" and "Retry-After" in response.headers:
                            try:
                                backoff = float(response.headers["Retry-After"])
                            except (ValueError, TypeError):
                                pass
                        time.sleep(backoff)
                        continue

                message = f"HTTP {response.status_code}"
                if body_text:
                    message = f"{message}: {body_text}"
                raise requests.RequestException(message)
            except ChirpierNonRetryableError:
                raise
            except requests.RequestException:
                if attempt == self.config.retries:
                    raise
                backoff = min(2**attempt, 30) + random.uniform(
                    0, 0.3 * min(2**attempt, 30)
                )
                time.sleep(backoff)

    def list_events(self) -> list[dict]:
        response = requests.get(
            f"{self.config.servicer_endpoint}/events",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def create_event(self, payload: dict) -> dict:
        response = requests.post(
            f"{self.config.servicer_endpoint}/events",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_event(self, event_id: str) -> dict:
        response = requests.get(
            f"{self.config.servicer_endpoint}/events/{event_id.strip()}",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def update_event(self, event_id: str, payload: dict) -> dict:
        response = requests.put(
            f"{self.config.servicer_endpoint}/events/{event_id.strip()}",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def list_policies(self) -> list[dict]:
        response = requests.get(
            f"{self.config.servicer_endpoint}/policies",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def create_policy(self, payload: dict) -> dict:
        response = requests.post(
            f"{self.config.servicer_endpoint}/policies",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_policy(self, policy_id: str) -> dict:
        response = requests.get(
            f"{self.config.servicer_endpoint}/policies/{policy_id.strip()}",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def update_policy(self, policy_id: str, payload: dict) -> dict:
        response = requests.put(
            f"{self.config.servicer_endpoint}/policies/{policy_id.strip()}",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def list_alerts(self, status: str | None = None) -> list[dict]:
        params = {"status": status} if status else None
        response = requests.get(
            f"{self.config.servicer_endpoint}/alerts",
            params=params,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_alert(self, alert_id: str) -> dict:
        response = requests.get(
            f"{self.config.servicer_endpoint}/alerts/{alert_id.strip()}",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def acknowledge_alert(self, alert_id: str) -> dict:
        response = requests.post(
            f"{self.config.servicer_endpoint}/alerts/{alert_id.strip()}/acknowledge",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def resolve_alert(self, alert_id: str) -> dict:
        response = requests.post(
            f"{self.config.servicer_endpoint}/alerts/{alert_id.strip()}/resolve",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def archive_alert(self, alert_id: str) -> dict:
        response = requests.post(
            f"{self.config.servicer_endpoint}/alerts/{alert_id.strip()}/archive",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def list_destinations(self) -> list[dict]:
        response = requests.get(
            f"{self.config.servicer_endpoint}/destinations",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def create_destination(self, payload: dict) -> dict:
        response = requests.post(
            f"{self.config.servicer_endpoint}/destinations",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_destination(self, destination_id: str) -> dict:
        response = requests.get(
            f"{self.config.servicer_endpoint}/destinations/{destination_id.strip()}",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def update_destination(self, destination_id: str, payload: dict) -> dict:
        response = requests.put(
            f"{self.config.servicer_endpoint}/destinations/{destination_id.strip()}",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def test_destination(self, destination_id: str) -> dict:
        response = requests.post(
            f"{self.config.servicer_endpoint}/destinations/{destination_id.strip()}/test",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_event_analytics(
        self,
        event_id: str,
        *,
        view: str = "window",
        period: str,
        previous: str,
    ) -> dict:
        response = requests.get(
            f"{self.config.servicer_endpoint}/events/{event_id.strip()}/analytics",
            params={"view": view, "period": period, "previous": previous},
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_alert_deliveries(
        self,
        alert_id: str,
        limit: int | None = None,
        offset: int | None = None,
        kind: str | None = None,
    ) -> list[dict]:
        params = {}
        if kind is not None:
            params["kind"] = kind
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        response = requests.get(
            f"{self.config.servicer_endpoint}/alerts/{alert_id.strip()}/deliveries",
            params=params or None,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_event_logs(
        self,
        event_id: str,
        period: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict]:
        params = {}
        if period:
            params["period"] = period
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        response = requests.get(
            f"{self.config.servicer_endpoint}/events/{event_id.strip()}/logs",
            params=params or None,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()


class Chirpier:
    """Global singleton manager for package-level usage."""

    _client: ClassVar[Client | None] = None

    @classmethod
    def initialize(cls, config: Config | None = None, **kwargs) -> None:
        if cls._client is not None:
            raise ChirpierError("Chirpier SDK is already initialized")

        client_config = config if config is not None else Config(**kwargs)
        cls._client = Client(client_config)

    @classmethod
    def log_event(cls, entry: Log) -> None:
        if cls._client is None:
            raise ChirpierError(
                "Chirpier SDK is not initialized. Please call initialize() first"
            )
        cls._client.log(entry)

    @classmethod
    def flush(cls) -> None:
        if cls._client is None:
            raise ChirpierError(
                "Chirpier SDK is not initialized. Please call initialize() first"
            )
        cls._client.flush()

    @classmethod
    def stop(cls) -> None:
        if cls._client is not None:
            cls._client.shutdown()
            cls._client = None


def initialize(config: Config | None = None, **kwargs) -> None:
    """Initialize global singleton client."""
    Chirpier.initialize(config=config, **kwargs)


def log_event(entry: Log) -> None:
    """Queue a log using the global singleton client."""
    Chirpier.log_event(entry)


def flush() -> None:
    """Flush queued logs for the global singleton client."""
    Chirpier.flush()


def stop() -> None:
    """Stop the global singleton client."""
    Chirpier.stop()


def new_client(config: Config | None = None, **kwargs) -> Client:
    """Create a standalone client instance (recommended)."""
    client_config = config if config is not None else Config(**kwargs)
    return Client(client_config)
