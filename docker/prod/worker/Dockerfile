ARG AWS_ACCOUNT_ID
ARG COMMIT_ID
ARG TRAVIS_BRANCH

FROM ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/evalai-${TRAVIS_BRANCH}-backend:${COMMIT_ID}

RUN apt-get update && \
  apt-get --no-install-recommends install -q -y default-jre default-jdk \
  git cmake libeigen3-dev libboost-python-dev libopencv-dev python-opencv \
  libgmp-dev libcgal-qt5-dev swig && \
  rm -rf /var/lib/apt/lists/*

RUN pip install -U cffi service_identity cython==0.29 numpy==1.18.1
RUN pip install -r worker.txt

CMD ["python", "-m", "scripts.workers.submission_worker"]
