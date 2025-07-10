import logging

from challenges.aws_utils import calculate_submission_retention_date
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Submission

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Submission)
def set_initial_retention_date(sender, instance, created, **kwargs):
    """
    Set initial retention date for new submissions based on their challenge phase.
    """
    if created and not instance.retention_eligible_date:
        retention_date = calculate_submission_retention_date(
            instance.challenge_phase
        )
        if retention_date:
            instance.retention_eligible_date = retention_date
            instance.save(update_fields=["retention_eligible_date"])
            logger.debug(
                f"Set initial retention date {retention_date} for new submission {instance.pk}"
            ) 