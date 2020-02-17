FROM python:3.7.5

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
  apt-get upgrade -y && \
  apt-get install -q -y default-jre default-jdk

RUN yes Y | apt-get install git cmake python3-dev python3.7-venv \
  libeigen3-dev libboost-python-dev libopencv-dev python-opencv \
  libgmp-dev libcgal-qt5-dev swig

RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/

RUN pip install -U cffi service_identity cython==0.29
RUN pip install -r prod.txt
RUN pip install -r worker.txt

ADD . /code

CMD ["python", "-m", "scripts.workers.submission_worker"]
