import logging
import sendgrid

from challenges.aws_utils import start_workers

from django.conf import settings

from sendgrid.helpers.mail import Email, Mail, Personalization

logger = logging.getLogger(__name__)


def challenge_start_notifier(sender, instance, field_name, **kwargs):
    prev = getattr(instance, "_original_{}".format(field_name))
    curr = getattr(instance, "{}".format(field_name))
    if prev != curr:
        challenge = instance

        # Start the challenge worker.
        response = start_workers([challenge])
        count, failures = response["count"], response["failures"]

        if(count != 1):
            logger.warning("Worker for challenge {} couldn't start! Error: {}".format(challenge.id, failures[0]["message"]))
        else:
            url = "https://evalai.cloudcv.org/web/challenges/challenge-page/{}".format(challenge.id)
            template_data = {"title": challenge.title,"url":url} # Gotta modify the template_data dict according to what's in the template.
            if challenge.image:
                template_data["image"] = challenge.image.url
            template_id = settings.SENDGRID_SETTINGS.get("TEMPLATES").get("CHALLENGE_APPROVAL_NOTIFICATION") # Add value in settings->common.py
            emails = challenge_obj.creator.get_all_challenge_host_email()
            for email in emails:
                send_email(
                    sender=settings.CLOUDCV_TEAM_EMAIL,
                    recipient=email,
                    template_id=template_id,
                    template_data=template_data,
                )