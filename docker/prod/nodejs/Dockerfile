# Stage 1: Build stage with build tools
FROM node:20.18.0-bullseye-slim AS builder

ARG NODE_ENV=production

# Set environment variables for npm
ENV NODE_ENV=${NODE_ENV} \
    NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_PROGRESS=true \
    NPM_CONFIG_FETCH_TIMEOUT=600000 \
    NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=20000 \
    NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=120000

# Install build dependencies only (for native module compilation and bower)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python2 \
    python-is-python2 \
    make \
    g++ \
    git \
    ca-certificates \
    curl \
    wget \
    gnupg \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy package files first for better caching
COPY package.json bower.json gulpfile.js .eslintrc karma.conf.js .npmrc ./

# Configure npm with optimized settings
RUN npm config set fetch-timeout 600000 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set progress true && \
    npm config set maxsockets 50 && \
    npm config set audit false && \
    npm config set fund false

# Install global dependencies with BuildKit cache
RUN --mount=type=cache,target=/root/.npm \
    npm install -g bower gulp gulp-cli karma-cli qs --no-audit --no-fund && \
    npm link gulp && \
    npm cache clean --force

# Install project dependencies with BuildKit cache mount (production only)
RUN --mount=type=cache,target=/root/.npm \
    npm install --only=production --no-audit --no-fund

# Copy frontend source
COPY frontend /code/frontend

# Copy SSL certificates to builder (if they exist in build context)
# Note: SSL files are pulled from S3 before build in push.sh script
# ssl/ is excluded from .dockerignore for production builds
# Since COPY fails if source doesn't exist, we copy the build context to a temp
# location first (already filtered by .dockerignore), then conditionally copy ssl
COPY . /tmp/build-context/
RUN mkdir -p /code/ssl && \
    if [ -d /tmp/build-context/ssl ] && [ "$(ls -A /tmp/build-context/ssl 2>/dev/null)" ]; then \
        cp -r /tmp/build-context/ssl/* /code/ssl/; \
    fi && \
    rm -rf /tmp/build-context

# Install bower components in builder stage
RUN bower install --allow-root

# Install Chrome for testing (if needed)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable libxss1 && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/* && \
    # Clean Chrome unnecessary files
    rm -rf /opt/google/chrome/locales/*.pak && \
    find /opt/google/chrome -name "*.pak" ! -name "en-US.pak" -delete 2>/dev/null || true

# Set Chrome environment variables
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_PATH=/usr/bin/google-chrome
ENV DISPLAY=:99.0

# Build frontend assets
RUN gulp ${NODE_ENV}

# Clean up npm and bower caches
RUN rm -rf /root/.npm && \
    rm -rf /root/.cache/bower && \
    rm -rf /tmp/*

# Stage 2: Nginx stage (already minimal with alpine)
FROM nginx:1.13-alpine

ARG NODE_ENV=production

# Copy nginx configuration
COPY docker/prod/nodejs/nginx_${NODE_ENV}.conf /etc/nginx/conf.d/default.conf

# Copy built frontend assets from builder stage
COPY --from=builder /code /code

# Copy SSL certificates from builder stage if they exist
RUN mkdir -p /etc/ssl && \
    if [ -d /code/ssl ] && [ "$(ls -A /code/ssl 2>/dev/null)" ]; then \
        cp -r /code/ssl/* /etc/ssl/; \
    fi
