# Infrastructure Setup Guide

## Overview

This document provides step-by-step instructions for deploying the News Digest API on a DigitalOcean droplet with Nginx, SSL, and systemd.

## Prerequisites

- DigitalOcean account
- Domain name pointed to DigitalOcean (for SSL)
- SSH key configured

## 1. DigitalOcean Droplet Setup

### Create Droplet

1. **Image**: Ubuntu 22.04 LTS
2. **Plan**: Basic - 1 GB RAM / 1 CPU ($6/month) - sufficient for personal use
3. **Region**: Choose closest to your users
4. **Authentication**: SSH key
5. **Hostname**: `news-digest-api`

### Initial Server Setup

```bash
# Connect to server
ssh root@your_server_ip

# Update system
apt update && apt upgrade -y

# Create application user
adduser newsdigest
usermod -aG sudo newsdigest

# Copy SSH key to new user
rsync --archive --chown=newsdigest:newsdigest ~/.ssh /home/newsdigest

# Configure firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable

# Switch to application user
su - newsdigest
```

## 2. Install Dependencies

### System Packages

```bash
# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip \
    postgresql postgresql-contrib \
    nginx certbot python3-certbot-nginx \
    git curl

# Verify Python version
python3.11 --version
```

### PostgreSQL Setup

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER newsdigest WITH PASSWORD 'your_secure_password_here';
CREATE DATABASE newsdigest_db OWNER newsdigest;
GRANT ALL PRIVILEGES ON DATABASE newsdigest_db TO newsdigest;
\c newsdigest_db
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
EOF

# Test connection
psql -U newsdigest -d newsdigest_db -h localhost -c "SELECT 1;"
```

## 3. Application Deployment

### Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/news-digest
sudo chown newsdigest:newsdigest /opt/news-digest

# Clone repository
cd /opt/news-digest
git clone https://github.com/yourusername/news-bot.git .
```

### Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Environment Configuration

```bash
# Create .env file
cat > /opt/news-digest/.env << 'EOF'
# Application
APP_NAME=NewsDigestAPI
APP_ENV=production
DEBUG=false
API_V1_PREFIX=/api/v1

# Server
HOST=127.0.0.1
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://newsdigest:your_secure_password@localhost:5432/newsdigest_db

# JWT Authentication
JWT_SECRET_KEY=your_256_bit_secret_key_here_generate_with_openssl
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# External APIs
NEWSAPI_KEY=your_newsapi_key_here
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/news-digest/app.log

# CORS (your frontend domain)
CORS_ORIGINS=["https://yourdomain.com"]
EOF

# Secure the .env file
chmod 600 /opt/news-digest/.env
```

### Generate JWT Secret

```bash
# Generate a secure 256-bit key
openssl rand -hex 32
```

### Create Log Directory

```bash
sudo mkdir -p /var/log/news-digest
sudo chown newsdigest:newsdigest /var/log/news-digest
```

### Run Database Migrations

```bash
cd /opt/news-digest
source venv/bin/activate
alembic upgrade head
```

## 4. Systemd Service

### Create Service File

```bash
sudo cat > /etc/systemd/system/news-digest.service << 'EOF'
[Unit]
Description=News Digest FastAPI Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=newsdigest
Group=newsdigest
WorkingDirectory=/opt/news-digest
Environment="PATH=/opt/news-digest/venv/bin"
EnvironmentFile=/opt/news-digest/.env
ExecStart=/opt/news-digest/venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000 --workers 2
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/news-digest /opt/news-digest

[Install]
WantedBy=multi-user.target
EOF
```

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable news-digest

# Start service
sudo systemctl start news-digest

# Check status
sudo systemctl status news-digest

# View logs
sudo journalctl -u news-digest -f
```

## 5. Nginx Configuration

### Create Nginx Site Configuration

```bash
sudo cat > /etc/nginx/sites-available/news-digest << 'EOF'
# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

upstream news_digest_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL configuration (will be managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/news-digest-access.log;
    error_log /var/log/nginx/news-digest-error.log;

    # Request size limits
    client_max_body_size 1M;

    # Gzip compression
    gzip on;
    gzip_types application/json text/plain;
    gzip_min_length 1000;

    # API location
    location /api/ {
        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;

        # Proxy settings
        proxy_pass http://news_digest_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffer settings
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://news_digest_backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Connection "";
    }

    # OpenAPI docs
    location /docs {
        proxy_pass http://news_digest_backend/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Connection "";
    }

    location /openapi.json {
        proxy_pass http://news_digest_backend/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Connection "";
    }
}
EOF
```

### Enable Site

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/news-digest /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## 6. SSL Certificate (Let's Encrypt)

### Obtain Certificate

```bash
# Temporarily allow HTTP for certificate verification
sudo certbot certonly --nginx -d api.yourdomain.com

# Or use standalone mode if Nginx isn't configured yet
sudo certbot certonly --standalone -d api.yourdomain.com
```

### Auto-Renewal

Certbot automatically sets up a systemd timer for renewal. Verify:

```bash
sudo systemctl list-timers | grep certbot
```

### Post-Renewal Hook

```bash
# Create renewal hook to reload Nginx
sudo cat > /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh << 'EOF'
#!/bin/bash
systemctl reload nginx
EOF

sudo chmod +x /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

## 7. Log Rotation

### Configure Logrotate

```bash
sudo cat > /etc/logrotate.d/news-digest << 'EOF'
/var/log/news-digest/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 newsdigest newsdigest
    sharedscripts
    postrotate
        systemctl reload news-digest > /dev/null 2>&1 || true
    endscript
}
EOF
```

## 8. DigitalOcean Monitoring

### Enable Droplet Monitoring

1. Go to DigitalOcean control panel
2. Select your droplet
3. Enable "Monitoring" in the droplet settings

### Install Monitoring Agent (if not pre-installed)

```bash
curl -sSL https://repos.insights.digitalocean.com/install.sh | sudo bash
```

### Set Up Alerts

In DigitalOcean control panel, create alerts for:
- CPU > 80% for 5 minutes
- Memory > 80% for 5 minutes
- Disk > 80%

## 9. Backup Configuration

### Database Backup Script

```bash
# Create backup directory
sudo mkdir -p /opt/backups
sudo chown newsdigest:newsdigest /opt/backups

# Create backup script
cat > /opt/news-digest/scripts/backup.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/newsdigest_$DATE.dump"

# Create backup
pg_dump -Fc -h localhost -U newsdigest newsdigest_db > "$BACKUP_FILE"

# Compress
gzip "$BACKUP_FILE"

# Remove backups older than 7 days
find "$BACKUP_DIR" -name "newsdigest_*.dump.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
EOF

chmod +x /opt/news-digest/scripts/backup.sh
```

### Schedule Backup

```bash
# Add to crontab
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/news-digest/scripts/backup.sh >> /var/log/news-digest/backup.log 2>&1") | crontab -
```

## 10. Environment Variables Reference

### `.env.example`

```bash
# =============================================================================
# News Digest API - Environment Configuration
# =============================================================================
# Copy this file to .env and fill in the values
# NEVER commit the .env file to version control
# =============================================================================

# -----------------------------------------------------------------------------
# Application Settings
# -----------------------------------------------------------------------------
APP_NAME=NewsDigestAPI
APP_ENV=production                    # development, staging, production
DEBUG=false                           # Enable debug mode (never in production)
API_V1_PREFIX=/api/v1

# -----------------------------------------------------------------------------
# Server Configuration
# -----------------------------------------------------------------------------
HOST=127.0.0.1                        # Bind address (127.0.0.1 for reverse proxy)
PORT=8000                             # Application port

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL=postgresql+asyncpg://newsdigest:password@localhost:5432/newsdigest_db

# Connection pool settings
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# -----------------------------------------------------------------------------
# JWT Authentication
# -----------------------------------------------------------------------------
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your_256_bit_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# -----------------------------------------------------------------------------
# External API Keys
# -----------------------------------------------------------------------------
# NewsAPI - Get from https://newsapi.org/
NEWSAPI_KEY=your_newsapi_key_here

# OpenAI - Get from https://platform.openai.com/
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini              # or gpt-4, gpt-3.5-turbo
OPENAI_MAX_TOKENS=2000

# -----------------------------------------------------------------------------
# Rate Limiting
# -----------------------------------------------------------------------------
RATE_LIMIT_PER_MINUTE=60              # Requests per minute per user
RATE_LIMIT_BURST=10                   # Burst allowance

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE_PATH=/var/log/news-digest/app.log
LOG_MAX_BYTES=10485760                # 10 MB
LOG_BACKUP_COUNT=5

# -----------------------------------------------------------------------------
# CORS Configuration
# -----------------------------------------------------------------------------
# JSON array of allowed origins
CORS_ORIGINS=["https://yourdomain.com"]

# -----------------------------------------------------------------------------
# Scheduler Configuration
# -----------------------------------------------------------------------------
SCHEDULER_ENABLED=true
DIGEST_CHECK_INTERVAL_MINUTES=15      # How often to check for due digests
```

## 11. Deployment Checklist

### Before Deployment

- [ ] Generate secure JWT secret key
- [ ] Obtain NewsAPI key
- [ ] Obtain OpenAI API key
- [ ] Configure DNS to point to droplet IP
- [ ] Review and customize `.env` values

### Deployment Steps

1. [ ] Create DigitalOcean droplet
2. [ ] Initial server setup (user, firewall)
3. [ ] Install system dependencies
4. [ ] Configure PostgreSQL
5. [ ] Clone repository
6. [ ] Set up Python environment
7. [ ] Configure `.env` file
8. [ ] Run database migrations
9. [ ] Create and start systemd service
10. [ ] Configure Nginx
11. [ ] Obtain SSL certificate
12. [ ] Test all endpoints
13. [ ] Enable monitoring and alerts
14. [ ] Set up backup schedule

### Post-Deployment Verification

```bash
# Check service status
sudo systemctl status news-digest

# Check Nginx status
sudo systemctl status nginx

# Test health endpoint
curl -k https://api.yourdomain.com/health

# Check logs
sudo journalctl -u news-digest --since "1 hour ago"
tail -f /var/log/news-digest/app.log
```

## 12. Maintenance Commands

### Service Management

```bash
# Restart application
sudo systemctl restart news-digest

# View application logs
sudo journalctl -u news-digest -f

# View Nginx access logs
sudo tail -f /var/log/nginx/news-digest-access.log
```

### Database Maintenance

```bash
# Connect to database
sudo -u newsdigest psql -d newsdigest_db

# Run migrations
cd /opt/news-digest && source venv/bin/activate && alembic upgrade head

# Create backup
/opt/news-digest/scripts/backup.sh
```

### Update Application

```bash
cd /opt/news-digest
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart news-digest
```
