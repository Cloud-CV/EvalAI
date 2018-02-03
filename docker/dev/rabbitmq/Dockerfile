FROM python:2.7
MAINTAINER CloudCV
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y python python-pip python-dev libpq-dev libjpeg-dev libyaml-dev libffi-dev

RUN mkdir /code
ADD ./ /code/
WORKDIR /code

RUN ls

RUN pip install -U cffi service_identity

RUN pip install -r requirements/dev.txt

CMD ["python", "scripts/workers/submission_worker.py"]
