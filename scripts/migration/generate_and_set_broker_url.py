# Command to run: python manage.py shell < scripts/migration/generate_and_set_broker_url.py

import traceback
import uuid

from challenges.models import Challenge

challenges = Challenge.objects.filter(approved_by_admin=True)

try:
    for challenge in challenges:
        challenge_title = challenge.title.split(' ')
        challenge_title = '-'.join(challenge_title).lower()
        random_challenge_id = uuid.uuid4() 
        challenge_queue_name = "{}-{}".format(challenge_title, random_challenge_id)
        challenge.broker_url = challenge_queue_name
        challenge.save()
except Exception as e:
    print(e)
    print(traceback.print_exc())
