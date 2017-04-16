FROM rabbitmq
MAINTAINER varunagrawal

RUN mkdir /code
ADD . /code
WORKDIR /code

ENTRYPOINT ["python", "scripts/workers/submission_worker.py"]