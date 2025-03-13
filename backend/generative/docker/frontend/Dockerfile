# Build stage
FROM node:21-slim as builder

WORKDIR /app

# Install pnpm for better dependency management
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package files
COPY ./frontend/package.json ./frontend/pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY ./frontend .

# Build the application
RUN pnpm build

# Production stage
FROM nginx:mainline-alpine3.20-slim

# Copy nginx configuration
COPY ./docker/frontend/nginx.conf /etc/nginx/nginx.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Add nginx configuration for SPA routing
RUN echo "location / { try_files \$uri \$uri/ /index.html; }" > /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget --quiet --tries=1 --spider http://localhost:80 || exit 1

# Use non-root user
RUN adduser -D -u 1000 frontend
USER frontend

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]