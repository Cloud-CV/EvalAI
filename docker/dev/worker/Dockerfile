FROM python:3.7.5

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
  apt-get install -q -y default-jre default-jdk && \
  rm -rf /var/lib/apt/lists/*

RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/

RUN pip install -U cffi service_identity cython==0.29 setuptools==57.5.0 && \
    pip install -r dev.txt && \
    pip install -r worker.txt

ADD . /code

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "-m", "scripts.workers.submission_worker"]
