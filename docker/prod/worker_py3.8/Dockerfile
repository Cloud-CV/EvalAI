ARG AWS_ACCOUNT_ID
ARG COMMIT_ID
ARG TRAVIS_BRANCH

FROM python:3.8

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD requirements/* /code/
RUN pip install -r prod.txt

ADD . /code

RUN apt-get update && \
  apt-get --no-install-recommends install -q -y default-jre default-jdk \
  git cmake libeigen3-dev libboost-python-dev libopencv-dev python-opencv \
  libgmp-dev libcgal-qt5-dev swig && \
  rm -rf /var/lib/apt/lists/*

RUN pip install -U cffi service_identity cython==0.29 numpy==1.18.1
RUN pip install -r worker.txt

CMD ["python", "-m", "scripts.workers.submission_worker"]
