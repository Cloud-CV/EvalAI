FROM node:18.19.0-bullseye AS base

ARG NODE_ENV

# Install Python2, symlink, and C++ build tools for node-gyp/node-sass
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python2 \
    python-is-python2 \
    make \
    g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy package files first for better caching
COPY package.json bower.json gulpfile.js .eslintrc karma.conf.js .npmrc ./

# Configure npm with better settings for Docker builds
RUN npm config set fetch-timeout 600000 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set progress true && \
    npm config set loglevel verbose

# Install global dependencies
RUN npm install -g bower gulp gulp-cli qs --progress && \
    npm install phantomjs-prebuilt --progress && \
    npm link gulp && \
    npm cache clean -f

# Install project dependencies with optimizations
RUN npm install --only=production --no-audit --no-fund --prefer-offline --progress && \
    bower install --allow-root

# Copy frontend source
COPY frontend /code/frontend

RUN gulp ${NODE_ENV}

FROM nginx:1.13-alpine
# Adding NODE_ENV here as well since this is a multistage build
ARG NODE_ENV
COPY docker/prod/nodejs/nginx_${NODE_ENV}.conf /etc/nginx/conf.d/default.conf
COPY --from=base /code /code
COPY /ssl /etc/ssl
