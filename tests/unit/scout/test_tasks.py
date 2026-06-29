from unittest import mock

from django.test import TestCase
from django.test.utils import override_settings
from scout.dedup import canonical_key
from scout.models import ScoutChallenge

SENDGRID_TEMPLATES = {"OUTREACH_BENCHMARK_HOSTING": "tmpl-123"}


@override_settings(
    OUTREACH_FROM_EMAIL="EvalAI Team <team@eval.ai>",
    SENDGRID_SETTINGS={"TEMPLATES": SENDGRID_TEMPLATES},
)
class SendDailyOutreachTests(TestCase):
    def _seed(self, name, organizers, outreach_sent_at=None):
        c = ScoutChallenge.objects.create(
            benchmark_name=name,
            conference="NeurIPS",
            year=2025,
            canonical_key=canonical_key(
                {
                    "benchmark_name": name,
                    "conference": "NeurIPS",
                    "year": 2025,
                }
            ),
            official_url="https://x",
            organizers=organizers,
            evalai_suitable=True,
            evalai_reasoning="reason",
        )
        if outreach_sent_at is not None:
            ScoutChallenge.objects.filter(pk=c.pk).update(
                outreach_sent_at=outreach_sent_at
            )
            c.refresh_from_db()
        return c

    @mock.patch("scout.tasks.send_email")
    def test_sends_one_email_per_organizer_on_pending_rows(self, mock_send):
        self._seed(
            "alpha",
            [
                {"name": "A", "email": "a@x.com"},
                {"name": "B", "email": "b@x.com"},
            ],
        )
        self._seed("beta", [{"name": "C", "email": "c@x.com"}])

        from scout.tasks import send_daily_outreach

        send_daily_outreach()

        self.assertEqual(mock_send.call_count, 3)
        recipients = sorted(
            call.kwargs["recipient"] for call in mock_send.call_args_list
        )
        self.assertEqual(recipients, ["a@x.com", "b@x.com", "c@x.com"])
        kwargs = mock_send.call_args_list[0].kwargs
        self.assertEqual(kwargs["sender"], "EvalAI Team <team@eval.ai>")
        self.assertEqual(kwargs["template_id"], "tmpl-123")
        self.assertIn("benchmark_name", kwargs["template_data"])

    @mock.patch("scout.tasks.send_email")
    def test_rows_are_marked_after_processing(self, mock_send):
        self._seed("alpha", [{"name": "A", "email": "a@x.com"}])

        from scout.tasks import send_daily_outreach

        send_daily_outreach()

        row = ScoutChallenge.objects.get(benchmark_name="alpha")
        self.assertIsNotNone(row.outreach_sent_at)

    @mock.patch("scout.tasks.send_email")
    def test_skips_already_sent_rows(self, mock_send):
        from django.utils import timezone

        self._seed(
            "old",
            [{"name": "Z", "email": "z@x.com"}],
            outreach_sent_at=timezone.now(),
        )
        self._seed("new", [{"name": "Y", "email": "y@x.com"}])

        from scout.tasks import send_daily_outreach

        send_daily_outreach()

        self.assertEqual(mock_send.call_count, 1)
        self.assertEqual(
            mock_send.call_args_list[0].kwargs["recipient"], "y@x.com"
        )

    @mock.patch("scout.tasks.send_email")
    def test_idempotent_when_no_pending_rows(self, mock_send):
        from scout.tasks import send_daily_outreach

        send_daily_outreach()
        self.assertEqual(mock_send.call_count, 0)

    @mock.patch("scout.tasks.send_email")
    def test_second_run_sends_nothing(self, mock_send):
        self._seed("alpha", [{"name": "A", "email": "a@x.com"}])

        from scout.tasks import send_daily_outreach

        send_daily_outreach()
        self.assertEqual(mock_send.call_count, 1)

        send_daily_outreach()
        self.assertEqual(mock_send.call_count, 1)

    @mock.patch("scout.tasks.send_email")
    def test_empty_organizers_row_is_marked_sent(self, mock_send):
        c = self._seed("empty", [])

        from scout.tasks import send_daily_outreach

        send_daily_outreach()

        self.assertEqual(mock_send.call_count, 0)
        c.refresh_from_db()
        self.assertIsNotNone(c.outreach_sent_at)

    @mock.patch("scout.tasks.send_email")
    def test_send_email_exception_does_not_stop_loop_and_row_is_marked(
        self, mock_send
    ):
        mock_send.side_effect = [Exception("first send blew up"), True]
        self._seed(
            "alpha",
            [
                {"name": "A", "email": "a@x.com"},
                {"name": "B", "email": "b@x.com"},
            ],
        )

        from scout.tasks import send_daily_outreach

        send_daily_outreach()

        self.assertEqual(mock_send.call_count, 2)
        row = ScoutChallenge.objects.get(benchmark_name="alpha")
        self.assertIsNotNone(row.outreach_sent_at)

    @mock.patch("scout.tasks.send_email")
    def test_row_is_not_marked_when_every_send_fails(self, mock_send):
        mock_send.side_effect = Exception("SES is down")
        self._seed(
            "alpha",
            [
                {"name": "A", "email": "a@x.com"},
                {"name": "B", "email": "b@x.com"},
            ],
        )

        from scout.tasks import send_daily_outreach

        send_daily_outreach()

        self.assertEqual(mock_send.call_count, 2)
        row = ScoutChallenge.objects.get(benchmark_name="alpha")
        self.assertIsNone(row.outreach_sent_at)

        mock_send.side_effect = None
        mock_send.return_value = True
        send_daily_outreach()
        self.assertEqual(mock_send.call_count, 4)
        row.refresh_from_db()
        self.assertIsNotNone(row.outreach_sent_at)

    @mock.patch("scout.tasks.send_email")
    def test_row_is_not_marked_when_send_email_returns_false(self, mock_send):
        # send_email swallows failures internally (bounce list, rate limit,
        # SES error) and returns False. Those rows must not be marked done.
        mock_send.return_value = False
        self._seed("alpha", [{"name": "A", "email": "a@x.com"}])

        from scout.tasks import send_daily_outreach

        send_daily_outreach()

        self.assertEqual(mock_send.call_count, 1)
        row = ScoutChallenge.objects.get(benchmark_name="alpha")
        self.assertIsNone(row.outreach_sent_at)
