<<<<<<< HEAD
FROM python:2.7
=======
FROM python:3.6.5
>>>>>>> 98065e3257db0cd629bc64b959a29bae519b0bfe

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/

RUN pip install -r dev.txt

CMD ["./docker/wait-for-it.sh", "db:5432", "--", "sh", "/code/docker/dev/django/container-start.sh"]

EXPOSE 8000
