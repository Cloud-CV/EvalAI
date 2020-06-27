import logging

from django.conf import settings

from base.utils import send_email
from challenges.aws_utils import create_eks_cluster, start_workers

logger = logging.getLogger(__name__)


def challenge_start_notifier(sender, instance, field_name, **kwargs):
    prev = getattr(instance, "_original_{}".format(field_name))
    curr = getattr(instance, "{}".format(field_name))
    if curr and not prev:  # Checking if the challenge has been approved by admin since last time.
        challenge = instance

        if challenge.is_docker_based:
            response = create_eks_cluster(challenge)
            if response is None:
                logger.warning("Could not create EKS cluster for docker based challenge {}!".format(challenge.id))
            else:
                construct_and_send_worker_start_mail(challenge)
        else:
            response = start_workers([challenge])
            count, failures = response["count"], response["failures"]
            if (count != 1):
                logger.warning("Worker for challenge {} couldn't start! Error: {}".format(challenge.id, failures[0]["message"]))
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