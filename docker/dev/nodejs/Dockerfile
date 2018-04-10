FROM node:8.11.1
MAINTAINER EvalAI Team <team@cloudcv.org>

RUN apt-get update -qq && apt-get install -y build-essential git curl libfontconfig
RUN apt-get update

RUN mkdir /code

# Add dependencies
ADD ./package.json /code
ADD ./bower.json /code
ADD ./gulpfile.js /code
ADD ./.eslintrc /code
ADD ./karma.conf.js /code

WORKDIR /code

# Install Prerequisites
RUN npm install -g bower gulp

RUN npm link gulp

RUN npm cache clean -f
RUN npm install -g n
RUN n stable
RUN npm install
RUN bower install --allow-root

ADD . /code

CMD ["gulp", "dev:runserver"]

EXPOSE 8888
