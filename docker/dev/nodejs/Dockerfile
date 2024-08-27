FROM node:14.20.0

RUN wget https://mirrors.edge.kernel.org/ubuntu/pool/main/g/gcc-10/gcc-10-base_10-20200411-0ubuntu1_amd64.deb && dpkg -i gcc-10-base_10-20200411-0ubuntu1_amd64.deb
RUN wget https://mirrors.edge.kernel.org/ubuntu/pool/main/g/gcc-10/libgcc-s1_10-20200411-0ubuntu1_amd64.deb && dpkg -i libgcc-s1_10-20200411-0ubuntu1_amd64.deb

# install chrome for protractor tests
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
RUN apt-get update && apt-get install -yq google-chrome-stable

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
RUN apt-get install -y libxss1

CMD ["gulp", "dev:runserver"]

EXPOSE 8888
