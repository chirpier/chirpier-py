"""Example usage for chirrop-py."""

from datetime import datetime, timezone

from chirrop import ChirrOp, Log


def main() -> None:
    ChirrOp.initialize(api_key="chp_your_api_key")
    ChirrOp.log_event(
        Log(
            agent="api.worker",
            event="request_finished",
            value=1,
            occurred_at=datetime.now(timezone.utc),
            meta={"path": "/v1.0/logs", "status": "ok"},
        )
    )
    ChirrOp.flush()
    ChirrOp.stop()


if __name__ == "__main__":
    main()
