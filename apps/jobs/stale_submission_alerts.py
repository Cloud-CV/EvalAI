import logging
from datetime import timedelta

from base.utils import send_email
from challenges.models import Challenge
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Min
from django.utils import timezone

from .models import Submission

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "remote_stuck_submission_alert:"


def get_stale_remote_submission_threshold():
    minutes = getattr(
        settings, "REMOTE_STUCK_SUBMISSION_THRESHOLD_MINUTES", 120
    )
    return timedelta(minutes=minutes)


def get_alert_cooldown():
    hours = getattr(settings, "REMOTE_STUCK_SUBMISSION_ALERT_COOLDOWN_HOURS", 6)
    return timedelta(hours=hours)


def cache_key_for_challenge(challenge_pk):
    return "{}{}".format(CACHE_KEY_PREFIX, challenge_pk)


def is_challenge_in_cooldown(challenge_pk):
    return cache.get(cache_key_for_challenge(challenge_pk)) is not None


def mark_challenge_alerted(challenge_pk):
    cooldown = get_alert_cooldown()
    cache.set(
        cache_key_for_challenge(challenge_pk),
        timezone.now().isoformat(),
        timeout=int(cooldown.total_seconds()),
    )


def _active_remote_challenge_filters(now):
    return {
        "challenge_phase__challenge__remote_evaluation": True,
        "challenge_phase__challenge__inform_hosts": True,
        "challenge_phase__challenge__published": True,
        "challenge_phase__challenge__is_submission_paused": False,
        "challenge_phase__challenge__start_date__lt": now,
        "challenge_phase__challenge__end_date__gt": now,
        "challenge_phase__is_submission_paused": False,
    }


def find_challenges_with_stale_remote_submissions():
    now = timezone.now()
    threshold = now - get_stale_remote_submission_threshold()
    stale_qs = (
        Submission.objects.filter(
            status=Submission.SUBMITTED,
            ignore_submission=False,
            submitted_at__lt=threshold,
            **_active_remote_challenge_filters(now),
        )
        .values("challenge_phase__challenge_id")
        .annotate(
            stale_count=Count("id"),
            oldest_submitted_at=Min("submitted_at"),
        )
    )
    return list(stale_qs)


def get_stale_submissions_for_challenge(challenge_pk):
    now = timezone.now()
    threshold = now - get_stale_remote_submission_threshold()
    return (
        Submission.objects.filter(
            status=Submission.SUBMITTED,
            ignore_submission=False,
            submitted_at__lt=threshold,
            challenge_phase__challenge_id=challenge_pk,
            **_active_remote_challenge_filters(now),
        )
        .select_related(
            "participant_team",
            "challenge_phase",
            "challenge_phase__challenge",
        )
        .order_by("submitted_at")[:50]
    )


def build_template_data(challenge, submissions):
    challenge_url = "{}/web/challenges/challenge-page/{}".format(
        settings.EVALAI_API_SERVER, challenge.pk
    )
    challenge_manage_url = (
        "{}/web/challenges/challenge-page/{}/manage".format(
            settings.EVALAI_API_SERVER, challenge.pk
        )
    )
    now = timezone.now()
    stuck_rows = []
    for submission in submissions:
        age = now - submission.submitted_at
        total_minutes = int(age.total_seconds() // 60)
        stuck_rows.append(
            {
                "SUBMISSION_PK": submission.pk,
                "TEAM_NAME": submission.participant_team.team_name,
                "PHASE_NAME": submission.challenge_phase.name,
                "SUBMITTED_AT": submission.submitted_at.isoformat(),
                "AGE_MINUTES": total_minutes,
            }
        )
    return {
        "CHALLENGE_NAME": challenge.title,
        "CHALLENGE_URL": challenge_url,
        "CHALLENGE_MANAGE_URL": challenge_manage_url,
        "HOST_TEAM_NAME": challenge.creator.team_name,
        "STUCK_COUNT": len(stuck_rows),
        "STUCK_SUBMISSIONS": stuck_rows,
        "THRESHOLD_MINUTES": int(
            get_stale_remote_submission_threshold().total_seconds() // 60
        ),
    }


def notify_remote_challenge_hosts_of_stale_submissions():
    """
    Email challenge hosts when remote-evaluation submissions remain in
    ``submitted`` longer than the configured threshold.
    """
    if settings.DEBUG:
        logger.info(
            "Skipping remote stuck submission host alerts in DEBUG mode."
        )
        return {
            "challenges_notified": 0,
            "emails_sent": 0,
            "skipped_cooldown": 0,
        }

    template_id = settings.SENDGRID_SETTINGS.get("TEMPLATES", {}).get(
        "STUCK_REMOTE_SUBMISSIONS_EMAIL"
    )
    if not template_id:
        logger.warning(
            "STUCK_REMOTE_SUBMISSIONS_EMAIL is not configured; skipping "
            "remote stuck submission alerts."
        )
        return {
            "challenges_notified": 0,
            "emails_sent": 0,
            "skipped_cooldown": 0,
        }

    challenges_notified = 0
    emails_sent = 0
    skipped_cooldown = 0

    for row in find_challenges_with_stale_remote_submissions():
        challenge_pk = row["challenge_phase__challenge_id"]
        if is_challenge_in_cooldown(challenge_pk):
            skipped_cooldown += 1
            continue

        try:
            challenge = Challenge.objects.get(pk=challenge_pk)
        except Challenge.DoesNotExist:
            continue

        submissions = list(get_stale_submissions_for_challenge(challenge_pk))
        if not submissions:
            continue

        host_emails = challenge.creator.get_all_challenge_host_email()
        if not host_emails:
            logger.warning(
                "No challenge host emails for challenge_pk=%s; skipping "
                "stuck submission alert.",
                challenge_pk,
            )
            continue

        template_data = build_template_data(challenge, submissions)
        delivered_to_any_host = False
        for email in host_emails:
            if send_email(
                sender=settings.DEFAULT_FROM_EMAIL,
                recipient=email,
                template_id=template_id,
                template_data=template_data,
            ):
                emails_sent += 1
                delivered_to_any_host = True

        if delivered_to_any_host:
            mark_challenge_alerted(challenge_pk)
            challenges_notified += 1
            logger.info(
                "Remote stuck submission alert sent for challenge_pk=%s "
                "(%d stale submission(s)).",
                challenge_pk,
                len(submissions),
            )

    return {
        "challenges_notified": challenges_notified,
        "emails_sent": emails_sent,
        "skipped_cooldown": skipped_cooldown,
    }
