FROM python:3.6.5

ENV PYTHONUNBUFFERED 1

ADD . /code

WORKDIR /code

ADD requirements/* /code/

RUN pip install -U cffi service_identity
RUN pip install -r dev.txt
RUN pip install -r worker.txt

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "-m", "scripts.workers.submission_worker"]
