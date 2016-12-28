FROM python:2.7
ENV PYTHONUNBUFFERED 1

# For websockets
# ENV REDIS_HOST "redis"

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
ADD ./docker/web/evalai_supervisor.conf /etc/supervisor/conf.d/evalai.conf

RUN mkdir /code
WORKDIR /code
ADD ./ /code/
RUN pip install -r requirements/prod.txt


CMD ["sh", "/code/docker/web/container-start.sh"]
EXPOSE 8000
EXPOSE 8001