FROM python:3.6.5

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD requirements/* /code/

RUN pip install -U cffi service_identity
RUN pip install -r prod.txt
RUN pip install -r worker.txt

ADD . /code

CMD ["python", "-m", "scripts.workers.submission_worker"]
