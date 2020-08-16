FROM node:8.11.2 as node

ARG NODE_ENV
ARG BACKEND
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
RUN sed -i "s/BACKEND/${BACKEND}/g" frontend/src/js/config.json

RUN gulp ${NODE_ENV}

FROM nginx:1.13-alpine
# Adding NODE_ENV here as well since this is a multistage build
ARG NODE_ENV
ARG DOMAIN
ARG FRONTEND
ARG BACKEND

COPY docker/vm/nodejs/nginx_${NODE_ENV}.conf /etc/nginx/conf.d/default.conf

# Update Frontend, Backend, Domain in nginx configs
RUN sed -i "s/DOMAIN/${DOMAIN}/g" /etc/nginx/conf.d/default.conf
RUN sed -i "s/FRONTEND/${FRONTEND}/g" /etc/nginx/conf.d/default.conf
RUN sed -i "s/BACKEND/${BACKEND}/g" /etc/nginx/conf.d/default.conf

COPY --from=node /code /code
