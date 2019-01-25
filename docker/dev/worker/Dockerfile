<<<<<<< HEAD
FROM python:2.7

ENV PYTHONUNBUFFERED 1

=======
FROM python:3.6.5

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
  apt-get upgrade -y && \
  apt-get install -q -y openjdk-8-jdk

>>>>>>> 98065e3257db0cd629bc64b959a29bae519b0bfe
RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/

<<<<<<< HEAD
RUN pip install -U cffi service_identity
RUN pip install -r dev.txt

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "scripts/workers/submission_worker.py" ]
=======
RUN pip install -U cffi service_identity cython==0.29 numpy==1.14.5
RUN pip install -r dev.txt
RUN pip install -r worker.txt

ADD . /code

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "-m", "scripts.workers.submission_worker"]
>>>>>>> 98065e3257db0cd629bc64b959a29bae519b0bfe
