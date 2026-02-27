import logging

from django.contrib.auth.models import User
from django_ses.signals import bounce_received, complaint_received

logger = logging.getLogger(__name__)


def handle_bounce(sender, mail_obj, bounce_obj, raw_message, **kwargs):
    """
    Process SES bounce notifications delivered via SNS.

    On permanent (hard) bounces, removes the allauth EmailAddress and
    deactivates the user account so no further emails are attempted.
    """
    bounce_type = bounce_obj.get("bounceType", "")
    bounced_recipients = bounce_obj.get("bouncedRecipients", [])

    for recipient in bounced_recipients:
        email = recipient.get("emailAddress", "").lower()
        if not email:
            continue

        if bounce_type == "Permanent":
            logger.warning(
                "Permanent bounce for %s — deactivating account.",
                email,
            )
            User.objects.filter(email__iexact=email).update(is_active=False)
        else:
            logger.info(
                "Transient bounce for %s (type=%s), no action taken.",
                email,
                bounce_type,
            )


def handle_complaint(sender, mail_obj, complaint_obj, raw_message, **kwargs):
    """
    Process SES complaint notifications (user marked email as spam).
    Deactivates the account to stop all future emails.
    """
    complained_recipients = complaint_obj.get("complainedRecipients", [])

    for recipient in complained_recipients:
        email = recipient.get("emailAddress", "").lower()
        if not email:
            continue

        logger.warning("Spam complaint from %s — deactivating account.", email)
        User.objects.filter(email__iexact=email).update(is_active=False)


def connect_signals():
    bounce_received.connect(handle_bounce)
    complaint_received.connect(handle_complaint)
