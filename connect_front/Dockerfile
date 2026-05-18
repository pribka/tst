FROM node:16.20.2-alpine3.18 as build-stage

WORKDIR /app

COPY package*.json ./

RUN apk add --no-cache python3 build-base
ENV PYTHON=/usr/bin/python3

RUN npm config set @dhx:registry https://npm.dhtmlx.com
RUN npm install --legacy-peer-deps

COPY . .

RUN npm run build

FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY ./nginx/conf.d /etc/nginx/conf.d

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]