import logging

from base.utils import send_email
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from scout.outreach import build_template_data, pending_challenges

logger = logging.getLogger(__name__)


@shared_task
def send_daily_outreach():
    template_id = settings.SENDGRID_SETTINGS["TEMPLATES"].get(
        "OUTREACH_BENCHMARK_HOSTING"
    )
    sender = settings.OUTREACH_FROM_EMAIL

    sent = 0
    attempted = 0
    rows_processed = 0

    for challenge in pending_challenges().iterator():
        rows_processed += 1
        for organizer in challenge.organizers or []:
            email = (organizer.get("email") or "").strip()
            if not email:
                continue
            attempted += 1
            try:
                send_email(
                    sender=sender,
                    recipient=email,
                    template_id=template_id,
                    template_data=build_template_data(challenge, organizer),
                )
                sent += 1
            except Exception:
                logger.exception(
                    "scout outreach: send_email raised for recipient=%s",
                    email,
                )
        challenge.outreach_sent_at = timezone.now()
        challenge.save(update_fields=["outreach_sent_at"])

    logger.info(
        "scout outreach complete: rows=%d attempted=%d sent=%d",
        rows_processed,
        attempted,
        sent,
    )
