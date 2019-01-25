FROM python:3.6.5

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD requirements/* /code/
RUN pip install -r prod.txt

ADD . /code

EXPOSE 8000

CMD ["sh", "/code/docker/prod/django/container-start.sh"]
