FROM node:12.2.0

RUN npm install -g @angular/cli@7.3.9
WORKDIR /code

ADD frontend_v2/package.json frontend_v2/yarn.lock /code/
RUN yarn install
ENV PATH="/code/node_modules/.bin:$PATH" 

CMD ["yarn","start", "--verbose", "--host", "0.0.0.0"]
