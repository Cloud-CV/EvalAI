FROM python:3.7.5

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/

RUN pip install -r dev.txt

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "sh", "/code/docker/dev/celery/container-start.sh"]
