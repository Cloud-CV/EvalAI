import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def construct_and_send_worker_start_mail(challenge):
    if settings.DEBUG:
        return
    logger.info(
        "Challenge %s approved — skipping email (emails disabled).",
        challenge.pk,
    )


def construct_and_send_eks_cluster_creation_mail(challenge):
    if settings.DEBUG:
        return
    logger.info(
        "EKS cluster created for challenge %s — skipping email (emails disabled).",
        challenge.pk,
    )
