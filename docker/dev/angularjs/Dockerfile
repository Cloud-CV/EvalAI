FROM ubuntu:14.04
MAINTAINER CloudCV

RUN apt-get update -qq && apt-get install -y build-essential git curl libfontconfig
RUN apt-get install nodejs-legacy -y
RUN apt-get install npm -y
RUN apt-get update
# RUN npm cache clean
# RUN npm install -g @angular/cli@1.6.6

RUN mkdir /code

# ADD dependencies
ADD ./frontend/karma.conf.js /code/frontend/karma.conf.js
ADD ./frontend/package.json /code/frontend/package.json
ADD ./frontend/protractor.conf.js /code/frontend/protractor.conf.js
ADD ./frontend/tsconfig.json /code/frontend/tsconfig.json
ADD ./frontend/tslint.json /code/frontend/tslint.json

WORKDIR /code/frontend

RUN npm install

EXPOSE 4200
