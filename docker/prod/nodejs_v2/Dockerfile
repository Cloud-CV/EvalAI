FROM node:12.2.0 as node

RUN npm install -g @angular/cli@7.3.9

WORKDIR /code
COPY frontend_v2/package.json frontend_v2/yarn.lock /code/
RUN yarn install
ENV PATH="./node_modules/.bin:$PATH" 
COPY frontend_v2/ /code
RUN ng build --prod

FROM nginx:1.13.12-alpine
COPY docker/dev/nodejs_v2/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=node /code/dist /usr/share/nginx/html
