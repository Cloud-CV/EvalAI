FROM python:3.4
MAINTAINER CloudCV
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y python python-pip python-dev libpq-dev libjpeg-dev libyaml-dev libffi-dev


ADD . /code
WORKDIR /code

RUN pip install -U cffi service_identity
RUN pip install -r requirements/dev.txt

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "scripts/workers/submission_worker.py" ]
