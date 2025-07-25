FROM node:22-alpine AS builder

ARG VITE_API_URL
ARG VITE_APP_TITLE
ARG VITE_APP_VERSION

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_TITLE=$VITE_APP_TITLE
ENV VITE_APP_VERSION=$VITE_APP_VERSION

RUN npm install -g pnpm@latest

WORKDIR /app

COPY package.json pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm build

FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

CMD ["nginx", "-g", "daemon off;"]
