# Stage 1: Build stage with build tools
FROM node:20.18.0-bullseye-slim AS builder

# Set environment variables for npm
ENV NODE_ENV=development \
    NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_PROGRESS=true \
    NPM_CONFIG_FETCH_TIMEOUT=600000 \
    NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=20000 \
    NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=120000

# Install build dependencies only (for native module compilation and bower)
# Note: ca-certificates is needed for git to verify SSL certificates when accessing GitHub
# Add retry logic and --fix-missing to handle transient network issues
RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
    python2 \
    python-is-python2 \
    make \
    g++ \
    git \
    ca-certificates \
    || (apt-get update && apt-get install -y --no-install-recommends --fix-missing \
        python2 \
        python-is-python2 \
        make \
        g++ \
        git \
        ca-certificates) && \
    rm -rf /var/lib/apt/lists/*

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
    npm install -g bower gulp gulp-cli karma-cli qs && \
    npm link gulp && \
    npm cache clean --force

# Install project dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm install --no-audit --no-fund

# Install bower components in builder stage (git available here)
RUN bower install --allow-root

# Clean up npm and bower caches
RUN rm -rf /root/.npm && \
    rm -rf /root/.cache/bower && \
    rm -rf /tmp/*

# Stage 2: Base runtime stage (no build tools, no git)
FROM node:20.18.0-bullseye-slim AS base

ENV NODE_ENV=development \
    CHROME_BIN=/usr/bin/google-chrome \
    CHROME_PATH=/usr/bin/google-chrome \
    DISPLAY=:99.0

# Install only essential runtime dependencies (no build tools, no git)
# Add retry logic and --fix-missing to handle transient network issues
RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
    ca-certificates \
    xvfb \
    || (apt-get update && apt-get install -y --no-install-recommends --fix-missing \
        ca-certificates \
        xvfb) && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/*

WORKDIR /code

# Copy node_modules, global packages, and bower_components from builder
COPY --from=builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /code/node_modules /code/node_modules
COPY --from=builder /code/bower_components /code/bower_components

# AMD64-specific stage for Chrome
FROM base AS amd64
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing google-chrome-stable libxss1 \
    || (apt-get update && apt-get install -y --no-install-recommends --fix-missing google-chrome-stable libxss1) && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/* && \
    # Clean Chrome unnecessary files
    rm -rf /opt/google/chrome/locales/*.pak && \
    find /opt/google/chrome -name "*.pak" ! -name "en-US.pak" -delete 2>/dev/null || true

# ARM64-specific stage for Chromium
FROM base AS arm64
RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing chromium libxss1 \
    || (apt-get update && apt-get install -y --no-install-recommends --fix-missing chromium libxss1) && \
    ln -sf /usr/bin/chromium /usr/bin/google-chrome && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/*

# Final stage - automatically selects the right architecture
FROM ${TARGETARCH:-amd64}

# Copy entrypoint script
COPY docker/dev/nodejs/nodejs-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/nodejs-entrypoint.sh

# Copy package files and source code (excluding node_modules and bower_components)
# These will be copied from builder stage after to ensure precompiled versions are used
COPY package.json bower.json gulpfile.js .eslintrc karma.conf.js .npmrc ./
COPY . /code/

# Re-copy node_modules and bower_components from builder to overwrite any empty directories
# from the source tree, ensuring the precompiled dependencies from builder are preserved
COPY --from=builder /code/node_modules /code/node_modules
COPY --from=builder /code/bower_components /code/bower_components

ENTRYPOINT ["/usr/local/bin/nodejs-entrypoint.sh"]
EXPOSE 8888
