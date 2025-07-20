FROM python:3.9.21-slim-bullseye

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -q -y \
    default-jre \
    default-jdk \
    libpq-dev \
    libcurl4-openssl-dev \
    build-essential \
    python3-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*


RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/

RUN pip install -r dev.txt
RUN pip install -r worker_py3_9.txt

ADD . /code

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "-m", "scripts.workers.submission_worker"]
