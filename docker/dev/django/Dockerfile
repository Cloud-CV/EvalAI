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

WORKDIR /code

ADD ./ /code/

RUN pip install -r requirements/dev.txt

ENV POSTGRES_NAME="postgres"
ENV POSTGRES_USER="postgres"
ENV POSTGRES_PASSWORD="postgres"
ENV POSTGRES_HOST="db"
ENV POSTGRES_PORT=5432

CMD ["sh", "/code/docker/dev/django/container-start.sh"]
EXPOSE 8000
