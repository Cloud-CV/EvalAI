FROM python:2.7

MAINTAINER Deshraj (deshraj@vt.edu)

# basic requirements

RUN apt-get update && \
    apt-get install -y build-essential python-dev python-pip libxml2-dev libxslt1-dev zlib1g-dev

COPY ./requirements /evalai/requirements

ADD . /evalai/

WORKDIR /evalai

RUN apt-get update
RUN apt-get install -y build-essential g++ gcc gfortran wget python-dev git libjpeg-dev python-psycopg2 libpq-dev python-matplotlib
RUN wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py && rm get-pip.py

# Install app requirements
RUN pip install --no-cache-dir -r requirements/dev.txt
RUN pip install --no-cache-dir -r requirements/test.txt
RUN pip install --no-cache-dir -r requirements/prod.txt
