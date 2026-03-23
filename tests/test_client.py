"""Tests for client and global SDK APIs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import MagicMock, patch

from chirpier import Chirpier, ChirpierError, Client, Config, Log, new_client


class TestClient(unittest.TestCase):
    def setUp(self):
        Chirpier._client = None

        self.requests_patcher = patch("chirpier.client.requests")
        self.mock_requests = self.requests_patcher.start()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        self.mock_requests.post.return_value = mock_response
        self.mock_requests.get.return_value = mock_response
        self.mock_requests.put.return_value = mock_response

    def tearDown(self):
        self.requests_patcher.stop()
        if Chirpier._client is not None:
            Chirpier._client.shutdown()
            Chirpier._client = None

    def test_initialize_invalid_key(self):
        with self.assertRaises(ValueError) as ctx:
            Chirpier.initialize(api_key="invalid")
        self.assertEqual(str(ctx.exception), "Invalid API key: must start with 'chp_'")

    def test_initialize_twice(self):
        Chirpier.initialize(api_key="chp_test_key")
        with self.assertRaises(ChirpierError) as ctx:
            Chirpier.initialize(api_key="chp_test_key")
        self.assertEqual(str(ctx.exception), "Chirpier SDK is already initialized")

    def test_log_event_without_init(self):
        with self.assertRaises(ChirpierError) as ctx:
            Chirpier.log_event(Log(event="test", value=1))
        self.assertEqual(
            str(ctx.exception),
            "Chirpier SDK is not initialized. Please call initialize() first",
        )

    def test_global_log_event(self):
        Chirpier.initialize(api_key="chp_test_key")
        Chirpier.log_event(
            Log(event="request_finished", value=1, agent_id="api.worker")
        )
        Chirpier.flush()

        self.assertTrue(self.mock_requests.post.called)
        call_kwargs = self.mock_requests.post.call_args.kwargs
        self.assertEqual(call_kwargs["json"][0]["event"], "request_finished")
        self.assertEqual(call_kwargs["json"][0]["agent_id"], "api.worker")

    def test_client_instance_api(self):
        client = Client(Config(api_key="chp_client_key", flush_delay=0.05))
        try:
            client.log(Log(event="instance.log", value=1, meta={"ok": True}))
            client.flush()

            self.assertTrue(self.mock_requests.post.called)
            call_kwargs = self.mock_requests.post.call_args.kwargs
            self.assertEqual(call_kwargs["json"][0]["event"], "instance.log")
            self.assertEqual(call_kwargs["json"][0]["meta"]["ok"], True)
        finally:
            client.shutdown()

    def test_new_client_factory(self):
        client = new_client(api_key="chp_factory_key", flush_delay=0.05)
        try:
            client.log(Log(event="factory.log", value=1))
            client.flush()
            self.assertTrue(self.mock_requests.post.called)
        finally:
            client.close()

    def test_agent_id_whitespace_omitted(self):
        Chirpier.initialize(api_key="chp_test_key")
        Chirpier.log_event(Log(event="request_finished", value=1, agent_id="   "))
        Chirpier.flush()

        call_kwargs = self.mock_requests.post.call_args.kwargs
        self.assertNotIn("agent_id", call_kwargs["json"][0])

    def test_occurred_at_in_payload(self):
        Chirpier.initialize(api_key="chp_test_key")
        occurred_at = datetime.now(timezone.utc) - timedelta(hours=1)
        Chirpier.log_event(
            Log(event="request_finished", value=1, occurred_at=occurred_at)
        )
        Chirpier.flush()

        call_kwargs = self.mock_requests.post.call_args.kwargs
        self.assertIn("occurred_at", call_kwargs["json"][0])
        self.assertTrue(call_kwargs["json"][0]["occurred_at"].endswith("Z"))

    def test_config_custom_endpoint(self):
        client = Client(
            Config(
                api_key="chp_test_key", api_endpoint="https://localhost:3001/v1.0/logs"
            )
        )
        try:
            client.log(Log(event="endpoint.test", value=1))
            client.flush()
            call_args = self.mock_requests.post.call_args.args
            self.assertEqual(call_args[0], "https://localhost:3001/v1.0/logs")
        finally:
            client.shutdown()

    def test_invalid_api_endpoint(self):
        with self.assertRaises(ValueError) as ctx:
            Config(api_key="chp_test_key", api_endpoint="not-a-url")
        self.assertEqual(
            str(ctx.exception), "api_endpoint must be a valid absolute URL"
        )

    def test_list_events_uses_servicer_endpoint(self):
        client = Client(Config(api_key="chp_test_key"))
        try:
            client.list_events()
            call_args = self.mock_requests.get.call_args.args
            self.assertEqual(call_args[0], "https://api.chirpier.co/v1.0/events")
        finally:
            client.shutdown()

    def test_update_event_uses_same_bearer_token(self):
        client = Client(Config(api_key="chp_test_key"))
        try:
            client.update_event("evt_123", {"title": "Updated"})
            call_kwargs = self.mock_requests.put.call_args.kwargs
            self.assertEqual(
                call_kwargs["headers"]["Authorization"], "Bearer chp_test_key"
            )
        finally:
            client.shutdown()

    def test_list_alerts_uses_query_params(self):
        client = Client(Config(api_key="chp_test_key"))
        try:
            client.list_alerts("triggered")
            call_kwargs = self.mock_requests.get.call_args.kwargs
            self.assertEqual(call_kwargs["params"], {"status": "triggered"})
        finally:
            client.shutdown()

    def test_create_policy_posts_to_servicer(self):
        client = Client(Config(api_key="chp_test_key"))
        try:
            client.create_policy(
                {
                    "event_id": "evt_1",
                    "title": "Policy",
                    "condition": "gt",
                    "threshold": 1,
                }
            )
            call_args = self.mock_requests.post.call_args.args
            self.assertEqual(call_args[0], "https://api.chirpier.co/v1.0/policies")
        finally:
            client.shutdown()

    def test_get_event_logs_uses_period_and_limit(self):
        client = Client(Config(api_key="chp_test_key"))
        try:
            client.get_event_logs("evt_123", period="day", limit=10, offset=5)
            call_kwargs = self.mock_requests.get.call_args.kwargs
            self.assertEqual(
                call_kwargs["params"], {"period": "day", "limit": 10, "offset": 5}
            )
        finally:
            client.shutdown()

    def test_get_alert_deliveries_uses_pagination(self):
        client = Client(Config(api_key="chp_test_key"))
        try:
            client.get_alert_deliveries("alrt_123", limit=20, offset=10, kind="test")
            call_kwargs = self.mock_requests.get.call_args.kwargs
            self.assertEqual(
                call_kwargs["params"], {"kind": "test", "limit": 20, "offset": 10}
            )
        finally:
            client.shutdown()

    def test_archive_alert_posts_to_servicer(self):
        client = Client(Config(api_key="chp_test_key"))
        try:
            client.archive_alert("alrt_123")
            call_args = self.mock_requests.post.call_args.args
            self.assertEqual(
                call_args[0], "https://api.chirpier.co/v1.0/alerts/alrt_123/archive"
            )
        finally:
            client.shutdown()

    def test_test_webhook_posts_to_servicer(self):
        client = Client(Config(api_key="chp_test_key"))
        try:
            client.test_webhook("whk_123")
            call_args = self.mock_requests.post.call_args.args
            self.assertEqual(
                call_args[0], "https://api.chirpier.co/v1.0/webhooks/whk_123/test"
            )
        finally:
            client.shutdown()


if __name__ == "__main__":
    unittest.main()
