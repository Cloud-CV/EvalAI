FROM python:3.6.5

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y python python-pip python-dev libpq-dev libjpeg-dev libyaml-dev libffi-dev

RUN mkdir /code

RUN git clone https://github.com/Cloud-CV/EvalAI.git /code/

WORKDIR /code

RUN pip install -U cffi service_identity cython==0.29 numpy==1.14.5
RUN pip install -r requirements/dev.txt
RUN pip install -r requirements/worker.txt

ADD . /code

CMD ["python", "-m", "scripts.workers.submission_worker"]
