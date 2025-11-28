# Deployment Guide

This document covers deploying the NewsDigest Backend API using Docker and CI/CD.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Local Development with Docker](#local-development-with-docker)
- [Production Deployment](#production-deployment)
- [Health Checks](#health-checks)
- [Monitoring and Observability](#monitoring-and-observability)
- [CI/CD Pipeline](#cicd-pipeline)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker 20.10+ and Docker Compose v2+
- PostgreSQL 16+ (or use provided Docker Compose setup)
- Python 3.12+ (for local development without Docker)

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Required Variables

| Variable         | Description                              | Example                                            |
| ---------------- | ---------------------------------------- | -------------------------------------------------- |
| `DATABASE_URL`   | PostgreSQL connection string             | `postgresql://user:pass@localhost:5432/newsdigest` |
| `OPENAI_API_KEY` | OpenAI API key for digest generation     | `sk-...`                                           |
| `NEWS_API_KEY`   | NewsAPI.org API key for article fetching | `abc123...`                                        |
| `RESEND_API_KEY` | Resend.com API key for email delivery    | `re_...`                                           |

### Optional Variables

| Variable                   | Description                    | Default        |
| -------------------------- | ------------------------------ | -------------- |
| `SECRET_KEY`               | JWT signing key                | Auto-generated |
| `LOG_LEVEL`                | Logging level                  | `INFO`         |
| `ENVIRONMENT`              | Deployment environment         | `development`  |
| `SCHEDULER_ENABLED`        | Enable background scheduler    | `false`        |
| `RATE_LIMIT_PER_MINUTE`    | API rate limit                 | `60`           |
| `DIGEST_GENERATION_HOUR`   | Hour to generate digests (UTC) | `6`            |
| `DIGEST_GENERATION_MINUTE` | Minute to generate digests     | `0`            |

### Example `.env` file

```bash
# Database
DATABASE_URL=postgresql://newsdigest:secretpassword@db:5432/newsdigest

# API Keys
OPENAI_API_KEY=sk-your-openai-key
NEWS_API_KEY=your-newsapi-key
RESEND_API_KEY=re_your-resend-key

# Application Settings
SECRET_KEY=your-super-secret-key-here
LOG_LEVEL=INFO
ENVIRONMENT=production
SCHEDULER_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Scheduler Settings
DIGEST_GENERATION_HOUR=6
DIGEST_GENERATION_MINUTE=0
```

---

## Local Development with Docker

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd news-bot
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start all services:**
   ```bash
   docker compose up -d
   ```

4. **Access the API:**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Docker Compose Services

| Service  | Description          | Port |
| -------- | -------------------- | ---- |
| `api`    | FastAPI application  | 8000 |
| `db`     | PostgreSQL database  | 5432 |
| `worker` | Background scheduler | -    |

### Useful Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f api
docker compose logs -f worker

# Stop services
docker compose down

# Rebuild after code changes
docker compose build
docker compose up -d

# Reset database
docker compose down -v
docker compose up -d

# Execute command in api container
docker compose exec api bash
```

---

## Production Deployment

### Building the Docker Image

```bash
# Build production image
docker build -t newsdigest-api:latest .

# Tag for registry
docker tag newsdigest-api:latest ghcr.io/<username>/newsdigest-api:latest

# Push to registry
docker push ghcr.io/<username>/newsdigest-api:latest
```

### Docker Image Features

- **Multi-stage build**: Minimal final image (~150MB)
- **Non-root user**: Runs as `appuser` (UID 1000) for security
- **Health checks**: Built-in health check endpoint
- **No dev dependencies**: Production-only packages

### Production Docker Compose

For production, consider:

1. **External database**: Use managed PostgreSQL (DigitalOcean, AWS RDS, etc.)
2. **Secrets management**: Use Docker secrets or external vault
3. **Reverse proxy**: Add nginx/traefik for TLS termination
4. **Logging**: Configure log aggregation (ELK, Loki, etc.)

Example production override:

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api:
    image: ghcr.io/<username>/newsdigest-api:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - ENVIRONMENT=production
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

---

## Health Checks

The API provides health check endpoints for monitoring and orchestration:

### Endpoints

| Endpoint                | Description                   |
| ----------------------- | ----------------------------- |
| `GET /health`           | Basic liveness check          |
| `GET /health/db`        | Database connectivity check   |
| `GET /health/scheduler` | Scheduler status (if enabled) |

### Response Examples

**Basic Health Check:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Database Health Check:**
```json
{
  "status": "healthy",
  "database": "connected",
  "latency_ms": 2.5
}
```

**Scheduler Health Check:**
```json
{
  "status": "healthy",
  "scheduler": "running",
  "jobs": ["generate_daily_digests", "cleanup_old_articles"],
  "next_run_times": {
    "generate_daily_digests": "2024-01-16T06:00:00Z"
  }
}
```

### Using Health Checks

**Docker Compose:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

**Kubernetes:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health/db
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

---

## Monitoring and Observability

### Structured Logging

All logs are output in JSON format for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "level": "INFO",
  "message": "Request completed",
  "logger": "uvicorn.access",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_path": "/api/v1/digests",
  "client_ip": "192.168.1.1"
}
```

### Request Tracing

Every request is assigned a unique `request_id` (UUID) that:
- Is included in all log entries for that request
- Can be used to trace requests across services
- Is available via the `X-Request-ID` response header

### Log Aggregation

For production, configure log forwarding:

**Docker logging driver:**
```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Or forward to external service:**
```yaml
services:
  api:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: "localhost:24224"
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

The project includes a CI/CD pipeline (`.github/workflows/ci.yml`) that:

1. **Test Job:**
   - Runs on every push and PR
   - Sets up Python 3.12
   - Installs dependencies
   - Runs pytest with coverage
   - Uploads coverage report as artifact

2. **Lint Job:**
   - Runs ruff for code linting
   - Runs in parallel with tests

3. **Build Job:**
   - Runs on main branch only
   - Requires tests and lint to pass
   - Builds Docker image
   - Pushes to GitHub Container Registry
   - Tags: `latest` and commit SHA

4. **Deploy Job:**
   - Runs after successful build
   - Deploys to production (DigitalOcean)

### Required Secrets

Configure these in GitHub repository settings:

| Secret                      | Description                         |
| --------------------------- | ----------------------------------- |
| `GHCR_TOKEN`                | GitHub token for container registry |
| `DIGITALOCEAN_ACCESS_TOKEN` | DigitalOcean API token              |

### Manual Deployment

To deploy manually from the CI/CD image:

```bash
# Pull latest image
docker pull ghcr.io/<username>/newsdigest-api:latest

# Deploy with docker compose
docker compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

### Common Issues

**Container fails to start:**
```bash
# Check logs
docker compose logs api

# Common causes:
# - Missing environment variables
# - Database not ready
# - Port already in use
```

**Database connection errors:**
```bash
# Verify database is running
docker compose ps db

# Check database health
docker compose exec db pg_isready

# Verify connection string
docker compose exec api python -c "from src.config import settings; print(settings.database_url)"
```

**Scheduler not running:**
```bash
# Check worker logs
docker compose logs worker

# Verify SCHEDULER_ENABLED is set
docker compose exec worker env | grep SCHEDULER

# Check scheduler health endpoint
curl http://localhost:8000/health/scheduler
```

**Permission errors (non-root user):**
```bash
# If volume permissions fail, fix ownership
sudo chown -R 1000:1000 ./data

# Or run container as root (not recommended)
docker compose run --user root api bash
```

### Debug Mode

Enable debug logging:

```bash
# Set log level
export LOG_LEVEL=DEBUG
docker compose up -d

# Or in docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG
```

### Getting Help

- Check the API documentation at `/docs`
- Review logs with `docker compose logs -f`
- Run health checks to identify issues
- Check GitHub Issues for known problems
