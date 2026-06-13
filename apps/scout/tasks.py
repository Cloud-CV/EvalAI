import hashlib
import logging

from base.utils import send_email
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from scout.outreach import build_template_data, pending_challenges

logger = logging.getLogger(__name__)


def _redact_email(email):
    # Stable, non-reversible identifier so we can correlate log lines for the
    # same recipient without writing the address (PII) into logs.
    digest = hashlib.sha256(email.encode("utf-8")).hexdigest()[:12]
    domain = email.rsplit("@", 1)[-1] if "@" in email else "?"
    return "sha256:{}@{}".format(digest, domain)


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
        row_attempted = 0
        row_sent = 0
        for organizer in challenge.organizers or []:
            email = (organizer.get("email") or "").strip()
            if not email:
                continue
            attempted += 1
            row_attempted += 1
            ok = False
            try:
                ok = send_email(
                    sender=sender,
                    recipient=email,
                    template_id=template_id,
                    template_data=build_template_data(challenge, organizer),
                )
            except Exception:
                logger.exception(
                    "scout outreach: send_email raised for recipient=%s",
                    _redact_email(email),
                )
            if ok:
                sent += 1
                row_sent += 1
            else:
                logger.warning(
                    "scout outreach: send_email did not confirm delivery for "
                    "recipient=%s; row will be retried on next run",
                    _redact_email(email),
                )
        # Mark the row done only if there was nothing to send, or at least one
        # send was confirmed delivered. If every attempted send failed (raised
        # or returned False), leave it unmarked so the next run retries
        # instead of silently dropping the outreach.
        if row_attempted == 0 or row_sent > 0:
            challenge.outreach_sent_at = timezone.now()
            challenge.save(update_fields=["outreach_sent_at"])

    logger.info(
        "scout outreach complete: rows=%d attempted=%d sent=%d",
        rows_processed,
        attempted,
        sent,
    )
