# Add Docker, Observability, and CI/CD to the NewsDigest Backend  
Transform the existing FastAPI backend into a containerized, observable, continuously-deployed service.

## Requirements  
Implement all items below cleanly, idiomatically, and production-ready.

---

# 1. Dockerization (Backend API + Scheduler)

## A. Create a top-level `Dockerfile`
**Constraints**
- Python 3.12-slim base image  
- Copy project, install dependencies from `requirements.txt`  
- Create a non-root user  
- Expose port 8000  
- Use environment variables (no hard-coding)  
- Healthcheck included  
- Start server via:  
  `uvicorn src.main:app --host 0.0.0.0 --port 8000`  

**Required**  
- Multi-stage build (builder + final image)  
- Fast, cache-efficient layering  
- Proper `WORKDIR`, `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`  
- Use `--no-cache-dir` for pip  
- Add a `.dockerignore`  

---

## B. Create a top-level `docker-compose.yml`
**Services**
1. **api**
   - Build from local Dockerfile  
   - Depends on `db`  
   - Loads `.env` for secrets  
   - Maps port `8000:8000`  
   - Restart-policy: unless-stopped  
   - Connects to PostgreSQL via `DATABASE_URL` using host `db`  
2. **db**
   - Image: postgres:16  
   - Environment variables for DB name, user, password  
   - Persistent volume for data  
   - Healthcheck command  
3. **(Optional now, but scaffold)** `worker` or `scheduler` service  
   - For future externalization of scheduler  
   - Same image as API  
   - Runs a scheduler-only entrypoint  
   - Controlled by `SCHEDULER_ENABLED=true`  

---

# 2. Observability Additions

## A. Add `/health/db` Endpoint
Add a new endpoint that:
- Performs a real DB query (`SELECT 1`)  
- Returns JSON `{ status: "ok", latency_ms: <float> }`  

## B. Add `/health/scheduler` Endpoint
Returns:
- Scheduler enabled flag  
- Loaded jobs  
- Next run times  

## C. Add Structured Logging Improvements
- JSON logs for all services  
- Include request-id (generate uuid per request)  
- Include timestamp, level, message, module, request_path, client_ip  
- Scheduler logs prefixed with `"scheduler"`  

## D. Add Basic Docker Healthchecks
- API container healthcheck pings `/health`  
- DB container healthcheck uses native Postgres health command  

---

# 3. GitHub Actions CI/CD Pipeline

## A. Required Workflow Name
`.github/workflows/ci.yml`

## B. Pipeline Structure
### On Every Push/PR
1. Checkout  
2. Set up Python 3.12  
3. Install dependencies  
4. Run pytest:  
   ```
   pytest -q --disable-warnings --maxfail=1
   ```  
5. Upload coverage artifact  
6. Linting (ruff or flake8)

### On Push to `main`
1. Build Docker image  
2. Tag as:  
   - `latest`  
   - Git short SHA  
3. Push to GitHub Container Registry (GHCR)  
4. (Optional placeholder) Deployment step to DigitalOcean droplet  

---

# 4. Environment Variables

## A. Required
- `JWT_SECRET_KEY`  
- `NEWSAPI_KEY`  
- `OPENAI_API_KEY`  
- `DATABASE_URL`  
  - Example:  
    `postgresql+asyncpg://newsdigest:password@db:5432/newsdigest_db`

## B. Optional with Defaults
Implement all of these in Pydantic Settings:
`APP_NAME, APP_ENV, DEBUG, HOST, PORT, DB_POOL_SIZE, DB_MAX_OVERFLOW, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, OPENAI_MODEL, OPENAI_MAX_TOKENS, RATE_LIMIT_PER_MINUTE, RATE_LIMIT_BURST, LOG_LEVEL, LOG_FILE_PATH, CORS_ORIGINS, SCHEDULER_ENABLED, DIGEST_CHECK_INTERVAL_MINUTES`

---

# 5. Additional Implementation Rules

## A. Files Claude Must Generate
- `Dockerfile`  
- `.dockerignore`  
- `docker-compose.yml`  
- `kubernetes/` directory **placeholder only**  
- Updated settings module to ensure compatibility with environments  
- Updated logging module  
- New healthcheck endpoints  
- GitHub Actions workflow file  
- New documentation: `docs/deployment.md`

## B. Coding Style
- Clean, concise, production-oriented  
- No placeholders requiring you (the user) to fill in values  
- All components fully functional as delivered  
- Comments only where useful for maintainability  

---

# 6. Deliverable Format  
Provide **one unified answer** containing:  
1. The full Dockerfile  
2. The full docker-compose.yml  
3. The .dockerignore  
4. The GitHub Actions workflow  
5. Any modified source code (full files)  
6. New endpoints  
7. New docs  

Everything must be provided inside the final response.  
No inner code blocks or nested markdown fences.  
All code in top-level fenced blocks only.

---

# Context Summary (Do Not Repeat)
- Backend: FastAPI, Python 3.12  
- DB: PostgreSQL + async SQLAlchemy  
- Scheduler: APScheduler in-process  
- Deployment: DigitalOcean Docker host  
- CI/CD: GitHub Actions  
- App entry: `uvicorn src.main:app --host 0.0.0.0 --port 8000`  

---

Produce a complete, production-ready implementation.
