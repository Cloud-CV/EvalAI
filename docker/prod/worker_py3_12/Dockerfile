FROM python:3.12.3

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get --no-install-recommends install -q -y default-jre default-jdk \
    git cmake libeigen3-dev libboost-python-dev libopencv-dev python-opencv \
    libgmp-dev libcgal-qt5-dev swig && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /code
WORKDIR /code
ADD requirements/* /code/

RUN pip install -r prod.txt
RUN pip install -r worker_py3_12.txt

ADD . /code

CMD ["python", "-m", "scripts.workers.submission_worker"]
