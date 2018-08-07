import django
import docker
import os
import sys

from io import BytesIO
from os.path import dirname

from django.utils import timezone
from django.conf import settings

# need to add django project path in sys path
# root directory : where manage.py lives
# worker is present in root-directory/scripts/workers
# but make sure that this worker is run like `python scripts/workers/master_worker.py`
DJANGO_PROJECT_PATH = dirname(dirname(dirname(os.path.abspath(__file__))))

# default settings module will be `dev`, to override it pass
# as command line arguments
DJANGO_SETTINGS_MODULE = 'settings.dev'

sys.path.insert(0, DJANGO_PROJECT_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', DJANGO_SETTINGS_MODULE)
django.setup()

from challenges.models import Challenge


def load_active_challenges():
    '''
         * Fetches active challenges and corresponding active phases for it.
    '''
    q_params = {'approved_by_admin': True}
    q_params['start_date__lt'] = timezone.now()
    q_params['end_date__gt'] = timezone.now()


    active_challenges = Challenge.objects.filter(**q_params)

    for challenge in active_challenges:
    	print(challenge)


def main():
    client = docker.from_env()
    load_active_challenges()
    file = open("docker/dev/submission-worker/Dockerfile", "r+")
    dockerfile = file.read()
    f = BytesIO(dockerfile.encode('utf-8'))
    image = client.images.build(fileobj=f, rm=True, tag='test', nocache=True)

if __name__ == '__main__':
    main()
