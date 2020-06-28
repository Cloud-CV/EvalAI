import logging

from django.conf import settings

from base.utils import send_email
from challenges.aws_utils import start_workers

logger = logging.getLogger(__name__)


def challenge_workers_start_notifier(sender, instance, field_name, **kwargs):
    prev = getattr(instance, "_original_{}".format(field_name))
    curr = getattr(instance, "{}".format(field_name))
    challenge = instance

    if curr and not prev:
        if challenge.is_docker_based:
            construct_and_send_worker_start_mail(challenge)
        else:  # Checking if the challenge has been approved by admin since last time.
            response = start_workers([challenge])
            count, failures = response["count"], response["failures"]
            if (count != 1):
                logger.error("Worker for challenge {} couldn't start! Error: {}".format(challenge.id, failures[0]["message"]))
            else:
                construct_and_send_worker_start_mail(challenge)


def construct_and_send_worker_start_mail(challenge):
    challenge_url = "https://{}/web/challenges/challenge-page/{}".format(settings.HOSTNAME, challenge.id)

    template_data = {"CHALLENGE_NAME": challenge.title, "CHALLENGE_URL": challenge_url}
    if challenge.image:
        template_data["CHALLENGE_IMAGE_URL"] = challenge.image.url

    template_id = settings.SENDGRID_SETTINGS.get("TEMPLATES").get("CHALLENGE_APPROVAL_EMAIL")

    emails = challenge.creator.get_all_challenge_host_email()
    for email in emails:
        send_email(
            sender=settings.CLOUDCV_TEAM_EMAIL,
            recipient=email,
            template_id=template_id,
            template_data=template_data,
        )
