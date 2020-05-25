import logging

from .aws_utils import restart_workers
from .models import Challenge

logger = logging.getLogger(__name__)


def restart_workers_cron_checker():
    challenges = [c for c in Challenge.objects if c.n_days_since_last_worker_start(3)]  # Restarting workers if last started/restarted 3 days ago.
    response = restart_workers(challenges)
    count, failures = response["count"], response["failures"]

    if(count == challenges.count()):
        logger.info("All challenge workers restarted succesfully.")
    else:
        for fail in failures:
            logger.warning("Worker restart for challenge {} failed. Error: {}".format(fail["challenge_pk"], fail["message"]))
