FROM node:8.11.2

WORKDIR /code

# Add dependencies
ADD ./package.json /code
ADD ./gulpfile.js /code
ADD ./.eslintrc /code
ADD ./karma.conf.js /code

# Install Prerequisites
RUN npm install -g yarn gulp

RUN npm link gulp

RUN npm cache clean -f
RUN yarn install

CMD ["gulp", "dev:runserver"]

EXPOSE 8888
