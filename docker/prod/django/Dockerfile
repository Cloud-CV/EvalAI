FROM python:2.7
MAINTAINER Deshraj
ENV PYTHONUNBUFFERED 1

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y

RUN apt-get install -y apt-utils

RUN groupadd webapps
RUN useradd evalai -G webapps
RUN mkdir -p /var/log/evalai/ && chown -R evalai /var/log/evalai/ && chmod -R u+rX /var/log/evalai/
RUN mkdir -p /var/run/evalai/ && chown -R evalai /var/run/evalai/ && chmod -R u+rX /var/run/evalai/

RUN apt-get install -y supervisor
RUN mkdir -p /var/log/supervisor

WORKDIR /code

ADD ./docker/prod/django/evalai_supervisor.conf /etc/supervisor/conf.d/evalai.conf
ADD ./ /code/
RUN pip install -r requirements/prod.txt

EXPOSE 8000
