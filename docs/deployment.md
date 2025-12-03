# 🚀 NewsDigest Production Deployment Runbook

> **Complete guide for deploying NewsDigest on a DigitalOcean Droplet**

**Target Stack:**
- Ubuntu 24.04 LTS
- Docker & Docker Compose
- Caddy (Reverse Proxy with Automatic HTTPS)
- PostgreSQL 16
- FastAPI (Uvicorn)
- Next.js (Static Export)

**Estimated Time:** 2-3 hours  
**Monthly Cost:** $6-12 (DigitalOcean Droplet)

---

## Table of Contents

1. [Pre-Deployment Checklist](#1-pre-deployment-checklist)
2. [Create DigitalOcean Droplet](#2-create-digitalocean-droplet)
3. [Initial Server Security](#3-initial-server-security)
4. [Firewall Configuration](#4-firewall-configuration)
5. [Fail2Ban Setup](#5-fail2ban-setup)
6. [Docker Installation](#6-docker-installation)
7. [DNS Configuration](#7-dns-configuration)
8. [Application Deployment](#8-application-deployment)
9. [SSL/TLS with Caddy](#9-ssltls-with-caddy)
10. [Operational Commands](#10-operational-commands)
11. [CI/CD Pipeline Configuration](#11-cicd-pipeline-configuration)
12. [Monitoring & Maintenance](#12-monitoring--maintenance)
13. [Troubleshooting Guide](#13-troubleshooting-guide)
14. [Security Hardening Checklist](#14-security-hardening-checklist)

---

## 1. Pre-Deployment Checklist

### 1.1 Required Accounts & Credentials

Before starting, ensure you have:

- [ ] DigitalOcean account ([signup](https://www.digitalocean.com/))
- [ ] Domain name (optional but recommended)
- [ ] GitHub account with repository access
- [ ] API Keys ready:
  - [ ] NewsAPI key ([get one](https://newsapi.org/))
  - [ ] OpenAI API key ([get one](https://platform.openai.com/))

### 1.2 Local Machine Requirements

```bash
# Verify SSH is available
ssh -V

# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your-email@example.com"

# View your public key (you'll need this)
cat ~/.ssh/id_ed25519.pub
```

### 1.3 Prepare Environment Variables

Create a secure copy of your production environment variables:

```bash
# Generate a secure JWT secret (save this!)
openssl rand -hex 32

# Generate a secure database password (save this!)
openssl rand -base64 24
```

**Required Variables:**
| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | JWT signing key (min 32 chars) | `<generated-hex-string>` |
| `NEWSAPI_KEY` | NewsAPI.org API key | `abc123...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `POSTGRES_PASSWORD` | Database password | `<generated-password>` |

---

## 2. Create DigitalOcean Droplet

### 2.1 Droplet Specifications

| Setting | Value |
|---------|-------|
| **Image** | Ubuntu 24.04 (LTS) x64 |
| **Plan** | Basic - $6/mo (1GB RAM, 1 vCPU, 25GB SSD) |
| **Datacenter** | Choose closest to your users |
| **Authentication** | SSH Key (recommended) |
| **Hostname** | `newsdigest-prod` |

> **Note:** For production with moderate traffic, consider the $12/mo plan (2GB RAM).

### 2.2 Create Droplet via Web Console

1. Log in to DigitalOcean
2. Click **Create** → **Droplets**
3. Select **Ubuntu 24.04 (LTS) x64**
4. Choose **Basic** plan ($6/mo or $12/mo)
5. Select your preferred datacenter region
6. Under **Authentication**, select **SSH keys**
7. Click **New SSH Key** and paste your public key
8. Set hostname to `newsdigest-prod`
9. Click **Create Droplet**

### 2.3 Note Your Droplet IP

```bash
# Your droplet IP will be shown in the DigitalOcean dashboard
# Example: 164.92.xxx.xxx
export DROPLET_IP="YOUR_DROPLET_IP"
```

### 2.4 Verify SSH Connection

```bash
# Test initial connection as root
ssh root@$DROPLET_IP
```

---

## 3. Initial Server Security

### 3.1 System Updates

```bash
# SSH into server as root
ssh root@$DROPLET_IP

# Update package lists and upgrade all packages
apt update && apt upgrade -y

# Install essential packages
apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Set timezone
timedatectl set-timezone UTC
```

### 3.2 Create Deploy User

```bash
# Create a non-root user for deployments
adduser deploy

# Add to sudo group
usermod -aG sudo deploy

# Create .ssh directory for the new user
mkdir -p /home/deploy/.ssh
chmod 700 /home/deploy/.ssh

# Copy authorized keys from root
cp ~/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys

# Test SSH login as deploy user (in a new terminal)
# ssh deploy@$DROPLET_IP
```

### 3.3 SSH Hardening

```bash
# Backup original SSH config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Edit SSH configuration
vim /etc/ssh/sshd_config
```

**Make these changes in `/etc/ssh/sshd_config`:**

```bash
# Disable root login
PermitRootLogin no

# Disable password authentication (key-only)
PasswordAuthentication no
PubkeyAuthentication yes

# Allow only specific user
AllowUsers deploy

# Change default port (optional, choose between 1024-65535)
# Port 2222

# Other security settings
X11Forwarding no
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
```

```bash
# Validate configuration
sshd -t

# Restart SSH service
systemctl restart sshd

# IMPORTANT: Test login in a NEW terminal before closing current session!
# ssh deploy@$DROPLET_IP
# or if you changed the port:
# ssh -p 2222 deploy@$DROPLET_IP
```

### 3.4 Configure SSH Client (Local Machine)

Add to your local `~/.ssh/config`:

```bash
Host newsdigest
    HostName YOUR_DROPLET_IP
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
```

Now you can connect with: `ssh newsdigest`

---

## 4. Firewall Configuration

### 4.1 Configure UFW (Uncomplicated Firewall)

```bash
# SSH as deploy user
ssh newsdigest

# Check UFW status
sudo ufw status

# Set default policies (deny incoming, allow outgoing)
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (adjust port if you changed it)
sudo ufw allow 22/tcp
# or if you changed SSH port:
# sudo ufw allow 2222/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable UFW
sudo ufw enable

# Verify rules
sudo ufw status verbose
```

**Expected output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
22/tcp (v6)                ALLOW       Anywhere (v6)
80/tcp (v6)                ALLOW       Anywhere (v6)
443/tcp (v6)               ALLOW       Anywhere (v6)
```

---

## 5. Fail2Ban Setup

### 5.1 Install and Configure Fail2Ban

```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Create local configuration
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit configuration
sudo vim /etc/fail2ban/jail.local
```

**Add/modify these settings in `/etc/fail2ban/jail.local`:**

```ini
[DEFAULT]
# Ban hosts for 1 hour
bantime = 1h

# Ban if 5 failures within 10 minutes
findtime = 10m
maxretry = 5

# Email notifications (optional)
# destemail = your-email@example.com
# sender = fail2ban@newsdigest.com
# action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
# If you changed SSH port:
# port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 24h
```

```bash
# Start and enable Fail2Ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Verify status
sudo fail2ban-client status

# Check SSH jail specifically
sudo fail2ban-client status sshd
```

---

## 6. Docker Installation

### 6.1 Install Docker Engine

```bash
# Remove old Docker versions (if any)
sudo apt remove docker docker-engine docker.io containerd runc 2>/dev/null

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add deploy user to docker group
sudo usermod -aG docker deploy

# Apply group changes (or logout/login)
newgrp docker

# Verify installation
docker --version
docker compose version

# Test Docker
docker run hello-world
```

### 6.2 Configure Docker for Production

```bash
# Create Docker daemon configuration
sudo vim /etc/docker/daemon.json
```

**Add to `/etc/docker/daemon.json`:**

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    }
  }
}
```

```bash
# Restart Docker
sudo systemctl restart docker

# Enable Docker to start on boot
sudo systemctl enable docker
```

---

## 7. DNS Configuration

### 7.1 Configure DNS Records

Add these DNS records at your domain registrar:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | `@` | `YOUR_DROPLET_IP` | 300 |
| A | `www` | `YOUR_DROPLET_IP` | 300 |
| A | `api` | `YOUR_DROPLET_IP` | 300 (optional) |

### 7.2 Verify DNS Propagation

```bash
# Check A record
dig +short yourdomain.com

# Check www subdomain
dig +short www.yourdomain.com

# Alternative: use online tools
# https://www.whatsmydns.net/
```

> **Note:** DNS propagation can take 5 minutes to 48 hours. Continue setup while waiting.

---

## 8. Application Deployment

### 8.1 Create Application Directory

```bash
# Create directory structure
sudo mkdir -p /opt/newsdigest
sudo chown -R deploy:deploy /opt/newsdigest

# Navigate to application directory
cd /opt/newsdigest
```

### 8.2 Clone Repository

```bash
# Generate deploy key for GitHub (on server)
ssh-keygen -t ed25519 -C "newsdigest-deploy" -f ~/.ssh/github_deploy

# Display public key (add this to GitHub as deploy key)
cat ~/.ssh/github_deploy.pub

# Configure SSH to use this key for GitHub
vim ~/.ssh/config
```

**Add to `~/.ssh/config`:**

```bash
Host github.com
    IdentityFile ~/.ssh/github_deploy
    IdentitiesOnly yes
```

```bash
# Clone repository
git clone git@github.com:samgonzalez27/news-bot.git /opt/newsdigest

# Navigate to project
cd /opt/newsdigest
```

### 8.3 Configure Environment Variables

```bash
# Create production environment file
cp .env.example .env.production
vim .env.production
```

**Configure `.env.production`:**

```bash
# =============================================================================
# NewsDigest Production Environment
# =============================================================================

# -----------------------------------------------------------------------------
# Required Secrets (CHANGE THESE!)
# -----------------------------------------------------------------------------
JWT_SECRET_KEY=your-generated-jwt-secret-minimum-32-characters
NEWSAPI_KEY=your-newsapi-key
OPENAI_API_KEY=sk-your-openai-api-key
POSTGRES_PASSWORD=your-secure-database-password

# -----------------------------------------------------------------------------
# Application Settings
# -----------------------------------------------------------------------------
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# -----------------------------------------------------------------------------
# JWT Settings
# -----------------------------------------------------------------------------
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# -----------------------------------------------------------------------------
# OpenAI Settings
# -----------------------------------------------------------------------------
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000

# -----------------------------------------------------------------------------
# CORS Configuration (update with your domain)
# -----------------------------------------------------------------------------
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# -----------------------------------------------------------------------------
# Scheduler Configuration
# -----------------------------------------------------------------------------
SCHEDULER_ENABLED=true
DIGEST_CHECK_INTERVAL_MINUTES=15

# -----------------------------------------------------------------------------
# Rate Limiting
# -----------------------------------------------------------------------------
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# -----------------------------------------------------------------------------
# pgAdmin Settings (CHANGE THESE!)
# -----------------------------------------------------------------------------
PGADMIN_EMAIL=admin@yourdomain.com
PGADMIN_PASSWORD=secure-pgadmin-password

# -----------------------------------------------------------------------------
# Frontend Settings
# -----------------------------------------------------------------------------
NEXT_PUBLIC_API_URL=

# -----------------------------------------------------------------------------
# Domain Configuration
# -----------------------------------------------------------------------------
DOMAIN=yourdomain.com
```

```bash
# Secure the environment file
chmod 600 .env.production

# Create symlink for docker compose
ln -sf .env.production .env
```

### 8.4 Create Production Docker Compose Override

```bash
# Create production-specific compose file
vim docker-compose.prod.yml
```

**Create `docker-compose.prod.yml`:**

```yaml
# =============================================================================
# Production Docker Compose Override
# =============================================================================
# Usage: docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
# =============================================================================

services:
  db:
    # Don't expose PostgreSQL port to host in production
    ports: !override []
    restart: always

  pgadmin:
    # Don't expose pgAdmin directly (use Caddy)
    ports: !override []
    restart: always
    profiles:
      - admin  # Only start with: docker compose --profile admin up -d

  api:
    # Don't expose API directly (use Caddy)
    ports: !override []
    restart: always
    environment:
      - APP_ENV=production
      - DEBUG=false
      - LOG_LEVEL=INFO

  frontend:
    restart: always

  nginx:
    # Nginx will be replaced by Caddy
    profiles:
      - nginx  # Disabled by default
```

### 8.5 Create Caddy Configuration

```bash
# Create Caddy directory
mkdir -p /opt/newsdigest/caddy

# Create Caddyfile
vim /opt/newsdigest/caddy/Caddyfile
```

**Create `caddy/Caddyfile`:**

```caddyfile
# =============================================================================
# NewsDigest Caddy Configuration
# =============================================================================
# Automatic HTTPS with Let's Encrypt
# =============================================================================

{
    # Global options
    email admin@yourdomain.com
    
    # Uncomment for staging certificates during testing
    # acme_ca https://acme-staging-v02.api.letsencrypt.org/directory
}

# Main website (www subdomain)
www.yourdomain.com {
    # Frontend static files
    reverse_proxy frontend:80

    # API routes
    handle /api/* {
        reverse_proxy api:8000
    }

    # Health check endpoint
    handle /health {
        reverse_proxy api:8000
    }

    # API documentation
    handle /docs {
        reverse_proxy api:8000
    }
    handle /redoc {
        reverse_proxy api:8000
    }
    handle /openapi.json {
        reverse_proxy api:8000
    }

    # Security headers
    header {
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    # Compression
    encode gzip

    # Logging
    log {
        output file /var/log/caddy/access.log {
            roll_size 10MB
            roll_keep 5
        }
    }
}

# Redirect root domain to www
yourdomain.com {
    redir https://www.yourdomain.com{uri} permanent
}

# pgAdmin (restrict access!)
# SECURITY: Consider IP whitelisting or VPN-only access
pgadmin.yourdomain.com {
    # Basic auth protection
    basicauth {
        admin $2a$14$HASHED_PASSWORD_HERE
    }
    
    reverse_proxy pgadmin:80

    # Security headers
    header {
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
    }
}
```

### 8.6 Create Complete Production Compose File

```bash
# Create the complete production compose file
vim docker-compose.production.yml
```

**Create `docker-compose.production.yml`:**

```yaml
# =============================================================================
# NewsDigest Production Stack
# =============================================================================
# Usage: docker compose -f docker-compose.production.yml up -d
# =============================================================================

services:
  # ---------------------------------------------------------------------------
  # Database Service - PostgreSQL
  # ---------------------------------------------------------------------------
  db:
    image: postgres:16-alpine
    container_name: newsdigest-db
    restart: always
    environment:
      - POSTGRES_USER=newsdigest
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=newsdigest_db
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U newsdigest -d newsdigest_db"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - internal

  # ---------------------------------------------------------------------------
  # pgAdmin Service - Database Administration (optional)
  # ---------------------------------------------------------------------------
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: newsdigest-pgadmin
    restart: always
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
      PGADMIN_CONFIG_SERVER_MODE: "False"
      PGADMIN_CONFIG_MASTER_PASSWORD_REQUIRED: "False"
    volumes:
      - pgadmin-data:/var/lib/pgadmin
    depends_on:
      db:
        condition: service_healthy
    networks:
      - internal
      - web
    profiles:
      - admin

  # ---------------------------------------------------------------------------
  # API Service - FastAPI Application
  # ---------------------------------------------------------------------------
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: newsdigest-api
    restart: always
    environment:
      - DATABASE_URL=postgresql+asyncpg://newsdigest:${POSTGRES_PASSWORD}@db:5432/newsdigest_db
      - APP_ENV=production
      - DEBUG=false
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - NEWSAPI_KEY=${NEWSAPI_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - SCHEDULER_ENABLED=${SCHEDULER_ENABLED:-true}
      - RATE_LIMIT_PER_MINUTE=${RATE_LIMIT_PER_MINUTE:-60}
      - RATE_LIMIT_BURST=${RATE_LIMIT_BURST:-10}
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    volumes:
      - app-logs:/var/log/news-digest
    networks:
      - internal
      - web

  # ---------------------------------------------------------------------------
  # Frontend Service - Next.js Static Site
  # ---------------------------------------------------------------------------
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-}
    container_name: newsdigest-frontend
    restart: always
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://127.0.0.1:80/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - web

  # ---------------------------------------------------------------------------
  # Caddy - Reverse Proxy with Automatic HTTPS
  # ---------------------------------------------------------------------------
  caddy:
    image: caddy:2.8-alpine
    container_name: newsdigest-caddy
    restart: always
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"  # HTTP/3
    volumes:
      - ./caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config
      - caddy-logs:/var/log/caddy
    depends_on:
      api:
        condition: service_healthy
      frontend:
        condition: service_healthy
    networks:
      - web
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:2019/metrics"]
      interval: 30s
      timeout: 10s
      retries: 3

# -----------------------------------------------------------------------------
# Volumes
# -----------------------------------------------------------------------------
volumes:
  postgres-data:
    driver: local
  pgadmin-data:
    driver: local
  app-logs:
    driver: local
  caddy-data:
    driver: local
  caddy-config:
    driver: local
  caddy-logs:
    driver: local

# -----------------------------------------------------------------------------
# Networks
# -----------------------------------------------------------------------------
networks:
  web:
    driver: bridge
  internal:
    driver: bridge
    internal: true
```

### 8.7 Build and Deploy

```bash
# Navigate to project directory
cd /opt/newsdigest

# Build images
docker compose -f docker-compose.production.yml build

# Start services
docker compose -f docker-compose.production.yml up -d

# Verify all containers are running
docker compose -f docker-compose.production.yml ps

# Check logs
docker compose -f docker-compose.production.yml logs -f
```

---

## 9. SSL/TLS with Caddy

### 9.1 Verify HTTPS

Caddy automatically provisions SSL certificates from Let's Encrypt.

```bash
# Check Caddy logs for certificate provisioning
docker compose -f docker-compose.production.yml logs caddy

# Test HTTPS
curl -I https://www.yourdomain.com

# Test HTTP to HTTPS redirect
curl -I http://yourdomain.com
```

### 9.2 Certificate Management

```bash
# View certificate information
docker exec newsdigest-caddy caddy list-certificates

# Force certificate renewal (if needed)
docker exec newsdigest-caddy caddy reload
```

### 9.3 Troubleshooting SSL Issues

```bash
# Check Caddy is running
docker exec newsdigest-caddy caddy validate

# Test certificate with OpenSSL
openssl s_client -connect www.yourdomain.com:443 -servername www.yourdomain.com

# Check Let's Encrypt rate limits
# https://letsencrypt.org/docs/rate-limits/
```

---

## 10. Operational Commands

### 10.1 Service Management

```bash
# Start all services
docker compose -f docker-compose.production.yml up -d

# Stop all services
docker compose -f docker-compose.production.yml down

# Restart specific service
docker compose -f docker-compose.production.yml restart api

# Restart all services
docker compose -f docker-compose.production.yml restart

# View running containers
docker compose -f docker-compose.production.yml ps

# Start with admin tools (pgAdmin)
docker compose -f docker-compose.production.yml --profile admin up -d
```

### 10.2 Viewing Logs

```bash
# All service logs
docker compose -f docker-compose.production.yml logs -f

# Specific service logs
docker compose -f docker-compose.production.yml logs -f api
docker compose -f docker-compose.production.yml logs -f caddy
docker compose -f docker-compose.production.yml logs -f db

# Last 100 lines
docker compose -f docker-compose.production.yml logs --tail=100 api

# Since a specific time
docker compose -f docker-compose.production.yml logs --since="2024-01-01T00:00:00" api
```

### 10.3 Updating the Application

```bash
# Navigate to project directory
cd /opt/newsdigest

# Pull latest code
git pull origin main

# Rebuild and restart services
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d

# Or with zero-downtime (rebuild in background)
docker compose -f docker-compose.production.yml up -d --build

# Clean up old images
docker image prune -f
```

### 10.4 Database Operations

```bash
# Access PostgreSQL CLI
docker exec -it newsdigest-db psql -U newsdigest -d newsdigest_db

# Create database backup
docker exec newsdigest-db pg_dump -U newsdigest newsdigest_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
cat backup_YYYYMMDD_HHMMSS.sql | docker exec -i newsdigest-db psql -U newsdigest -d newsdigest_db

# View database size
docker exec newsdigest-db psql -U newsdigest -d newsdigest_db -c "SELECT pg_size_pretty(pg_database_size('newsdigest_db'));"
```

### 10.5 Shell Access

```bash
# Access API container shell
docker exec -it newsdigest-api /bin/bash

# Access database container shell
docker exec -it newsdigest-db /bin/sh

# Access Caddy container shell
docker exec -it newsdigest-caddy /bin/sh
```

---

## 11. CI/CD Pipeline Configuration

### 11.1 GitHub Secrets Setup

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

| Secret Name | Value |
|-------------|-------|
| `SSH_PRIVATE_KEY` | Your deploy SSH private key |
| `DROPLET_HOST` | Your droplet IP address |
| `DROPLET_USER` | `deploy` |

### 11.2 Generate Deploy SSH Key

```bash
# On your LOCAL machine
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy

# Display private key (add to GitHub Secrets as SSH_PRIVATE_KEY)
cat ~/.ssh/github_actions_deploy

# Display public key (add to server)
cat ~/.ssh/github_actions_deploy.pub
```

```bash
# On SERVER: Add the public key
ssh newsdigest
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
```

### 11.3 Update GitHub Actions Workflow

Update `.github/workflows/ci.yml` to enable deployment:

```yaml
# Uncomment and configure the deploy job in your existing ci.yml

  deploy:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: production
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H ${{ secrets.DROPLET_HOST }} >> ~/.ssh/known_hosts

      - name: Deploy to DigitalOcean Droplet
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.DROPLET_USER }}@${{ secrets.DROPLET_HOST }} << 'EOF'
            set -e
            echo "🚀 Starting deployment..."
            
            cd /opt/newsdigest
            
            # Pull latest code
            git pull origin main
            
            # Pull latest images and rebuild
            docker compose -f docker-compose.production.yml pull
            docker compose -f docker-compose.production.yml build
            
            # Deploy with zero-downtime
            docker compose -f docker-compose.production.yml up -d
            
            # Wait for services to be healthy
            sleep 10
            
            # Verify deployment
            if curl -sf http://localhost:8000/health > /dev/null; then
              echo "✅ API health check passed"
            else
              echo "❌ API health check failed"
              exit 1
            fi
            
            # Clean up old images
            docker image prune -f
            
            echo "✅ Deployment completed successfully!"
          EOF

      - name: Health Check
        run: |
          sleep 15
          status_code=$(curl -s -o /dev/null -w "%{http_code}" https://www.yourdomain.com/health)
          if [ $status_code -eq 200 ]; then
            echo "✅ Production health check passed (HTTP $status_code)"
          else
            echo "❌ Production health check failed (HTTP $status_code)"
            exit 1
          fi

      - name: Cleanup SSH
        if: always()
        run: rm -f ~/.ssh/deploy_key
```

---

## 12. Monitoring & Maintenance

### 12.1 Health Checks

```bash
# Manual health check
curl -s https://www.yourdomain.com/health | jq

# Check all container health status
docker compose -f docker-compose.production.yml ps

# Check container resource usage
docker stats --no-stream
```

### 12.2 Log Rotation

Docker logs are automatically rotated based on the daemon config. For application logs:

```bash
# Create logrotate configuration
sudo vim /etc/logrotate.d/newsdigest
```

**Add to `/etc/logrotate.d/newsdigest`:**

```
/opt/newsdigest/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    sharedscripts
    postrotate
        docker compose -f /opt/newsdigest/docker-compose.production.yml kill -s USR1 api
    endscript
}
```

### 12.3 Automated Backups

```bash
# Create backup script
vim /opt/newsdigest/scripts/backup.sh
```

**Create `scripts/backup.sh`:**

```bash
#!/bin/bash
# =============================================================================
# NewsDigest Database Backup Script
# =============================================================================

set -e

BACKUP_DIR="/opt/newsdigest/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker exec newsdigest-db pg_dump -U newsdigest newsdigest_db | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Delete old backups
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ Backup completed: $BACKUP_DIR/db_$DATE.sql.gz"
```

```bash
# Make executable
chmod +x /opt/newsdigest/scripts/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
```

**Add to crontab:**

```cron
0 2 * * * /opt/newsdigest/scripts/backup.sh >> /var/log/newsdigest-backup.log 2>&1
```

### 12.4 System Updates

```bash
# Create update script
vim /opt/newsdigest/scripts/update-system.sh
```

**Create `scripts/update-system.sh`:**

```bash
#!/bin/bash
# =============================================================================
# System Update Script
# =============================================================================

set -e

echo "📦 Updating system packages..."
apt update
apt upgrade -y

echo "🐳 Updating Docker images..."
cd /opt/newsdigest
docker compose -f docker-compose.production.yml pull

echo "🧹 Cleaning up..."
apt autoremove -y
docker system prune -f

echo "✅ System update completed!"
```

```bash
chmod +x /opt/newsdigest/scripts/update-system.sh
```

---

## 13. Troubleshooting Guide

### 13.1 Common Issues

#### Container Won't Start

```bash
# Check container logs
docker compose -f docker-compose.production.yml logs api

# Check container status
docker compose -f docker-compose.production.yml ps

# Inspect container
docker inspect newsdigest-api
```

#### Database Connection Issues

```bash
# Test database connection
docker exec newsdigest-db pg_isready -U newsdigest

# Check database logs
docker compose -f docker-compose.production.yml logs db

# Verify environment variables
docker exec newsdigest-api env | grep DATABASE
```

#### SSL Certificate Issues

```bash
# Check Caddy logs
docker compose -f docker-compose.production.yml logs caddy

# Validate Caddyfile
docker exec newsdigest-caddy caddy validate --config /etc/caddy/Caddyfile

# Check certificate status
docker exec newsdigest-caddy caddy list-certificates
```

#### Out of Disk Space

```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Clean up Docker resources
docker system prune -a --volumes

# Find large files
du -sh /opt/newsdigest/*
```

### 13.2 Emergency Rollback

```bash
# Stop current deployment
docker compose -f docker-compose.production.yml down

# Checkout previous working commit
git log --oneline -10
git checkout <previous-commit-hash>

# Rebuild and restart
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d
```

### 13.3 View Real-time Metrics

```bash
# Container resource usage
docker stats

# System resources
htop

# Network connections
ss -tuln

# Disk I/O
iotop
```

---

## 14. Security Hardening Checklist

### 14.1 Server Security

- [ ] **SSH Configuration**
  - [ ] Root login disabled
  - [ ] Password authentication disabled
  - [ ] SSH keys only
  - [ ] Non-default port (optional)

- [ ] **Firewall (UFW)**
  - [ ] Default deny incoming
  - [ ] Only necessary ports open (22, 80, 443)
  - [ ] IPv6 rules configured

- [ ] **Fail2Ban**
  - [ ] Installed and running
  - [ ] SSH jail active
  - [ ] Appropriate ban times configured

### 14.2 Application Security

- [ ] **Environment Variables**
  - [ ] Strong JWT secret (32+ characters)
  - [ ] Secure database password
  - [ ] Environment file has 600 permissions
  - [ ] No secrets in version control

- [ ] **Network**
  - [ ] Database not exposed to host
  - [ ] Internal network for inter-service communication
  - [ ] HTTPS enforced
  - [ ] Security headers configured

- [ ] **Docker**
  - [ ] Non-root user in containers
  - [ ] Read-only mounts where possible
  - [ ] Resource limits configured
  - [ ] Regular image updates

### 14.3 Monitoring & Maintenance

- [ ] **Backups**
  - [ ] Automated daily backups
  - [ ] Backup retention policy
  - [ ] Tested restore procedure

- [ ] **Updates**
  - [ ] System update schedule
  - [ ] Docker image update process
  - [ ] Security patch monitoring

- [ ] **Logging**
  - [ ] Application logs configured
  - [ ] Log rotation enabled
  - [ ] Log monitoring (optional: external service)

---

## Quick Reference Card

### Essential Commands

```bash
# SSH to server
ssh newsdigest

# Navigate to project
cd /opt/newsdigest

# View status
docker compose -f docker-compose.production.yml ps

# View logs
docker compose -f docker-compose.production.yml logs -f

# Restart services
docker compose -f docker-compose.production.yml restart

# Update and deploy
git pull && docker compose -f docker-compose.production.yml up -d --build

# Backup database
docker exec newsdigest-db pg_dump -U newsdigest newsdigest_db > backup.sql

# Check system resources
htop
docker stats
```

### Important Paths

| Path | Description |
|------|-------------|
| `/opt/newsdigest` | Application root |
| `/opt/newsdigest/.env` | Environment variables |
| `/opt/newsdigest/caddy/Caddyfile` | Caddy configuration |
| `/opt/newsdigest/backups` | Database backups |
| `/opt/newsdigest/scripts` | Maintenance scripts |

### Service URLs

| Service | URL |
|---------|-----|
| Frontend | `https://www.yourdomain.com` |
| API Docs | `https://www.yourdomain.com/docs` |
| Health Check | `https://www.yourdomain.com/health` |
| pgAdmin | `https://pgadmin.yourdomain.com` |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-03 | Initial release |

---

**Document maintained by:** Sam Gonzalez  
**Last updated:** December 3, 2024
