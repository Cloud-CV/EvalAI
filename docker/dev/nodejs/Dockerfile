FROM node:8.11.2

WORKDIR /code

# Add dependencies
ADD ./package.json /code
ADD ./bower.json /code
ADD ./gulpfile.js /code
ADD ./.eslintrc /code
ADD ./karma.conf.js /code

# Install Prerequisites
<<<<<<< HEAD
RUN npm install -g bower gulp@next
=======
RUN npm install -g bower gulp
>>>>>>> 98065e3257db0cd629bc64b959a29bae519b0bfe

RUN npm link gulp

RUN npm cache clean -f
RUN npm install
RUN bower install --allow-root

CMD ["gulp", "dev:runserver"]

EXPOSE 8888
