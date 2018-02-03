FROM python:2.7
MAINTAINER CloudCV
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

RUN mkdir /code

RUN git clone https://github.com/Cloud-CV/EvalAI.git /code/

WORKDIR /code

RUN cp /code/settings/dev.sample.py /code/settings/dev.py

RUN pip install -r requirements/dev.txt

CMD ["sh", "/code/docker/dev/django/container-start.sh"]

EXPOSE 8000
