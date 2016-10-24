FROM python:2.7

MAINTAINER Deshraj(deshraj@vt.edu)

# Basics
RUN sudo apt-get update
RUN apt-get install -y gfortran git wget unzip python-dev build-essential
RUN wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py && rm get-pip.py

RUN apt-get update && \
    apt-get install -y build-essential python-dev python-pip \ python-setuptools libxml2-dev libxslt1-dev zlib1g-dev

# Requirements for celery
RUN pip install celery redis
 
# Starting celery worker
ENV C_FORCE_ROOT TRUE

RUN pip install flower

EXPOSE 5555

WORKDIR /evalai

CMD ["celery","-A","celeryTasks","worker","--loglevel=debug", "--logfile=/evalai/celery.log"]