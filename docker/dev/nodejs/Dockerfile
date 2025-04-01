# Base stage with common dependencies
FROM node:14.20.0 AS base
WORKDIR /code

# Add dependencies
ADD ./package.json /code
ADD ./bower.json /code
ADD ./gulpfile.js /code
ADD ./.eslintrc /code
ADD ./karma.conf.js /code

# Install Prerequisites
RUN npm ci --quiet && \
    npm install -g bower gulp-cli karma-cli qs && \
    npm link gulp && \
    bower install --allow-root --silent


# AMD64-specific stage
FROM base AS amd64
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
RUN apt-get update && apt-get install -yq google-chrome-stable libxss1

# ARM64-specific stage
FROM base AS arm64
# Using newer keyring method for better compatibility
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-chrome.gpg
# Add a message for users on ARM64
RUN echo "Chrome installation skipped on ARM64 architecture" && \
    # Create a placeholder chrome executable that exits gracefully
    echo '#!/bin/bash' > /usr/bin/google-chrome && \
    echo 'echo "Warning: Running on ARM64 architecture. Chrome is not available."' >> /usr/bin/google-chrome && \
    echo 'echo "For full Chrome functionality, rebuild with: docker build --platform=linux/amd64 ."' >> /usr/bin/google-chrome && \
    echo 'exit 0' >> /usr/bin/google-chrome && \
    chmod +x /usr/bin/google-chrome && \
    apt-get update && apt-get install -yq libxss1

# Final stage - automatically selects the right architecture
FROM ${TARGETARCH:-amd64}

# Set common command and expose port
CMD ["gulp", "dev:runserver"]
EXPOSE 8888
