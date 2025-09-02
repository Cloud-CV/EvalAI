FROM node:18.19.0-bullseye

ARG NODE_ENV

# Install Python2, symlink, and C++ build tools for node-gyp/node-sass
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python2 \
    python-is-python2 \
    make \
    g++ \
    curl \
    wget \
    gnupg \
    ca-certificates \
    xvfb && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy package files first for better caching
COPY package.json bower.json gulpfile.js .eslintrc karma.conf.js .npmrc ./

# Configure npm with better settings for Docker builds
RUN npm config set fetch-timeout 600000 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set progress true && \
    npm config set loglevel verbose && \
    npm config set maxsockets 50

# Install global dependencies
RUN npm install -g bower gulp gulp-cli karma-cli qs --no-audit --no-fund --progress --verbose && \
    npm link gulp && \
    npm cache clean -f

# Install project dependencies with optimizations
RUN npm install --only=production --no-audit --no-fund --prefer-offline --progress --verbose

# Copy frontend source
COPY frontend /code/frontend

# Install bower components after source code is copied
RUN bower install --allow-root

# Install Chrome for testing (if needed)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' && \
    apt-get update && apt-get install -yq google-chrome-stable libxss1 && \
    rm -rf /var/lib/apt/lists/*

# Set Chrome environment variables for production
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_PATH=/usr/bin/google-chrome
ENV DISPLAY=:99.0

RUN gulp ${NODE_ENV}

FROM nginx:1.13-alpine
# Adding NODE_ENV here as well since this is a multistage build
ARG NODE_ENV
COPY docker/prod/nodejs/nginx_${NODE_ENV}.conf /etc/nginx/conf.d/default.conf
COPY --from=0 /code /code
COPY /ssl /etc/ssl
