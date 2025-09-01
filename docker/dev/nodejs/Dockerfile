# Base stage with common dependencies
FROM node:14.21.3-bullseye AS base

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
COPY package.json bower.json gulpfile.js .eslintrc karma.conf.js ./

# Install global dependencies
RUN npm install -g bower gulp gulp-cli karma-cli qs && \
    npm link gulp && \
    npm cache clean -f

# Install project dependencies
RUN npm ci --only=production --no-audit --no-fund && \
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

# Copy source code
COPY . /code/

# Set common command and expose port
CMD ["gulp", "dev:runserver"]
EXPOSE 8888
