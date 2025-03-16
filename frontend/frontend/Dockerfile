FROM node:18 AS build

WORKDIR /app

COPY package.json yarn.lock ./

RUN echo "FRONTEND: Yarn install"
RUN yarn install

COPY . .

RUN echo "FRONTEND: Build"
RUN yarn build

FROM nginx:alpine

RUN echo "FRONTEND: Copy build"
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

RUN echo "FRONTEND: Start"
CMD ["nginx", "-g", "daemon off;"]
