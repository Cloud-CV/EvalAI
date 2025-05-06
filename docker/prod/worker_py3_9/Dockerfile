FROM python:3.9.21

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
    python3-opencv \
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

RUN pip install -r prod.txt
RUN pip install -r worker_py3_9.txt

ADD . /code

CMD ["python", "-m", "scripts.workers.submission_worker"]
