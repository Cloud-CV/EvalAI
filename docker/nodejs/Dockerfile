FROM nginx:latest

########### Nginx Configuration starts here ###########
RUN apt-get update && apt-get install -qqy --no-install-recommends \
    supervisor \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY docker/nodejs/remote.conf etc/nginx/conf.d/
COPY docker/nodejs/uwsgi_params etc/nginx/conf.d/

COPY docker/nodejs/nginx.sh /
COPY docker/nodejs/nginx_supervisor.conf /etc/supervisor/conf.d/app.conf
RUN mkdir -p /var/log/supervisord

RUN rm /etc/nginx/conf.d/default.conf
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN sed -i '15i\ \tclient_max_body_size 75M;' /etc/nginx/nginx.conf

RUN ln -sf /dev/stdout /var/log/nginx/acces.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

###########  NodeJS Configurations starts here ###########
RUN apt-get update -qq && apt-get install -y build-essential git curl
RUN apt-get install nodejs-legacy -y
RUN apt-get install npm -y
RUN apt-get install -y ruby
RUN gem install sass

RUN groupadd webapps
RUN useradd nodejs -G webapps
RUN mkdir -p /var/log/nodejs/ && chown -R nodejs /var/log/nodejs/ && chmod -R u+rX /var/log/nodejs/
RUN mkdir -p /var/run/nodejs/ && chown -R nodejs /var/run/nodejs/ && chmod -R u+rX /var/run/nodejs/

RUN apt-get install -y supervisor
RUN mkdir -p /var/log/supervisor

RUN mkdir /code

# Add dependencies
ADD ./ /code
WORKDIR /code

# Install Prerequisites
RUN npm install bower -g
RUN npm install gulp -g

RUN npm cache clean -f
RUN npm install -g n
RUN n stable

RUN npm install
RUN bower install --allow-root

# Port 80 for server
EXPOSE 80

CMD ["sh", "/code/docker/nodejs/nginx.sh"]
