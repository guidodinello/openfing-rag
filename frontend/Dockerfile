FROM node:22-alpine AS base

RUN npm install -g pnpm@latest-10

WORKDIR /app

COPY package.json pnpm-lock.yaml ./

FROM base AS dependencies
RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
    --mount=type=cache,target=/app/node_modules/.cache \
    pnpm install --frozen-lockfile

FROM dependencies AS builder

ARG VITE_API_URL
ARG VITE_APP_TITLE
ARG VITE_APP_VERSION

ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_APP_TITLE=${VITE_APP_TITLE}
ENV VITE_APP_VERSION=${VITE_APP_VERSION}
ENV NODE_ENV=production

COPY . .

RUN --mount=type=cache,target=/app/node_modules/.cache \
    pnpm run build

FROM nginx:1.29-alpine AS production

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    # Create nginx cache directory
    mkdir -p /var/cache/nginx && \
    chown -R nginx:nginx /var/cache/nginx

USER nginx

CMD ["nginx", "-g", "daemon off;"]
