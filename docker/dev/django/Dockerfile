FROM python:3.9.21

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/
RUN pip install --no-cache-dir --progress-bar off -r dev.txt --no-compile

CMD ["./docker/wait-for-it.sh", "db:5432", "--", "sh", "/code/docker/dev/django/container-start.sh"]
