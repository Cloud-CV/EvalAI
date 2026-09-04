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
# deb.debian.org (Fastly) intermittently resets connections, and sporadically
# returns 404 for pool files that do exist -- the same URL serves fine minutes
# later. Acquire::Retries handles the transport errors, but apt treats 404 as
# fatal and will not retry it, so retry the whole update+install with a pause.
# Bounded, so a genuinely missing package still fails the build.
# Do not "fix" this by pointing at another mirror: security.debian.org and
# cloudfront.debian.net were both measured to 404 bullseye-security pool files
# that deb.debian.org serves correctly.
RUN n=0; until [ "$n" -ge 4 ]; do \
        apt-get -o Acquire::Retries=5 update && \
        apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
        python2 \
        python-is-python2 \
        make \
        g++ \
        git \
        ca-certificates \
        && break; \
        n=$((n+1)); \
        echo "apt failed (attempt $n), retrying in 20s" >&2; \
        sleep 20; \
    done; \
    [ "$n" -lt 4 ] && \
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

# Install only essential runtime dependencies (no build tools, no git).
# xvfb is installed with Chrome/Chromium in arch-specific stages so Mesa GL deps resolve together.
RUN n=0; until [ "$n" -ge 4 ]; do \
        apt-get -o Acquire::Retries=5 update && \
        apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
        ca-certificates \
        && break; \
        n=$((n+1)); \
        echo "apt failed (attempt $n), retrying in 20s" >&2; \
        sleep 20; \
    done; \
    [ "$n" -lt 4 ] && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/*

WORKDIR /code

# Copy node_modules, global packages, and bower_components from builder
COPY --from=builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /code/node_modules /code/node_modules
COPY --from=builder /code/bower_components /code/bower_components

# AMD64-specific stage for Chrome
FROM base AS amd64
RUN n=0; until [ "$n" -ge 4 ]; do \
        apt-get -o Acquire::Retries=5 update && \
        apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
        wget \
        gnupg \
        procps \
        && break; \
        n=$((n+1)); \
        echo "apt failed (attempt $n), retrying in 20s" >&2; \
        sleep 20; \
    done; \
    [ "$n" -lt 4 ] && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    rm -rf /var/lib/apt/lists/*

RUN n=0; until [ "$n" -ge 4 ]; do \
        apt-get -o Acquire::Retries=5 update && \
        apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
        google-chrome-stable \
        libxss1 \
        xvfb \
        && break; \
        n=$((n+1)); \
        echo "apt failed (attempt $n), retrying in 20s" >&2; \
        sleep 20; \
    done; \
    [ "$n" -lt 4 ] && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/* && \
    find /opt/google/chrome/locales -name "*.pak" ! -name "en-US.pak" -delete 2>/dev/null || true

# ARM64-specific stage for Chromium
FROM base AS arm64
RUN n=0; until [ "$n" -ge 4 ]; do \
        apt-get -o Acquire::Retries=5 update && \
        apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
        chromium \
        libxss1 \
        procps \
        xvfb \
        && break; \
        n=$((n+1)); \
        echo "apt failed (attempt $n), retrying in 20s" >&2; \
        sleep 20; \
    done; \
    [ "$n" -lt 4 ] && \
    ln -sf /usr/bin/chromium /usr/bin/google-chrome && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/*

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
