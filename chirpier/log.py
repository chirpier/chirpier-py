"""Log model for the Chirpier SDK."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
import math
from typing import Any
from uuid import UUID
from uuid6 import uuid7


@dataclass(slots=True)
class Log:
    """Represents a log entry sent to Chirpier."""

    event: str
    value: float | int
    agent: str | None = None
    log_id: str | None = None
    meta: Any = None
    occurred_at: datetime | str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event, str) or not self.event.strip():
            raise ValueError("event must be a non-empty string")
        self.event = self.event.strip()

        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError("value must be a number")
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError("value must be finite")

        if self.agent is not None:
            if not isinstance(self.agent, str):
                raise ValueError("agent must be a string when provided")
            self.agent = self.agent.strip() or None

        if self.log_id is None:
            self.log_id = str(uuid7())
        elif not isinstance(self.log_id, str):
            raise ValueError("log_id must be a UUID string when provided")
        else:
            self.log_id = self.log_id.strip()
            if not self.log_id:
                self.log_id = str(uuid7())
            else:
                try:
                    self.log_id = str(UUID(self.log_id))
                except ValueError as exc:
                    raise ValueError(
                        "log_id must be a UUID string when provided"
                    ) from exc

        if self.meta is not None:
            try:
                if json.dumps(self.meta) is None:
                    raise ValueError("meta must be JSON-encodable")
            except (TypeError, ValueError) as exc:
                raise ValueError("meta must be JSON-encodable") from exc

        if self.occurred_at is not None:
            if isinstance(self.occurred_at, str):
                normalized = self.occurred_at.replace("Z", "+00:00")
                try:
                    self.occurred_at = datetime.fromisoformat(normalized)
                except ValueError as exc:
                    raise ValueError(
                        "occurred_at must be a valid ISO 8601 datetime"
                    ) from exc
            elif not isinstance(self.occurred_at, datetime):
                raise ValueError("occurred_at must be a datetime or ISO 8601 string")

            if self.occurred_at.tzinfo is None:
                self.occurred_at = self.occurred_at.replace(tzinfo=timezone.utc)
            else:
                self.occurred_at = self.occurred_at.astimezone(timezone.utc)

            now = datetime.now(timezone.utc)
            oldest_allowed = now - timedelta(days=30)
            newest_allowed = now + timedelta(days=1)
            if self.occurred_at < oldest_allowed or self.occurred_at > newest_allowed:
                raise ValueError(
                    "occurred_at must be within the last 30 days and no more than 1 day in the future"
                )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if payload["agent"] is None:
            payload.pop("agent")
        if payload["meta"] is None:
            payload.pop("meta")
        if payload["occurred_at"] is None:
            payload.pop("occurred_at")
        elif isinstance(payload["occurred_at"], datetime):
            payload["occurred_at"] = (
                payload["occurred_at"]
                .astimezone(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )
        return payload
