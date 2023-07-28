FROM python:3.7.5

ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/

RUN pip install -r dev.txt

CMD ["sh", "/code/docker/prod/celery/container-start.sh"]
