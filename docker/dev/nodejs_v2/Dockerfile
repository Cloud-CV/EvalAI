FROM node:12.2.0 as node

RUN npm install -g @angular/cli@7.3.9
WORKDIR /code

ADD frontend_v2/package.json frontend_v2/yarn.lock /code/
RUN yarn install
ENV PATH="/code/node_modules/.bin:$PATH" 
COPY frontend_v2/ /code

CMD ["yarn","start", "--verbose", "--host", "0.0.0.0"]	
