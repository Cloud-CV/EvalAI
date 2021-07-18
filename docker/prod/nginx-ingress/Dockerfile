FROM nginx:1.13-alpine
ARG MONITORING_ENV
COPY docker/prod/nginx-ingress/nginx_${MONITORING_ENV}.conf /etc/nginx/conf.d/default.conf
COPY /ssl /etc/ssl
