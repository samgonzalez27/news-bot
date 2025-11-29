# Nginx Proxy Configuration for NewsDigest

This document provides Nginx configuration examples for serving both the frontend static site and proxying API requests to the backend on a single DigitalOcean droplet.

## Overview

The recommended setup:
- Frontend: Served as static files by Nginx
- Backend: FastAPI running on port 8000
- Nginx: Reverse proxy on port 80/443

## Option 1: Frontend Container + Nginx Proxy

If running frontend in a Docker container with its own Nginx:

```nginx
# /etc/nginx/sites-available/newsdigest

upstream frontend {
    server 127.0.0.1:3000;  # Frontend container port
}

upstream backend {
    server 127.0.0.1:8000;  # Backend container port
}

server {
    listen 80;
    server_name example.com www.example.com;

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    # SSL certificates (via Certbot)
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # API proxy
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Health endpoint for backend
    location /health {
        proxy_pass http://backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Frontend proxy
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Option 2: Serve Static Files Directly

If extracting frontend static files to serve directly (more efficient):

```nginx
# /etc/nginx/sites-available/newsdigest

upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name example.com www.example.com;

    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    # Document root for frontend static files
    root /var/www/newsdigest/out;
    index index.html;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml image/svg+xml;

    # API proxy to backend
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400s;
    }

    # Direct backend health check
    location /health {
        proxy_pass http://backend/health;
        proxy_set_header Host $host;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Next.js static files
    location /_next/static/ {
        alias /var/www/newsdigest/out/_next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA fallback - serve index.html for client routes
    location / {
        try_files $uri $uri.html $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

## Setting Up TLS with Certbot

1. **Install Certbot:**
   ```bash
   sudo apt update
   sudo apt install certbot python3-certbot-nginx
   ```

2. **Obtain certificates:**
   ```bash
   sudo certbot --nginx -d example.com -d www.example.com
   ```

3. **Auto-renewal test:**
   ```bash
   sudo certbot renew --dry-run
   ```

## Deployment Steps

1. **Copy static files to server:**
   ```bash
   # From frontend directory after build
   scp -r out/* user@droplet:/var/www/newsdigest/out/
   ```

2. **Set permissions:**
   ```bash
   sudo chown -R www-data:www-data /var/www/newsdigest
   sudo chmod -R 755 /var/www/newsdigest
   ```

3. **Enable site:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/newsdigest /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Environment Configuration

For the frontend to communicate with the backend:

- **Same domain (recommended):** Frontend uses `/api/*` routes, Nginx proxies to backend
- **Different domain:** Set `NEXT_PUBLIC_API_URL` at build time

## Troubleshooting

### 502 Bad Gateway
- Check if backend container is running: `docker ps`
- Verify backend is listening: `curl http://localhost:8000/health`
- Check Nginx logs: `tail -f /var/log/nginx/error.log`

### CORS Errors
- Ensure backend `CORS_ORIGINS` includes the frontend domain
- Check browser network tab for actual origin being sent

### Static Files Not Found
- Verify `root` path in Nginx config
- Check file permissions
- Ensure `try_files` directive is correct

### SSL Certificate Issues
- Renew certificates: `sudo certbot renew`
- Check certificate paths in config
- Verify domain DNS points to server
