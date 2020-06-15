# Command to run: python manage.py shell < scripts/migration/generate_and_set_broker_url.py
# TODO: Run the code using a function based approach

import traceback
import uuid

from challenges.models import Challenge

challenges = Challenge.objects.all()

try:
    for challenge in challenges:
        challenge_title = challenge.title.split(" ")
        challenge_pk = challenge.pk
        challenge_title = "-".join(challenge_title).lower()
        random_challenge_id = uuid.uuid4()
        challenge_queue_name = "{}-{}-{}".format(
            challenge_title, challenge_pk, random_challenge_id
        )[:75]
        challenge.queue = challenge_queue_name
        challenge.save()
except Exception as e:
    print(e)
    print(traceback.print_exc())
