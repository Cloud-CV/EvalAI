# Command to run: python manage.py shell < scripts/migration/set_challenge_slug_field.py
# TODO: Run the code using a function based approach

import traceback

from challenges.models import Challenge

challenges = Challenge.objects.all()

try:
    for challenge in challenges:
        challenge_title = challenge.title.split(' ')
        challenge_slug = '-'.join(challenge_title).lower()
        challenge.slug = challenge_slug
        challenge.save()
except Exception as e:
    print(e)
    print(traceback.print_exc())
