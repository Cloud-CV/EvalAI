FROM rabbitmq
MAINTAINER CloudCV

RUN apt-get update && apt-get install -y python

RUN mkdir /code
ADD . /code
WORKDIR /code

ENTRYPOINT ["python", "scripts/workers/submission_worker.py"]
