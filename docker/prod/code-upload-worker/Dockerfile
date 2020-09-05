FROM python:3.6.5

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

RUN apt-get update && apt-get install unzip

ADD requirements/* /code/

RUN pip install -r code_upload_worker.txt

ADD . /code

RUN chmod +x scripts/workers/code_upload_worker_utils/deploy_calico.sh

CMD ["scripts/workers/code_upload_worker_utils/deploy_calico.sh"]
