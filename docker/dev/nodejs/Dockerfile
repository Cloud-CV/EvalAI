FROM ubuntu:14.04
MAINTAINER CloudCV

RUN apt-get update -qq && apt-get install -y build-essential git curl libfontconfig
RUN apt-get install nodejs-legacy -y
RUN apt-get install npm -y
RUN apt-get install -y ruby-dev
RUN gem install sass -v 3.2.19

RUN mkdir /code

# Add dependencies
ADD ./frontend /code/frontend
ADD ./package.json /code
ADD ./bower.json /code
ADD ./gulpfile.js /code
ADD ./.eslintrc /code
ADD ./karma.conf.js /code

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

# Set the command to run on startup
CMD ["gulp", "connect"]

EXPOSE 8888
