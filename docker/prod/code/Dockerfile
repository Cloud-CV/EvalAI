FROM python:2.7

MAINTAINER Deshraj(deshraj@vt.edu)

RUN git clone https://github.com/Cloud-CV/evalai.git --branch master
VOLUME ["/evalai"]
RUN chmod 775 -R /evalai/media/* 
CMD ["chmod", "775" "-R", "/evalai/media/*"]
