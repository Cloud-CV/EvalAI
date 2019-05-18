FROM node:8.11.2

WORKDIR /code

# Add dependencies
ADD ./package.json /code
ADD ./bower.json /code
ADD ./gulpfile.js /code
ADD ./.eslintrc /code
ADD ./karma.conf.js /code

# Install Prerequisites
RUN npm install -g bower gulp

# This enables `apt` to run from the new sources
RUN printf "deb http://archive.debian.org/debian/ \
jessie main\ndeb-src http://archive.debian.org/debian/ \
jessie main\ndeb http://security.debian.org jessie/updates \
main\ndeb-src http://security.debian.org \
jessie/updates main" > /etc/apt/sources.list

# Install the latest chrome dev package
RUN apt-get update && \
	apt-get -y install gconf-service libasound2 libatk1.0-0 libc6 libcairo2 \
		libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 \
		libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 \
		libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 \
		libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 \
		libnss3 lsb-release xdg-utils wget

RUN npm link gulp

RUN npm cache clean -f
RUN npm install
RUN npm install -g karma-cli
RUN bower install --allow-root

CMD ["gulp", "dev:runserver"]

EXPOSE 8888
