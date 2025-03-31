FROM python:3.7.5

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
  apt-get --no-install-recommends install -q -y default-jre default-jdk \
  git cmake libeigen3-dev libboost-python-dev libopencv-dev python-opencv \
  libgmp-dev libcgal-qt5-dev swig && \
  rm -rf /var/lib/apt/lists/*

RUN mkdir /code
WORKDIR /code
ADD requirements/* /code/

RUN pip install -U cffi service_identity cython==0.29 numpy==1.18.1
RUN pip install -r prod.txt
RUN pip install -r worker.txt

ADD . /code

CMD ["python", "-m", "scripts.workers.submission_worker"]
