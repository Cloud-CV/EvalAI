FROM python:3.8.3

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD requirements/* /code/
RUN pip install -r prod.txt

ADD . /code

CMD ["sh", "/code/docker/prod/celery/container-start.sh"]
