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
RUN npm install -g bower gulp gulp-cli
RUN npm link gulp
RUN npm cache clean -f
RUN npm install
RUN npm install -g karma-cli
RUN npm install -g qs
RUN bower install --allow-root

# AMD64-specific stage
FROM base AS amd64
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
RUN apt-get update && apt-get install -yq google-chrome-stable libxss1

# ARM64-specific stage
FROM base AS arm64
RUN apt-get update && apt-get install -yq chromium libxss1
RUN ln -sf /usr/bin/chromium /usr/bin/google-chrome

# Final stage - automatically selects the right architecture
FROM ${TARGETARCH:-amd64}

# Set common command and expose port
CMD ["gulp", "dev:runserver"]
EXPOSE 8888
