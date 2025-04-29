from challenges.admin import ChallengeFilter
from challenges.models import Challenge
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHostTeam


class ChallengeFilterTest(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username="testuser", password="12345"
        )

        # Create a challenge host team
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        # Create test data
        self.past_challenge = Challenge.objects.create(
            title="Past Challenge",
            start_date=timezone.now() - timezone.timedelta(days=10),
            end_date=timezone.now() - timezone.timedelta(days=5),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )
        self.present_challenge = Challenge.objects.create(
            title="Present Challenge",
            start_date=timezone.now() - timezone.timedelta(days=5),
            end_date=timezone.now() + timezone.timedelta(days=5),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )
        self.future_challenge = Challenge.objects.create(
            title="Future Challenge",
            start_date=timezone.now() + timezone.timedelta(days=5),
            end_date=timezone.now() + timezone.timedelta(days=10),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )

    def test_past_challenge_filter(self):
        request = None  # Mock request if needed
        filter_instance = ChallengeFilter(
            request, {}, Challenge, Challenge.objects.all()
        )
        filter_instance.value = lambda: "past"
        queryset = filter_instance.queryset(request, Challenge.objects.all())
        self.assertIn(self.past_challenge, queryset)
        self.assertNotIn(self.present_challenge, queryset)
        self.assertNotIn(self.future_challenge, queryset)

    def test_present_challenge_filter(self):
        request = None  # Mock request if needed
        filter_instance = ChallengeFilter(
            request, {}, Challenge, Challenge.objects.all()
        )
        filter_instance.value = lambda: "present"
        queryset = filter_instance.queryset(request, Challenge.objects.all())
        self.assertNotIn(self.past_challenge, queryset)
        self.assertIn(self.present_challenge, queryset)
        self.assertNotIn(self.future_challenge, queryset)

    def test_future_challenge_filter(self):
        request = None  # Mock request if needed
        filter_instance = ChallengeFilter(
            request, {}, Challenge, Challenge.objects.all()
        )
        filter_instance.value = lambda: "future"
        queryset = filter_instance.queryset(request, Challenge.objects.all())
        self.assertNotIn(self.past_challenge, queryset)
        self.assertNotIn(self.present_challenge, queryset)
        self.assertIn(self.future_challenge, queryset)
