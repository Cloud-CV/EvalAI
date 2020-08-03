FROM python:3.6.5

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/

RUN pip install -r code_upload_worker.txt

ADD . /code

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "-m", "scripts.workers.code_upload_submission_worker"]
