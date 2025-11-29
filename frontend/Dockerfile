# Multi-stage build for NewsDigest Frontend
# Stage 1: Build the Next.js application
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --legacy-peer-deps

# Copy source files
COPY . .

# Set build-time environment variables
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000}

# Build and export static files
RUN npm run build

# Stage 2: Production image with Nginx
FROM nginx:alpine AS production

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy static assets from builder
COPY --from=builder /app/out /usr/share/nginx/html

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Set correct permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
