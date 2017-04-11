FROM ubuntu:14.04
MAINTAINER Deshraj

RUN apt-get update -qq && apt-get install -y build-essential git curl
RUN apt-get install nodejs-legacy -y
RUN apt-get install npm -y
RUN apt-get install -y ruby
RUN gem install sass

RUN mkdir /code

# Add dependencies
ADD . /code
WORKDIR /code

# Install Prerequisites
RUN npm install bower -g
RUN npm install gulp -g

RUN npm link gulp

RUN npm cache clean -f
RUN npm install -g n
RUN n stable

RUN npm install
RUN bower install --allow-root

RUN gulp dev:runserver

EXPOSE 8888
