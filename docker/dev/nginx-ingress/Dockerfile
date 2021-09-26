FROM nginx:1.13-alpine
COPY monitoring/authentication/.htpasswd /etc/nginx/.htpasswd
COPY docker/dev/nginx-ingress/nginx.conf /etc/nginx/nginx.conf
COPY docker/dev/nginx-ingress/nginx_http.conf /etc/nginx/conf.d/default.conf
