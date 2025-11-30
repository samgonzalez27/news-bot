# =============================================================================
# Multi-stage build for NewsDigest Frontend
# =============================================================================
# Stage 1: Build the Next.js application and export static files
# Stage 2: Serve static assets with Nginx
# =============================================================================

# Stage 1: Build the Next.js application
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Install dependencies first (better caching)
COPY package*.json ./
RUN npm ci --legacy-peer-deps

# Copy source files
COPY . .

# Set build-time environment variables
# Empty NEXT_PUBLIC_API_URL means use relative paths (proxied via nginx)
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-}

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# Build and export static files
# The `next build` command will automatically export to `out/` when output: 'export' is set
RUN npm run build

# Verify the static export was successful
RUN test -d /app/out && echo "Static export successful" || (echo "Static export failed" && exit 1)

# Stage 2: Production image with Nginx
FROM nginx:alpine AS production

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy static assets from builder
COPY --from=builder /app/out /usr/share/nginx/html

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Create custom error pages
RUN echo '<!DOCTYPE html><html><head><title>Error</title></head><body><h1>Service Temporarily Unavailable</h1></body></html>' > /usr/share/nginx/html/50x.html

# Create a fallback 404 page that redirects to index for SPA routing
# This ensures dynamic routes like /digest/[id] work properly
RUN cp /usr/share/nginx/html/index.html /usr/share/nginx/html/404.html 2>/dev/null || true

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
