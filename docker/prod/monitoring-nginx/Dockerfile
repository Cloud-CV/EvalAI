FROM nginx:1.13-alpine
COPY docker/prod/monitoring-nginx/nginx_${MONITORING_ENV}.conf /etc/nginx/conf.d/default.conf
COPY /ssl /etc/ssl
