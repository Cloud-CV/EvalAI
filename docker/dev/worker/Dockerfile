FROM python:2.7

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/

RUN pip install -U cffi service_identity
RUN pip install -r dev.txt

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "scripts/workers/submission_worker.py" ]
