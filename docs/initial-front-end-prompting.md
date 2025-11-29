You are **Claude Opus 4.5**. Act as a senior full-stack frontend engineer. Your task: scaffold and implement a production-ready **Next.js + TypeScript + Tailwind + shadcn** frontend for the NewsDigest project using the exact constraints below. Produce a complete, copy/paste-ready file set and concise run/deploy commands. Target a static export (no Node server in production). Use React Context for auth/state. Store JWT in localStorage. Containerize the frontend and serve static files with Nginx on the same DigitalOcean droplet as the backend.

Do not add unrelated options. Do not ask clarifying questions. Assume the backend API described previously exists and is reachable at runtime under `http://backend:8000` within Docker Compose, and externally at `http://<droplet-ip>:8000` after deployment. Maintain production-level security and reliability.

---

## High-level constraints (use these exactly)

- Framework: Next.js (App Router allowed, but all pages must be compatible with `next export`).  
- Languages & UI: TypeScript, Tailwind CSS, shadcn/ui.  
- Auth: JWT in `localStorage`. React Context (`AuthProvider`) + `useAuth`.  
- Routes (Option B):  
  `/`, `/login`, `/register`, `/dashboard`, `/digest`, `/digest/[id]`, `/interests`, `/settings`.  
- Data fetching: **Hybrid for static export** — SSG for purely static pages, client-side fetching for all authenticated pages.  
- API base URL: `NEXT_PUBLIC_API_URL` env var.  
- Containerization: Multi-stage Dockerfile → static export → Nginx image serving `out/`.  
- Hosting: served from the same droplet behind Nginx.  
- CI: GitHub Actions that lint, test, build, and push the frontend image to GHCR.

---

## Deliverables (Claude must output each file exactly)

Claude must generate **all** of the following files, each inside a single master markdown block, with section headers:

1. `<FILE: package.json>`
2. `<FILE: tsconfig.json>`
3. `<FILE: next.config.js>` — with `output: "export"` and `images.unoptimized = true`.
4. `<FILE: tailwind.config.ts>`
5. `<FILE: postcss.config.js>`
6. `<FILE: styles/globals.css>`
7. `<FILE: app/layout.tsx>`
8. `<FILE: app/page.tsx>`
9. `<FILE: app/login/page.tsx>`
10. `<FILE: app/register/page.tsx>`
11. `<FILE: app/dashboard/page.tsx>`
12. `<FILE: app/digest/page.tsx>`
13. `<FILE: app/digest/[id]/page.tsx>`
14. `<FILE: app/interests/page.tsx>`
15. `<FILE: app/settings/page.tsx>`
16. `<FILE: src/lib/api.ts>`
17. `<FILE: src/context/AuthContext.tsx>`
18. `<FILE: src/hooks/useFetch.ts>`
19. `<FILE: public/robots.txt>`
20. `<FILE: public/favicon.ico>` (placeholder)
21. `<FILE: Dockerfile>` — full multi-stage Node build → Nginx static serve.
22. `<FILE: .dockerignore>`
23. `<FILE: nginx/nginx.conf>`
24. `<FILE: docker-compose.yml>`
25. `<FILE: docker-compose.override.yml>`
26. `<FILE: .env.local.example>`
27. `<FILE: .github/workflows/frontend-ci.yml>`
28. `<FILE: README.frontend.md>`
29. `<FILE: docs/nginx-proxy.md>`
30. `<FILE: frontend-checklist.md>`

---

## Implementation standards Claude must follow

- All dynamic pages use client-side fetch hooks.  
- Landing page uses SSG.  
- `AuthProvider` must manage token persistence, auto-logout on 401, and route guarding.  
- API client auto-injects Authorization header when token present.  
- UI uses Tailwind + shadcn components consistently.  
- No Next.js server runtime (`getServerSideProps` forbidden).  
- `next export` must work flawlessly.  
- Dockerfile must output a clean, minimal Nginx image.  
- GitHub Actions must build and push the container to GHCR.  

---

## Acceptance criteria

Claude must:

- Output **all files**, syntactically correct, in a single markdown code block.  
- Produce a frontend that builds successfully with:  
  `npm install && npm run build && npm run export`  
- Produce a Docker image that correctly serves the static site.  
- Produce CI that builds & pushes images to GHCR.  
- Provide a deployment-ready result.

---

## Output format

Claude must produce **one single markdown code block** containing all files, where each file begins with:

`<FILE: path>`

followed by the file content.

No explanations. No commentary. No backticks inside file contents.

Begin now.

---

# Fixing application local hosting prompt

---

You are Claude Opus 4.5.
Your task is to act as the principal engineer responsible for fully building, validating, and maintaining the NewsDigest project, which consists of:

1. A backend (FastAPI + Postgres + async SQLAlchemy + Redis optional + scheduler + workers)
2. A frontend (Next.js 14 + TypeScript + Tailwind + shadcn/ui)
3. A full Dockerized local environment (backend, frontend, Postgres, pgAdmin)
4. A unified deployment model via Docker Compose + Nginx reverse proxy on a single DigitalOcean droplet
5. Documentation, correctness, coverage, observability, and developer experience

Your outputs must be complete, correct, production-grade, and immediately runnable.

====================================================================
PROJECT CONTEXT
====================================================================

This project is NOT a commercial SaaS.
It is a personal, portfolio-grade application that I will demo to others.
Your job is to design and implement everything with strong engineering rigor but without unnecessary enterprise complexity.

====================================================================
BACKEND REQUIREMENTS
====================================================================

FastAPI backend with:

- async SQLAlchemy + Postgres 16
- Alembic migrations
- JWT Auth (HS256) stored on the frontend in localStorage
- NewsAPI + OpenAI integration
- request-ID middleware
- structured JSON logging
- rate limiting
- observability endpoints: /health, /health/db, /health/scheduler
- scheduler for digest generation
- worker for heavy async tasks
- complete test suite
- ASGI-compatible lazy loader fixed to:

class _LazyApp:
    _real_app = None

    def _get_app(self):
        if self._real_app is None:
            self._real_app = _create_app()
        return self._real_app

    def __getattr__(self, name):
        return getattr(self._get_app(), name)

    async def __call__(self, scope, receive, send):
        app = self._get_app()
        return await app(scope, receive, send)

Backend must run inside Docker Compose and pass healthchecks.

====================================================================
FRONTEND REQUIREMENTS
====================================================================

Stack:
Next.js 14 (App Router)
TypeScript
Tailwind CSS
shadcn/ui
JWT stored in localStorage
React Context for global auth state
Hybrid data fetching model
Route structure: OPTION B (nested routes)
Build as fully static export via "next export"
Serve static assets through Nginx inside the same droplet

Frontend pages:
/
login
register
dashboard
digest
digest/[id]
interests
settings

Protected pages redirect automatically when JWT is missing.

====================================================================
CONTAINERIZATION REQUIREMENTS
====================================================================

Docker Compose environment containing:
api
frontend
db (Postgres)
pgadmin (exposed at localhost:5050)
nginx proxy
internal network "news-digest-network"

Frontend served as static files by Nginx.
Backend on port 8000.
Nginx reverse proxy routes:
    /api → FastAPI backend
    / → Next.js exported static assets

====================================================================
DELIVERABLES CLAUDE MUST GENERATE
====================================================================

Claude must generate full, complete file contents for:

BACKEND:
- Entire FastAPI project structure
- All routers, schemas, services, models, workers
- Fixed main.py with ASGI-compatible lazy loader
- Alembic setup
- Dockerfile
- docker-compose.yml (including all services)
- docker-compose.override.yml
- logging config
- environment variables
- tests

FRONTEND:
- Complete Next.js 14 + TypeScript project
- App routes defined in OPTION B structure
- Tailwind + shadcn configuration
- AuthContext using localStorage
- API client abstraction
- Dockerfile
- Export configuration

INFRA:
- Nginx reverse proxy configuration
- pgAdmin configuration
- Networking and volumes

DOCUMENTATION:
- README.md
- deployment.md
- local development instructions

====================================================================
CLAUDE'S OPERATING RULES
====================================================================

1. Always output complete files with correct paths.
2. Ensure all services work with "docker compose up --build".
3. Validate import paths, environment variables, and health checks.
4. Maintain production quality but avoid overengineering.
5. Check ASGI signatures, circular imports, and connection strings.
6. When providing improvements, keep them minimal and practical.

====================================================================
FIRST TASK FOR CLAUDE
====================================================================

Your first task:

Generate the complete, final, runnable codebase for both the backend and frontend, including Docker, Nginx, pgAdmin, and documentation, according to all specifications above.

All output must be complete file contents, not fragments.
