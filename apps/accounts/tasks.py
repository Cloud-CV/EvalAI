import logging
from datetime import timedelta

from django.utils import timezone

from evalai.celery import app

logger = logging.getLogger(__name__)

BOUNCE_GRACE_PERIOD = timedelta(hours=24)


@app.task
def deactivate_stale_bounced_accounts():
    """Deactivate accounts that have had email_bounced=True for over 24 hours
    without the user verifying a new email address."""
    from accounts.models import Profile
    from accounts.serializers import UserDeactivateSerializer

    cutoff = timezone.now() - BOUNCE_GRACE_PERIOD
    stale_profiles = Profile.objects.filter(
        email_bounced=True,
        email_bounced_at__lte=cutoff,
        user__is_active=True,
    ).select_related("user")

    count = 0
    for profile in stale_profiles:
        serializer = UserDeactivateSerializer(profile.user)
        serializer.deactivate()
        count += 1
        logger.warning(
            "Auto-deactivated user %s (%s) — email bounced at %s, "
            "grace period expired.",
            profile.user.username,
            profile.user.email,
            profile.email_bounced_at,
        )

    if count:
        logger.info(
            "deactivate_stale_bounced_accounts: deactivated %d account(s).",
            count,
        )
    return count
