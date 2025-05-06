FROM python:3.9.21

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD requirements/* /code/
RUN pip install -r prod.txt
RUN pip install -r django.txt

ADD . /code

CMD ["sh", "/code/docker/prod/django/container-start.sh"]
