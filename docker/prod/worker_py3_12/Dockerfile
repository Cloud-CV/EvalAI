FROM python:3.12.3

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -q -y --no-install-recommends \
    default-jre \
    default-jdk \
    git \
    cmake \
    libeigen3-dev \
    libboost-python-dev \
    libopencv-dev \
    python-opencv \
    libgmp-dev \
    libcgal-qt5-dev \
    swig \
    libpq-dev \
    libcurl4-openssl-dev \
    build-essential \
    python3-dev \
    curl && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /code
WORKDIR /code
ADD requirements/* /code/

RUN pip install --only-binary=:all: -r common.txt
RUN pip install --only-binary=:all: -r worker_py3_12.txt

ADD . /code

CMD ["python", "-m", "scripts.workers.submission_worker"]
