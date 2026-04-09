"""Example usage for chirpier-py."""

from datetime import datetime, timezone

from chirpier import Chirpier, Log


def main() -> None:
    Chirpier.initialize(api_key="chp_your_api_key")
    Chirpier.log_event(
        Log(
            agent="api.worker",
            event="request_finished",
            value=1,
            occurred_at=datetime.now(timezone.utc),
            meta={"path": "/v1.0/logs", "status": "ok"},
        )
    )
    Chirpier.flush()
    Chirpier.stop()


if __name__ == "__main__":
    main()
