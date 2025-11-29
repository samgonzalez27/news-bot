# NewsDigest Frontend Deployment Checklist

Use this checklist to ensure a smooth deployment of the NewsDigest frontend.

## Pre-Deployment

### Environment & Secrets

- [ ] `NEXT_PUBLIC_API_URL` - Set to production API URL
- [ ] `GITHUB_TOKEN` or `GHCR_PAT` - For pushing/pulling Docker images
- [ ] GitHub Actions secrets configured:
  - [ ] `DO_HOST` - Droplet IP address
  - [ ] `DO_SSH_USER` - SSH username (usually `root` or custom user)
  - [ ] `DO_SSH_KEY` - Private SSH key for deployment
- [ ] `.env.local` created from `.env.local.example`

### Build Verification

- [ ] `npm install` completes without errors
- [ ] `npm run lint` passes
- [ ] `npm run build` succeeds
- [ ] `out/` directory contains exported static files
- [ ] Test locally: `npx serve out` works

### Docker Verification

- [ ] `docker build` completes successfully
- [ ] `docker run` serves pages on port 80
- [ ] Health check passes: `curl http://localhost/health`

## Deployment Steps

### 1. GitHub Container Registry Setup

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and push (or let CI do it)
docker build -t ghcr.io/USERNAME/news-bot/frontend:latest ./frontend
docker push ghcr.io/USERNAME/news-bot/frontend:latest
```

### 2. Droplet Preparation

```bash
# SSH into droplet
ssh user@droplet-ip

# Install Docker if not present
curl -fsSL https://get.docker.com | sh

# Create Docker network
docker network create news-digest-network || true

# Ensure backend is running
docker ps | grep news-digest-api
```

### 3. Deploy Frontend Container

```bash
# Pull latest image
docker pull ghcr.io/USERNAME/news-bot/frontend:latest

# Stop existing container
docker stop news-digest-frontend || true
docker rm news-digest-frontend || true

# Run new container
docker run -d \
  --name news-digest-frontend \
  --restart unless-stopped \
  -p 80:80 \
  --network news-digest-network \
  ghcr.io/USERNAME/news-bot/frontend:latest

# Verify
docker ps
curl http://localhost/health
```

### 4. Configure Nginx (if using host Nginx)

```bash
# Copy nginx config
sudo cp nginx-proxy.conf /etc/nginx/sites-available/newsdigest
sudo ln -sf /etc/nginx/sites-available/newsdigest /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx

# Setup SSL
sudo certbot --nginx -d yourdomain.com
```

## Post-Deployment Verification

### Functional Tests

- [ ] Landing page loads at `https://yourdomain.com`
- [ ] Login page accessible at `/login`
- [ ] Registration works end-to-end
- [ ] Login stores token in localStorage
- [ ] Dashboard loads after login
- [ ] API calls work (check Network tab)
- [ ] Digest generation works
- [ ] Interests page updates preferences
- [ ] Logout clears session

### Performance Tests

- [ ] Page load time < 3s on 3G
- [ ] Lighthouse score > 80
- [ ] Gzip compression active (check response headers)
- [ ] Static assets cached (check Cache-Control headers)

### Security Tests

- [ ] HTTPS redirect works
- [ ] Security headers present (X-Frame-Options, etc.)
- [ ] No sensitive data in browser console
- [ ] JWT not exposed in URL

## Demo Data Setup

### Create Test User

```bash
curl -X POST http://api.yourdomain.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "DemoPass123",
    "full_name": "Demo User"
  }'
```

### Add Interests

```bash
# Login first
TOKEN=$(curl -s -X POST http://api.yourdomain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "DemoPass123"}' | jq -r '.access_token')

# Set interests
curl -X PUT http://api.yourdomain.com/users/me/interests \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"interest_slugs": ["technology", "science", "business"]}'
```

### Generate Sample Digest

```bash
curl -X POST http://api.yourdomain.com/digests/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

## Rollback Procedure

If deployment fails:

```bash
# On droplet
docker stop news-digest-frontend

# Run previous version
docker run -d \
  --name news-digest-frontend \
  --restart unless-stopped \
  -p 80:80 \
  --network news-digest-network \
  ghcr.io/USERNAME/news-bot/frontend:previous-tag
```

## Monitoring

### Container Health

```bash
# Check container status
docker ps

# View logs
docker logs -f news-digest-frontend

# Check resource usage
docker stats news-digest-frontend
```

### Nginx Logs

```bash
# Access logs
tail -f /var/log/nginx/access.log

# Error logs
tail -f /var/log/nginx/error.log
```

## Contacts

- **Backend Issues:** Check backend container logs
- **DNS Issues:** DigitalOcean control panel
- **SSL Issues:** Let's Encrypt / Certbot

---

Last updated: November 2025
