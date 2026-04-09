# Chirpier SDK

The Chirpier SDK for Python sends OpenClaw-friendly flat events to Chirpier/Ingres with batching and retries.

## Installation

<!-- docs:start install -->
```bash
pip install chirpier
```
<!-- docs:end install -->

## Quick Start

<!-- docs:start quickstart -->
### Global API

```python
from chirpier import Chirpier, Log

Chirpier.initialize(api_key="chp_your_api_key")
Chirpier.log_event(Log(log_id="9f97d65f-fb30-4062-b4d0-8617c03fe4f6", event="tool.errors.count", value=1, agent="openclaw.main", meta={"tool_name": "browser.open"}))
Chirpier.flush()
Chirpier.stop()
```

### Instance API (Recommended)

```python
from chirpier import new_client, Log

client = new_client(api_key="chp_your_api_key")
client.log(Log(event="task.duration_ms", value=420, agent="openclaw.main", meta={"task_name": "email_triage"}))
client.flush()
client.close()
```
<!-- docs:end quickstart -->

## API

### Config

`Config` fields:
- `api_key` (str, optional): API key. Must start with `chp_`.
- `api_endpoint` (str, optional): Full ingestion endpoint override.
- `servicer_endpoint` (str, optional): Control-plane endpoint override. Defaults to `https://api.chirpier.co/v1.0`.
- `retries` (int, optional): Retry attempts.
- `timeout` (float, optional): HTTP timeout in seconds.
- `batch_size` (int, optional): Flush threshold.
- `flush_delay` (float, optional): Worker flush interval in seconds.
- `queue_size` (int, optional): In-memory queue capacity. `0` means unbounded and is the default.
- `log_level` (int, optional): Python logging level.

API key resolution precedence when `api_key` is omitted:
1. `api_key` passed in Config/initialize
2. `CHIRPIER_API_KEY` process environment variable
3. `CHIRPIER_API_KEY` in local `.env`

Default ingest endpoint: `https://logs.chirpier.co/v1.0/logs`.
Default servicer endpoint: `https://api.chirpier.co/v1.0`.
The same bearer token is used for both ingest and servicer APIs.
Queued logs are not dropped locally because of queue capacity or retry exhaustion.

### Log

`Log` fields:
- `agent` (str, optional): Free-form agent identifier text.
- `log_id` (str, optional): UUID idempotency key for the log. Generated automatically when omitted.
- `event` (str, required): Event name.
- `value` (number, required): Numeric value.
- `occurred_at` (datetime | str, optional): Event occurrence timestamp.
- `meta` (json, optional): Additional JSON-encodable metadata.

Example with `occurred_at`:

```python
from datetime import datetime, timezone

entry = Log(
    agent="openclaw.main",
    event="tokens.used",
    value=1530,
    occurred_at=datetime(2026, 3, 5, 14, 30, 0, tzinfo=timezone.utc),
)
```

Notes:
- `agent` whitespace-only values are treated as omitted.
- `log_id` blank values are treated as omitted and replaced with a generated UUIDv4.
- `event` must be non-empty after trimming.
- `occurred_at` must be within the last 30 days and no more than 1 day in the future.
- Use timezone-aware UTC datetimes or ISO8601 UTC strings, for example `2026-03-05T14:30:00Z`.
- `meta` must be JSON-encodable.
- Unknown events are auto-created in Ingres as event definitions.

### Event definition helpers

<!-- docs:start common-tasks -->
```python
events = client.list_events()
event_def = client.get_event(events[0]["event_id"])
updated = client.update_event(event_def["event_id"], {
    "description": "OpenClaw Tool Errors",
})
```

### Policy and alert helpers

```python
policies = client.list_policies()
policy = client.create_policy({
    "event_id": "evt_123",
    "title": "OpenClaw tool errors spike",
    "condition": "gt",
    "threshold": 5,
    "period": "hour",
    "aggregate": "sum",
    "enabled": True,
})
alerts = client.list_alerts("triggered")
deliveries = client.get_alert_deliveries(alerts[0]["alert_id"], limit=20, offset=0, kind="alert")
rollups = client.get_event_logs("evt_123", period="hour", limit=25, offset=0)
ack = client.acknowledge_alert(alerts[0]["alert_id"])
resolved = client.resolve_alert(ack["alert_id"])
archived = client.archive_alert(resolved["alert_id"])
client.test_webhook("whk_123")
```
<!-- docs:end common-tasks -->

### Convenience constructor

Use `new_client(...)` to create standalone clients without manually constructing `Config`.

## Connector Setup Examples

Create a Slack connector for OpenClaw alerts:

```python
import requests

requests.post(
    "https://api.chirpier.co/v1.0/webhooks",
    json={
        "url": "https://hooks.slack.com/services/T000/B000/secret",
        "type": "slack",
        "enabled": True,
    },
    headers={"Authorization": f"Bearer {api_key}"},
    timeout=10,
)
```

Create a Telegram connector for OpenClaw alerts:

```python
requests.post(
    "https://api.chirpier.co/v1.0/webhooks",
    json={
        "type": "telegram",
        "enabled": True,
        "credentials": {
            "bot_token": "123456:telegram-bot-token",
            "chat_id": "987654321",
        },
    },
    headers={"Authorization": f"Bearer {api_key}"},
    timeout=10,
)
```

Send a test notification:

```python
client.test_webhook("whk_123")
```
