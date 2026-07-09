import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

app = Celery(broker=settings.CELERY_BROKER_URL)
app.config_from_object("django.conf:settings")

celery_queue_name = os.environ.get("CELERY_QUEUE_NAME")
if settings.DEBUG:
    app.conf.task_default_queue = "celery_dev"
elif celery_queue_name:
    app.conf.task_default_queue = celery_queue_name

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if __name__ == "__main__":
    app.start()
