import json

from django.test import Client, TestCase

from scout.models import Scout, ScoutChallenge, ScoutRun


SAMPLE_PAYLOAD = {
    "challenges": [
        {
            "benchmark_name": "ImageNet-21K-P",
            "task_area": "vision",
            "conference": "NeurIPS",
            "year": 2025,
            "official_url": "https://imagenet21k.org/challenge",
            "dataset_url": "https://imagenet21k.org/data",
            "organizers": [{"name": "Dr. Jane", "email": "jane@x.edu"}],
            "evalai_suitable": True,
            "evalai_reasoning": "Standardized leaderboard hosting would help.",
        },
        {
            "benchmark_name": "Foo-Bench",
            "task_area": "NLP",
            "conference": "ACL",
            "year": 2026,
            "official_url": "https://foo.example/bench",
            "dataset_url": "",
            "organizers": [{"name": "Dr. Bar", "email": "bar@x.edu"}],
            "evalai_suitable": True,
            "evalai_reasoning": "Reasonable fit.",
        },
    ]
}


def _make_scout(name="default", token="secret-token", scout_id=None):
    return Scout.objects.create(
        name=name,
        webhook_token=token,
        scout_id=scout_id or "uuid-{}".format(name),
        query_hash="dummy-hash",
        webhook_url="https://example.com/api/scout/webhook/{}/{}/".format(
            name, token
        ),
    )


class WebhookReceiverTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.scout = _make_scout()
        self.url = "/api/scout/webhook/{}/{}/".format(
            self.scout.name, self.scout.webhook_token
        )

    def _post(self, url, body):
        return self.client.post(
            url, data=json.dumps(body), content_type="application/json"
        )

    def test_valid_name_and_token_and_payload_creates_run_and_challenges(self):
        resp = self._post(self.url, SAMPLE_PAYLOAD)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ScoutRun.objects.count(), 1)
        self.assertEqual(ScoutChallenge.objects.count(), 2)
        run = ScoutRun.objects.first()
        self.assertEqual(run.scout_id, self.scout.id)
        self.assertEqual(run.new_challenge_count, 2)
        body = resp.json()
        self.assertEqual(body["received"], 2)
        self.assertEqual(body["new"], 2)
        self.assertEqual(body["run_id"], run.id)
        self.assertEqual(body["scout"], self.scout.name)

    def test_unknown_scout_name_returns_404(self):
        resp = self._post(
            "/api/scout/webhook/nope/{}/".format(self.scout.webhook_token),
            SAMPLE_PAYLOAD,
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(ScoutRun.objects.count(), 0)
        self.assertEqual(ScoutChallenge.objects.count(), 0)

    def test_invalid_token_returns_403(self):
        resp = self._post(
            "/api/scout/webhook/{}/wrong-token/".format(self.scout.name),
            SAMPLE_PAYLOAD,
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(ScoutRun.objects.count(), 0)
        self.assertEqual(ScoutChallenge.objects.count(), 0)

    def test_token_for_one_scout_does_not_work_on_another(self):
        other = _make_scout(name="other", token="other-token")
        resp = self._post(
            "/api/scout/webhook/{}/{}/".format(other.name, self.scout.webhook_token),
            SAMPLE_PAYLOAD,
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(ScoutRun.objects.count(), 0)
        self.assertEqual(ScoutChallenge.objects.count(), 0)

    def test_malformed_json_returns_400(self):
        resp = self.client.post(
            self.url, data="not-json", content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(ScoutRun.objects.count(), 0)
        self.assertEqual(ScoutChallenge.objects.count(), 0)

    def test_missing_challenges_key_persists_run_with_warning(self):
        resp = self._post(self.url, {"not_challenges": []})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ScoutRun.objects.count(), 1)
        self.assertEqual(ScoutChallenge.objects.count(), 0)
        run = ScoutRun.objects.first()
        self.assertEqual(run.new_challenge_count, 0)
        self.assertTrue(len(run.parse_warnings) > 0)

    def test_bad_challenge_entry_is_skipped_and_warned(self):
        payload = {
            "challenges": [
                SAMPLE_PAYLOAD["challenges"][0],
                {"benchmark_name": "missing-fields"},
            ]
        }
        resp = self._post(self.url, payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ScoutChallenge.objects.count(), 1)
        run = ScoutRun.objects.first()
        self.assertEqual(run.new_challenge_count, 1)
        self.assertEqual(len(run.parse_warnings), 1)

    def test_duplicate_delivery_does_not_create_duplicate_challenges(self):
        self._post(self.url, SAMPLE_PAYLOAD)
        self._post(self.url, SAMPLE_PAYLOAD)
        self.assertEqual(ScoutRun.objects.count(), 2)
        self.assertEqual(ScoutChallenge.objects.count(), 2)
        second_run = ScoutRun.objects.order_by("-received_at").first()
        self.assertEqual(second_run.new_challenge_count, 0)

    def test_same_challenge_to_two_scouts_dedupes_globally(self):
        other = _make_scout(name="other", token="other-token")
        other_url = "/api/scout/webhook/{}/{}/".format(other.name, other.webhook_token)
        self._post(self.url, SAMPLE_PAYLOAD)
        self._post(other_url, SAMPLE_PAYLOAD)
        self.assertEqual(ScoutRun.objects.count(), 2)
        self.assertEqual(ScoutChallenge.objects.count(), 2)
        scout_ids = sorted(r.scout_id for r in ScoutRun.objects.all())
        self.assertEqual(scout_ids, sorted([self.scout.id, other.id]))
        second_run = ScoutRun.objects.order_by("-received_at").first()
        self.assertEqual(second_run.new_challenge_count, 0)
