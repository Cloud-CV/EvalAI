import datetime
import logging

from .aws_utils import restart_workers
from .models import Challenge

logger = logging.getLogger(__name__)


def restart_workers_cron_checker:
    challenges = [c for c in Challenge.objects if c.three_days_since_last_start]
    response = restart_workers(challenges)
    count, failures = response["count"], response["failures"]

    if(count == challenges.count()):
        logger.info("All challenge workers restarted succesfully.")
    else:
        for fail in failures:
            logger.warning("Worker restart for challenge {} failed. Error: {}".format(fail["challenge_pk"], fail["message"]))


'''
def restart_workers_cron_checker:
    today = datetime.date.today()
    challenges = Challenge.objects.filter(is_active=True)
    for challenge in challenges: # This might be a bit inefficient due to function call overhead for each challenge. Gotta use custom managers.
        if challenge.is_active:
            delta = challenge.last_started_at - today
            if(delta.days == 3):
                response = restart_workers([challenge])
                count, failures = response["count"], response["failures"]

                if count == 1:
                    logger.info("Worker(s) for challenge {} restarted succesfully.".format(challenge.id))
                else:
                    logger.warning("Worker restart for challenge {} failed. Error: {}".format(challenge.id, failures[0]["message"]))
'''
