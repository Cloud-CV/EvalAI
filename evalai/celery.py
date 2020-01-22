import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

app = Celery(broker=settings.CELERY_BROKER_URL)
app.conf.task_default_queue = os.environ.get('CELERY_QUEUE_NAME')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if __name__ == '__main__':
    app.start()
