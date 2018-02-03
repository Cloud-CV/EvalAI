FROM node:9.4.0
MAINTAINER CloudCV Team

RUN apt-get update -qq && apt-get install -y build-essential git curl libfontconfig
RUN apt-get install nodejs-legacy -y
RUN apt-get install npm -y
RUN npm cache verify
RUN npm install -g @angular/cli@1.6.5 --unsafe

RUN mkdir /code

# Copy codebase
COPY . /code

WORKDIR /code

RUN npm install

EXPOSE 8888

CMD ["ng","serve", "--host", "0.0.0.0"]
