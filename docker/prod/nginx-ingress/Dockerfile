FROM nginx:1.13-alpine
ARG MONITORING_ENV
COPY monitoring/authentication/.htpasswd /etc/nginx/.htpasswd
COPY docker/prod/nginx-ingress/nginx_${MONITORING_ENV}.conf /etc/nginx/nginx.conf
COPY docker/prod/nginx-ingress/nginx_http_${MONITORING_ENV}.conf /etc/nginx/conf.d/default.conf
COPY /ssl /etc/ssl
