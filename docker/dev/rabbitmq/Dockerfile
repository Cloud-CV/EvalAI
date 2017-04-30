FROM rabbitmq
MAINTAINER CloudCV

RUN apt-get update && apt-get install -y python python-pip python-dev libpq-dev libjpeg-dev

RUN mkdir /code
ADD . /code
WORKDIR /code

RUN pip install -r requirements/common.txt

ENTRYPOINT ["python", "scripts/workers/submission_worker.py"]
