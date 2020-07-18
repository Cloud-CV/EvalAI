import logging

from django.conf import settings

from base.utils import send_email

logger = logging.getLogger(__name__)


def construct_and_send_worker_start_mail(challenge):
    if settings.DEBUG:
        return

    challenge_url = "https://{}/web/challenges/challenge-page/{}".format(
        settings.HOSTNAME, challenge.pk
    )

    template_data = {
        "CHALLENGE_NAME": challenge.title,
        "CHALLENGE_URL": challenge_url,
    }
    if challenge.image:
        template_data["CHALLENGE_IMAGE_URL"] = challenge.image.url

    template_id = settings.SENDGRID_SETTINGS.get("TEMPLATES").get(
        "CHALLENGE_APPROVAL_EMAIL"
    )

    emails = challenge.creator.get_all_challenge_host_email()
    for email in emails:
        send_email(
            sender=settings.CLOUDCV_TEAM_EMAIL,
            recipient=email,
            template_id=template_id,
            template_data=template_data,
        )
