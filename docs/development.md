# Deployment Guide

This document covers deploying the full-stack NewsDigest application using Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Services Overview](#services-overview)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker 20.10+ and Docker Compose v2+
- API Keys:
  - NewsAPI key ([get one here](https://newsapi.org/))
  - OpenAI API key ([get one here](https://platform.openai.com/))

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd news-bot

# 2. Create environment file
cp .env.example .env

# 3. Edit .env with your API keys
nano .env

# 4. Start all services
docker compose up --build

# 5. Access the application
# Frontend: http://localhost
# API Docs: http://localhost/docs
# pgAdmin:  http://localhost:5050
```

---

## Environment Variables

### Required Variables

| Variable            | Description                    | Example                |
| ------------------- | ------------------------------ | ---------------------- |
| `JWT_SECRET_KEY`    | JWT signing key (min 32 chars) | `openssl rand -hex 32` |
| `NEWSAPI_KEY`       | NewsAPI.org API key            | `abc123...`            |
| `OPENAI_API_KEY`    | OpenAI API key                 | `sk-...`               |
| `POSTGRES_PASSWORD` | Database password              | `newsdigest_secret`    |

### Optional Variables

| Variable            | Description                 | Default                  |
| ------------------- | --------------------------- | ------------------------ |
| `APP_ENV`           | Environment mode            | `development`            |
| `LOG_LEVEL`         | Logging level               | `INFO`                   |
| `SCHEDULER_ENABLED` | Enable background scheduler | `true`                   |
| `CORS_ORIGINS`      | Allowed CORS origins        | `http://localhost`       |
| `PGADMIN_EMAIL`     | pgAdmin login email         | `admin@newsdigest.local` |
| `PGADMIN_PASSWORD`  | pgAdmin login password      | `admin`                  |

### Example `.env` file

```bash
# Required - API Keys
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters
NEWSAPI_KEY=your-newsapi-key
OPENAI_API_KEY=your-openai-key
POSTGRES_PASSWORD=newsdigest_secret

# Optional - Application Settings
APP_ENV=production
LOG_LEVEL=INFO
SCHEDULER_ENABLED=true
CORS_ORIGINS=http://localhost,http://yourdomain.com

# Optional - pgAdmin
PGADMIN_EMAIL=admin@newsdigest.local
PGADMIN_PASSWORD=admin
```

---

## Services Overview

The `docker-compose.yml` includes the following services:

| Service    | Description         | Port     | URL                   |
| ---------- | ------------------- | -------- | --------------------- |
| `nginx`    | Reverse proxy       | 80       | http://localhost      |
| `frontend` | Next.js static site | Internal | Via nginx             |
| `api`      | FastAPI backend     | Internal | Via nginx at /api     |
| `db`       | PostgreSQL 16       | Internal | -                     |
| `pgadmin`  | Database admin      | 5050     | http://localhost:5050 |

### Architecture

```
                    ┌─────────────┐
                    │   nginx     │ :80
                    │   (proxy)   │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
      ┌──────────┐  ┌──────────┐  ┌──────────┐
      │ frontend │  │   api    │  │   docs   │
      │ (static) │  │ (FastAPI)│  │ (/docs)  │
      └──────────┘  └────┬─────┘  └──────────┘
                         │
                    ┌────┴────┐
                    │   db    │
                    │(postgres)│
                    └─────────┘
```

---

## Local Development

### Full Stack (Docker)

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Rebuild after changes
docker compose up --build -d
```

### Backend Only (Local Python)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start database
docker compose up -d db

# Run migrations
alembic upgrade head

# Start server
uvicorn src.main:app --reload --port 8000
```

### Frontend Only (Local Node.js)

```bash
cd frontend

# Install dependencies
npm install

# Set API URL (backend must be running)
export NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

---

## Production Deployment

### DigitalOcean Droplet

1. **Create a Droplet:**
   - Ubuntu 22.04+
   - 2GB RAM minimum
   - Enable monitoring

2. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```

3. **Clone and Configure:**
   ```bash
   git clone <repository-url>
   cd news-bot
   cp .env.example .env
   nano .env  # Configure with production values
   ```

4. **Start Services:**
   ```bash
   docker compose up -d
   ```

### SSL/HTTPS with Let's Encrypt

For production, add SSL by modifying `nginx/nginx.conf`:

```nginx
# Add to http block
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of config
}
```

Generate certificates with certbot:

```bash
# Install certbot
apt install certbot

# Generate certificate
certbot certonly --standalone -d yourdomain.com

# Auto-renewal cron
echo "0 0 * * * certbot renew --quiet" | crontab -
```

### Resource Limits

For production, add resource limits to `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

---

## Health Checks

### Endpoints

| Endpoint                | Description           |
| ----------------------- | --------------------- |
| `GET /health`           | Basic liveness check  |
| `GET /health/db`        | Database connectivity |
| `GET /health/scheduler` | Scheduler status      |
| `GET /health/ready`     | Full readiness check  |

### Example Responses

```bash
# Basic health check
curl http://localhost/health
# {"status": "healthy", "app": "NewsDigestAPI", "version": "1.0.0"}

# Database health
curl http://localhost/health/db
# {"status": "ok", "latency_ms": 1.23}

# Scheduler status
curl http://localhost/health/scheduler
# {"enabled": true, "running": true, "jobs": [...], "job_count": 1}
```

---

## Troubleshooting

### Container Issues

```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f nginx

# Restart a service
docker compose restart api

# Rebuild from scratch
docker compose down -v
docker compose up --build
```

### Common Problems

**Port already in use:**
```bash
# Check what's using port 80
sudo lsof -i :80

# Stop conflicting service or change port in docker-compose.yml
```

**Database connection failed:**
```bash
# Check database is healthy
docker compose exec db pg_isready -U newsdigest

# View database logs
docker compose logs db
```

**Frontend not loading:**
```bash
# Check nginx logs
docker compose logs nginx

# Verify frontend build
docker compose logs frontend | grep -i error
```

**API returns 502:**
```bash
# Check API is running
docker compose ps api

# Check API health
docker compose exec api curl -s localhost:8000/health
```

### Reset Everything

```bash
# Stop and remove all containers, volumes, and networks
docker compose down -v --remove-orphans

# Remove all images
docker compose down --rmi all

# Fresh start
docker compose up --build
```

---

## Useful Commands

```bash
# Execute command in container
docker compose exec api bash
docker compose exec db psql -U newsdigest -d newsdigest_db

# Run migrations
docker compose exec api alembic upgrade head

# Create new migration
docker compose exec api alembic revision --autogenerate -m "description"

# View database
docker compose exec db psql -U newsdigest -d newsdigest_db -c "\dt"

# Copy logs
docker compose logs api > api.log
```
