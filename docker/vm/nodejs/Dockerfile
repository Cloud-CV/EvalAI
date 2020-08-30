FROM node:8.11.2 as node

ARG NODE_ENV
ARG DOMAIN_NAME
WORKDIR /code

# Add dependencies
ADD ./package.json /code
ADD ./bower.json /code
ADD ./gulpfile.js /code
ADD ./.eslintrc /code
ADD ./karma.conf.js /code

# Install Prerequisites
RUN npm install -g bower gulp
RUN npm install phantomjs-prebuilt
RUN npm link gulp
RUN npm cache clean -f
RUN npm install
RUN bower install --allow-root
ADD frontend /code/frontend
RUN sed -i "s/example.com/${DOMAIN_NAME}/g" frontend/src/js/config.json

RUN gulp ${NODE_ENV}

FROM nginx:1.13-alpine
# Adding NODE_ENV here as well since this is a multistage build
ARG NODE_ENV
ARG DOMAIN_NAME
ARG NGINX_FILE_NAME

COPY docker/vm/nodejs/${NGINX_FILE_NAME}.conf /etc/nginx/conf.d/default.conf
RUN sed -i "s/example.com/${DOMAIN_NAME}/g" /etc/nginx/conf.d/default.conf
COPY --from=node /code /code