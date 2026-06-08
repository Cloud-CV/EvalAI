import json
from unittest import TestCase

import responses

from scout.client import YutoriClient, YutoriAPIError


class YutoriClientTests(TestCase):
    @responses.activate
    def test_create_scout_posts_correct_request(self):
        responses.add(
            responses.POST,
            "https://api.yutori.com/v1/scouting/tasks",
            json={
                "id": "scout-uuid-123",
                "query": "test prompt",
                "view_url": "https://platform.yutori.com/scouts/scout-uuid-123",
            },
            status=200,
        )

        client = YutoriClient(api_key="test-key")
        result = client.create_scout(
            query="test prompt",
            output_schema={"type": "object"},
            webhook_url="https://example.com/api/scout/webhook/abc/",
            output_interval=86400,
        )

        self.assertEqual(result["id"], "scout-uuid-123")

        sent = responses.calls[0].request
        self.assertEqual(sent.headers["X-API-Key"], "test-key")
        body = json.loads(sent.body)
        self.assertEqual(body["query"], "test prompt")
        self.assertEqual(body["output_interval"], 86400)
        self.assertEqual(body["webhook_format"], "scout")
        self.assertTrue(body["skip_email"])
        self.assertEqual(
            body["webhook_url"],
            "https://example.com/api/scout/webhook/abc/",
        )
        self.assertEqual(body["output_schema"], {"type": "object"})

    @responses.activate
    def test_create_scout_raises_on_non_2xx(self):
        responses.add(
            responses.POST,
            "https://api.yutori.com/v1/scouting/tasks",
            json={"error": "bad request"},
            status=400,
        )
        client = YutoriClient(api_key="test-key")
        with self.assertRaises(YutoriAPIError):
            client.create_scout(
                query="x",
                output_schema={},
                webhook_url="https://x/",
            )

    @responses.activate
    def test_pause_scout_posts_to_pause_endpoint(self):
        responses.add(
            responses.POST,
            "https://api.yutori.com/v1/scouting/tasks/scout-uuid-123/pause",
            json={"id": "scout-uuid-123", "paused_at": "2026-06-06T10:00:00Z"},
            status=200,
        )
        client = YutoriClient(api_key="test-key")
        result = client.pause_scout("scout-uuid-123")
        self.assertEqual(result["id"], "scout-uuid-123")
        self.assertEqual(
            responses.calls[0].request.headers["X-API-Key"], "test-key"
        )

    @responses.activate
    def test_resume_scout_posts_to_resume_endpoint(self):
        responses.add(
            responses.POST,
            "https://api.yutori.com/v1/scouting/tasks/scout-uuid-123/resume",
            json={"id": "scout-uuid-123"},
            status=200,
        )
        client = YutoriClient(api_key="test-key")
        result = client.resume_scout("scout-uuid-123")
        self.assertEqual(result["id"], "scout-uuid-123")
