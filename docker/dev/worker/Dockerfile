FROM python:3.4
MAINTAINER CloudCV

ENV PYTHONUNBUFFERED 1

ADD . /code

WORKDIR /code

ADD requirements/* /code/

RUN pip install -U cffi service_identity
RUN pip install -r dev.txt

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "scripts/workers/submission_worker.py" ]
