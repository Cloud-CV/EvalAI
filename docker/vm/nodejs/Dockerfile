FROM node:8.11.2 as node

ARG NODE_ENV
ARG BACKEND
ARG TYPE
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

# Update Backend URL with args
RUN sed -i "s/BACKEND_DOMAIN/${BACKEND}/g" frontend/src/js/config.json
RUN sed -i "s/https/${TYPE}/g" frontend/src/js/config.json

RUN gulp ${NODE_ENV}

FROM nginx:1.13-alpine
# Adding NODE_ENV here as well since this is a multistage build
ARG NODE_ENV
ARG DOMAIN
ARG FRONTEND
ARG BACKEND
ARG NGINX_FILE_NAME

COPY docker/vm/nodejs/${NGINX_FILE_NAME}.conf /etc/nginx/conf.d/default.conf

# Update Frontend, Backend, Domain in nginx configs
RUN sed -i "s/DOMAIN/${DOMAIN}/g" /etc/nginx/conf.d/default.conf
RUN sed -i "s/FRONTEND/${FRONTEND}/g" /etc/nginx/conf.d/default.conf
RUN sed -i "s/BACKEND/${BACKEND}/g" /etc/nginx/conf.d/default.conf

COPY --from=node /code /code
