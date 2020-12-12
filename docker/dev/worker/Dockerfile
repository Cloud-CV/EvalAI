FROM evalai_django

RUN apt-get update && \
  apt-get install -q -y default-jdk


RUN pip install -r worker.txt

ADD . /code

CMD ["./docker/wait-for-it.sh", "django:8000", "--", "python", "-m", "scripts.workers.submission_worker"]
