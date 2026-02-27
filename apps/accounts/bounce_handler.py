import logging

from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.utils import timezone
from django_ses.signals import bounce_received, complaint_received

from .serializers import EmailBounceSerializer, UserDeactivateSerializer

logger = logging.getLogger(__name__)


def _is_email_verified(email):
    return EmailAddress.objects.filter(
        email__iexact=email, verified=True
    ).exists()


def _handle_bad_email(email, reason):
    """Flag verified users (soft) or deactivate unverified users (hard)."""
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        logger.info("%s for unknown email %s, ignoring.", reason, email)
        return

    if _is_email_verified(email):
        serializer = EmailBounceSerializer(
            user.profile,
            data={
                "email_bounced": True,
                "email_bounced_at": timezone.now(),
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.warning(
            "%s for verified user %s (%s) — flagged email_bounced.",
            reason,
            user.username,
            email,
        )
    else:
        serializer = UserDeactivateSerializer(user)
        serializer.deactivate()
        logger.warning(
            "%s for unverified user %s (%s) — deactivated account.",
            reason,
            user.username,
            email,
        )


def handle_bounce(sender, mail_obj, bounce_obj, raw_message, **kwargs):
    bounce_type = bounce_obj.get("bounceType", "")
    bounced_recipients = bounce_obj.get("bouncedRecipients", [])

    for recipient in bounced_recipients:
        email = recipient.get("emailAddress", "").lower()
        if not email:
            continue

        if bounce_type == "Permanent":
            _handle_bad_email(email, "Permanent bounce")
        else:
            logger.info(
                "Transient bounce for %s (type=%s), no action taken.",
                email,
                bounce_type,
            )


def handle_complaint(sender, mail_obj, complaint_obj, raw_message, **kwargs):
    complained_recipients = complaint_obj.get("complainedRecipients", [])

    for recipient in complained_recipients:
        email = recipient.get("emailAddress", "").lower()
        if not email:
            continue
        _handle_bad_email(email, "Spam complaint")


def connect_signals():
    bounce_received.connect(handle_bounce)
    complaint_received.connect(handle_complaint)
