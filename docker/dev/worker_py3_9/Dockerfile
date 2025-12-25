FROM python:3.9.21-bullseye

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
ADD constraints.txt /code/

ADD requirements/* /code/

RUN pip install -c constraints.txt -r dev.txt
RUN pip install -c constraints.txt -r worker_py3_9.txt

ADD . /code

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "-m", "scripts.workers.submission_worker"]
