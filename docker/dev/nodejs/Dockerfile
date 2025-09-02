# Base stage with common dependencies
FROM node:18.19.0-bullseye AS base

# Set environment variables for better npm performance
ENV NODE_ENV=production
ENV NPM_CONFIG_LOGLEVEL=verbose
ENV NPM_CONFIG_PROGRESS=true
ENV NPM_CONFIG_FETCH_TIMEOUT=600000
ENV NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=20000
ENV NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=120000

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
    ca-certificates && \
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

# Install global dependencies first with optimizations and progress
RUN npm install -g bower gulp gulp-cli karma-cli qs --no-audit --no-fund --progress --verbose && \
    npm link gulp && \
    npm cache clean -f

# Install project dependencies with optimizations and progress
RUN npm install --only=production --no-audit --no-fund --prefer-offline --progress --verbose && \
    bower install --allow-root

# AMD64-specific stage
FROM base AS amd64
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' && \
    apt-get update && apt-get install -yq google-chrome-stable libxss1 && \
    rm -rf /var/lib/apt/lists/*

# ARM64-specific stage
FROM base AS arm64
RUN apt-get update && apt-get install -yq chromium libxss1 && \
    ln -sf /usr/bin/chromium /usr/bin/google-chrome && \
    rm -rf /var/lib/apt/lists/*

# Final stage - automatically selects the right architecture
FROM ${TARGETARCH:-amd64}

# Set Chrome environment variables for Travis CI
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_PATH=/usr/bin/google-chrome
ENV DISPLAY=:99.0

# Copy source code
COPY . /code/

# Set common command and expose port
CMD ["gulp", "dev:runserver"]
EXPOSE 8888
