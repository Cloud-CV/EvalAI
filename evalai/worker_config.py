from django.conf import settings


if settings.DEBUG:
    import dramatiq  # noqa
    from evalai.dramatiq_conf import broker  # noqa
else:
    from evalai.celery import app  # noqa


def task_wrapper(fn, *args, **kwargs):
    def inner(fn):
        if settings.DEBUG:
            dramatiq.set_broker(broker)
            res = dramatiq.actor(fn, *args, **kwargs)
            res.action = res.send
        else:
            res = app.task(fn, *args, **kwargs)
            res.action = res.delay

        return res
    return inner(fn)
