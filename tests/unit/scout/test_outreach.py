from unittest import TestCase

from django.test import TestCase as DjangoTestCase
from scout.models import ScoutChallenge
from scout.outreach import build_template_data, iter_pending_targets


class BuildTemplateDataTests(TestCase):
    def test_includes_all_required_keys(self):
        challenge = ScoutChallenge(
            benchmark_name="ImageNet-21K-P",
            conference="NeurIPS",
            year=2025,
            official_url="https://imagenet21k.org/challenge",
            evalai_reasoning="Standardized leaderboard hosting would help.",
            evalai_suitable=True,
        )
        organizer = {"name": "Dr. Jane Doe", "email": "jane@x.edu"}
        data = build_template_data(challenge, organizer)
        self.assertEqual(
            set(data.keys()),
            {
                "organizer_name",
                "benchmark_name",
                "conference",
                "year",
                "official_url",
                "evalai_pitch",
            },
        )
        self.assertEqual(data["organizer_name"], "Dr. Jane Doe")
        self.assertEqual(data["benchmark_name"], "ImageNet-21K-P")
        self.assertEqual(
            data["evalai_pitch"],
            "Standardized leaderboard hosting would help.",
        )

    def test_missing_organizer_name_falls_back_to_empty_string(self):
        challenge = ScoutChallenge(
            benchmark_name="x",
            conference="y",
            year=2025,
            official_url="https://x",
            evalai_reasoning="",
            evalai_suitable=False,
        )
        data = build_template_data(challenge, {"email": "x@y.com"})
        self.assertEqual(data["organizer_name"], "")


class IterPendingTargetsTests(DjangoTestCase):
    def _make(self, name, organizers, outreach_sent_at=None):
        c = ScoutChallenge.objects.create(
            benchmark_name=name,
            conference="NeurIPS",
            year=2025,
            canonical_key="{}|neurips|2025".format(name.lower()),
            official_url="https://x",
            organizers=organizers,
            evalai_suitable=True,
            evalai_reasoning="x",
        )
        if outreach_sent_at is not None:
            ScoutChallenge.objects.filter(pk=c.pk).update(
                outreach_sent_at=outreach_sent_at
            )
            c.refresh_from_db()
        return c

    def test_includes_only_challenges_with_null_outreach_sent_at(self):
        from django.utils import timezone

        self._make(
            "old",
            [{"name": "A", "email": "a@x.com"}],
            outreach_sent_at=timezone.now(),
        )
        self._make("new", [{"name": "B", "email": "b@x.com"}])
        pairs = list(iter_pending_targets())
        names = sorted(c.benchmark_name for c, _ in pairs)
        self.assertEqual(names, ["new"])

    def test_skips_organizers_with_missing_or_empty_email(self):
        self._make(
            "x",
            [
                {"name": "Has email", "email": "y@x.com"},
                {"name": "No email"},
                {"name": "Empty email", "email": ""},
                {"name": "Whitespace email", "email": "   "},
            ],
        )
        pairs = list(iter_pending_targets())
        emails = [org["email"] for _, org in pairs]
        self.assertEqual(emails, ["y@x.com"])

    def test_handles_challenge_with_empty_organizers_list(self):
        c = self._make("empty", [])
        pairs = list(iter_pending_targets())
        self.assertEqual(pairs, [])
        self.assertTrue(
            ScoutChallenge.objects.filter(
                pk=c.pk, outreach_sent_at__isnull=True
            ).exists()
        )
