"""Log model for the Chirpier SDK."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
import math
from typing import Any


@dataclass(slots=True)
class Log:
    """Represents a log entry sent to Chirpier."""

    event: str
    value: float | int
    agent_id: str | None = None
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

        if self.agent_id is not None:
            if not isinstance(self.agent_id, str):
                raise ValueError("agent_id must be a string when provided")
            self.agent_id = self.agent_id.strip() or None

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
        if payload["agent_id"] is None:
            payload.pop("agent_id")
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
