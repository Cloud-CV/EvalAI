FROM evalai/evalai-aws-backend:latest

RUN apt-get update && \
  apt-get install -q -y default-jre default-jdk

RUN yes Y | apt-get install git cmake \
  libeigen3-dev libboost-python-dev libopencv-dev python-opencv \
  libgmp-dev libcgal-qt5-dev swig

RUN pip install -U cffi service_identity cython==0.29 numpy==1.18.1
RUN pip install -r worker.txt

ADD . /code

CMD ["python", "-m", "scripts.workers.submission_worker"]