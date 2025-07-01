import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from jobs.models import Submission

from .aws_utils import (
    calculate_submission_retention_date,
    update_submission_retention_dates,
)
from .models import ChallengePhase

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ChallengePhase)
def store_original_challenge_phase_values(sender, instance, **kwargs):
    """Store original values to detect changes in challenge phase"""
    if instance.pk:
        try:
            original = ChallengePhase.objects.get(pk=instance.pk)
            instance._original_end_date = original.end_date
            instance._original_is_public = original.is_public
        except ChallengePhase.DoesNotExist:
            instance._original_end_date = None
            instance._original_is_public = None
    else:
        instance._original_end_date = None
        instance._original_is_public = None


@receiver(post_save, sender=ChallengePhase)
def update_submission_retention_on_phase_change(
    sender, instance, created, **kwargs
):
    """
    Update submission retention dates when challenge phase end_date or is_public changes.
    This ensures retention policies are automatically updated when challenges end or
    become non-public.
    """
    if created:
        # For new phases, set retention dates if applicable
        retention_date = calculate_submission_retention_date(instance)
        if retention_date:
            # Update existing submissions for this phase
            submissions_updated = Submission.objects.filter(
                challenge_phase=instance,
                retention_eligible_date__isnull=True,
                is_artifact_deleted=False,
            ).update(retention_eligible_date=retention_date)

            if submissions_updated > 0:
                logger.info(
                    f"Set retention date {retention_date} for {submissions_updated} "
                    f"submissions in new phase {instance.pk}"
                )
        return

    # Check if relevant fields changed
    end_date_changed = (
        hasattr(instance, "_original_end_date")
        and instance._original_end_date != instance.end_date
    )

    is_public_changed = (
        hasattr(instance, "_original_is_public")
        and instance._original_is_public != instance.is_public
    )

    if end_date_changed or is_public_changed:
        logger.info(
            f"Challenge phase {instance.pk} changed - end_date: {end_date_changed}, "
            f"is_public: {is_public_changed}. Updating submission retention dates."
        )

        # Calculate new retention date
        retention_date = calculate_submission_retention_date(instance)

        if retention_date:
            # Update submissions for this phase
            submissions_updated = Submission.objects.filter(
                challenge_phase=instance, is_artifact_deleted=False
            ).update(retention_eligible_date=retention_date)

            logger.info(
                f"Updated retention date to {retention_date} for {submissions_updated} "
                f"submissions in phase {instance.pk}"
            )
        else:
            # Clear retention dates if phase is now public or has no end date
            submissions_updated = Submission.objects.filter(
                challenge_phase=instance, is_artifact_deleted=False
            ).update(retention_eligible_date=None)

            if submissions_updated > 0:
                logger.info(
                    f"Cleared retention dates for {submissions_updated} "
                    f"submissions in phase {instance.pk} (phase is now public or has no end date)"
                )


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
