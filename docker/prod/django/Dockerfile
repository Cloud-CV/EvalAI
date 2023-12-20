FROM python:3.7.5

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD requirements/* /code/
RUN pip install --progress-bar off -r prod.txt

ADD . /code

CMD ["sh", "/code/docker/prod/django/container-start.sh"]
