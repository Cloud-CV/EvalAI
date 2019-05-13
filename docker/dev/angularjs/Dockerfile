FROM node:12.2.0

RUN apt-get update
RUN apt-get install -y build-essential git curl libfontconfig
RUN apt-get install nodejs-legacy -y
RUN npm install -g @angular/cli@7.3.9

RUN mkdir /code

# Copy codebase
COPY . /code

WORKDIR /code
RUN npm install
RUN npm audit fix

EXPOSE 8888

CMD ["ng","serve", "--host", "0.0.0.0"]
