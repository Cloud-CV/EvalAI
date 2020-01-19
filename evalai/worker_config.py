from django.conf import settings


def task_wrapper(fn, *args, **kwargs):
    def inner(fn):
        if settings.DEBUG:
            import dramatiq  # noqa
            from evalai.dramatiq import broker  # noqa
            dramatiq.set_broker(broker)
            res = dramatiq.actor(fn, *args, **kwargs)
            res.action = res.send
        else:
            from evalai.celery import app  # noqa
            res = app.task(fn, *args, **kwargs)
            res.action = res.delay

        return res
    return inner(fn)
