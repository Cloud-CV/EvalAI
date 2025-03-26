FROM python:3.9.21

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on

RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/ 
RUN pip install --no-cache-dir --progress-bar off -r dev.txt --no-compile

CMD ["./docker/wait-for-it.sh", "db:5432", "--", "sh", "/code/docker/dev/django/container-start.sh"]
