FROM rabbitmq
MAINTAINER CloudCV

RUN apt-get update && apt-get install -y python

RUN mkdir /code
ADD . /code
WORKDIR /code

RUN pip install -r requirements/dev.txt

ENTRYPOINT ["python", "scripts/workers/submission_worker.py"]
