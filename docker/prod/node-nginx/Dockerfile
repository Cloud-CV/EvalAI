FROM nginx:1.10
MAINTAINER Deshraj

RUN apt-get update -qq && apt-get install -y build-essential git curl
RUN apt-get install nodejs-legacy -y
RUN apt-get install npm -y
RUN apt-get install -y ruby
RUN gem install sass

RUN mkdir /code

# Add dependencies
ADD . /code
WORKDIR /code

# Install Prerequisites
RUN npm install bower -g
RUN npm install gulp -g

RUN npm link gulp

RUN npm cache clean -f
RUN npm install -g n
RUN n stable

RUN npm install
RUN bower install --allow-root

RUN gulp prod

RUN apt-get update && apt-get install -qqy --no-install-recommends \
    supervisor \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


COPY docker/prod/node-nginx/remote.conf /etc/nginx/conf.d/
COPY docker/prod/node-nginx/uwsgi_params /etc/nginx/conf.d/

COPY docker/prod/node-nginx/container-start.sh /
COPY docker/prod/node-nginx/nginx_supervisor.conf /etc/supervisor/conf.d/app.conf
RUN mkdir -p /var/log/supervisord

RUN rm /etc/nginx/conf.d/default.conf
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN sed -i '15i\ \tclient_max_body_size 75M;' /etc/nginx/nginx.conf

RUN ln -sf /dev/stdout /var/log/nginx/acces.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 80
