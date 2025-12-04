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

---

# Fixing front-end Functionality Prompting

## Objectives

Analyze and fix the following **three critical defects** in a Next.js 14 + TypeScript + shadcn/ui + JWT auth + FastAPI backend stack. Your output must include:

- Root cause analysis  
- Exact code fixes (both frontend + backend if needed)  
- Required API call adjustments  
- React state fixes  
- Next.js routing corrections  
- Auth provider corrections  
- Data-fetching corrections  
- Logging instrumentation  
- End-to-end verification steps

Do NOT generate theory. Produce the concrete repairs.

---

## Defect 1 — Registration Works in Backend but Frontend Shows “registration failed – failed to fetch”

Observed behavior:
- User submits registration form with valid credentials.
- Backend **successfully creates the user** (verified by logging in right after).
- Frontend displays error toast: *"Registration failed – failed to fetch"*
- Behavior is **intermittent**, occurring even when backend logs show 200 OK responses.

Your tasks:
1. Identify and enumerate the **possible root causes**, with priority ordering:
   - CORS misconfiguration
   - Network request not awaited or swallowed error
   - Double-submit due to uncontrolled form
   - Navigating away before fetch resolves
   - Wrong `Content-Type`
   - Incorrect API URL construction (`NEXT_PUBLIC_API_URL`)
   - Nginx reverse proxy misrouting (for container mode)
   - Missing `return` in `handleRegister`
   - Missing `response.ok` handling
2. Show the exact rewritten frontend API request code that **guarantees**:
   - Correct await behavior  
   - Proper error branching  
   - Comprehensive error logging  
   - A single toast per error  
3. Provide the corrected implementation for the `/register` page including:
   - Controlled inputs  
   - Client-side validation  
   - Correct dependency usage from AuthProvider  
4. Provide the corrected CORS and Nginx config if they are contributing factors.

---

## Defect 2 — Landing Page Does Not Change UI After Login

Current behavior:
- When logged OUT: landing page correctly shows **Sign In** + **Start Free**.
- When logged IN: landing page still shows **Sign In** + **Start Free**, even though clicking them goes to the dashboard.

Your tasks:
1. Diagnose likely root causes:
   - AuthProvider not exposing correct `isAuthenticated`
   - Token missing or failing initial validation
   - Landing page rendered as static (SSG) instead of client component
   - Missing `use client` or incorrect use of server components
   - Failing hydration of auth state
2. Provide a fixed implementation for:
   - AuthProvider context state
   - JWT restore-from-localStorage logic
   - LandingPage component including conditional routing:
     - If logged in → show **Go to Dashboard** button  
     - If logged out → show **Sign In / Create Account** buttons
3. Provide a short verification list confirming correctness.

---

## Defect 3 — Digest Detail Page Always Returns “Digest Not Found”

Observed:
- Clicking a digest on `/dashboard` leads to:  
  `/digest/<id>`
- Page displays:
  - “Digest not found. This digest may have been deleted or doesn't exist.”
  - Toast “Failed to load digest”
- Even for **newly created digests**, always fails.

Your tasks:
1. Identify likely root causes:
   - Wrong route pathname (`/digest/` vs `/digests/`)
   - Wrong API request URL
   - Missing URL parameter parsing in Next.js route (`[id]/page.tsx`)
   - Incorrect `generateStaticParams` or static export mode preventing dynamic fetch
   - Trying to fetch API routes during build instead of client runtime
   - Backend digest GET endpoint returning 401 due to missing token
   - Token not forwarded in fetch headers
2. Provide:
   - Corrected Next.js page folder structure (App Router)
   - Corrected `useEffect` or `useQuery` digest fetch logic
   - Correct API client code including Authorization header
   - Correct backend GET handler example
3. Patch any build-time problems caused by `generateStaticParams` or accidental SSG.
4. Provide full corrected code for:
   - `/digest/[id]/page.tsx`
   - The digest fetch helper function
   - Any required backend route fixes

---

## Required Output Format

Produce **all of the following** in order:

### 1. Root-Cause Analysis for Each Problem  
Bullet list, specific, technical, no guesses.

### 2. Full Corrected Code  
Front-end and backend where needed, including:
- Registration page
- AuthProvider
- Landing page
- Digest detail page
- API helpers
- CORS settings
- Nginx rules (if affected)

### 3. End-to-End Flow Verification  
Describe exactly how the system behaves after fixes.

---

## Additional Constraints

- Use TypeScript conventions.
- Use React Server Components **only where safe**, otherwise apply `use client`.
- Ensure all auth-dependent pages are client components.
- JWTs stored in `localStorage`.
- No double-fetching.
- No static pre-rendering for user-specific data.
- Must assume containers are running behind Nginx.

---

## Final Deliverable

Produce a **complete repaired implementation** fixing all defects and restoring expected UX, with code blocks for each file requiring modification.

---

# Debugging Prompt — OpenAPI Auth + Swagger UI 401

You are a senior backend engineer. I need you to thoroughly debug and fix an authentication + Swagger UI integration problem in a FastAPI application behind NGINX. The issues revolve around missing OpenAPI securitySchemes, incorrect Swagger behavior, and mismatches between how authentication is implemented and how Swagger attempts to call protected endpoints.

## Context & Symptoms

- My FastAPI app has protected routes that require a JWT access token via an HTTP Bearer header.
- Authentication itself works correctly when calling the API manually with:
  Authorization: Bearer <token>
  (Postman and curl succeed.)
- When I generate a token through `/api/v1/auth/login`, Swagger’s “Try it out” tests always return 401, because the UI sends no Authorization header.
- In my codebase, there is **no OpenAPI securitySchemes defined** and no route-level `security=[...]`.
- Because of this, Swagger UI:
  - Shows no Authorize button
  - Never attaches JWTs to requests
  - Cannot test protected endpoints

### NGINX reverse proxy config (relevant section)
location /api/ {
    proxy_pass http://api_backend/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

There is no header stripping happening; authentication works fully outside Swagger.

## What I Need You To Produce

Deliver a complete, deeply reasoned fix that includes:

### 1. The correct FastAPI OpenAPI configuration
- Add a proper `securitySchemes` entry for HTTP Bearer.
- Add global `security=[{"bearerAuth": []}]` or per-route security declarations.
- Ensure Swagger UI’s Authorize button appears and functions.

### 2. Updated FastAPI code
Provide corrected, production-ready code for:
- security.py (or wherever your bearer scheme / OpenAPI components are defined)
- Any dependencies used for validating JWTs (e.g., `get_token_from_header`, `get_current_user`)
- main.py showing proper FastAPI initialization and swagger configuration
- Correct use of `dependencies=[Depends(get_current_user)]` for protected routes

### 3. Validation of the end-to-end flow
Ensure:
- Logging in generates a valid token.
- Clicking “Authorize” in Swagger stores the token.
- Swagger attaches `Authorization: Bearer <token>` to every protected request.
- The 401 errors disappear.
- NGINX path rewriting still routes `/api/*` cleanly to the backend.

### 4. Identify any hidden root causes
Provide concise senior-level reasoning for potential hidden causes, including:
- Incorrect token prefix (e.g., using "bearer" vs "Bearer")
- Wrong dependency injection or wrong dependency signature
- Missing `tokenUrl` settings in OpenAPI/security config
- OpenAPI not regenerating after code edits (timing/lifespan issues)
- Wrong path prefix (`/api/v1/...`) in swagger docs vs NGINX proxy path
- NGINX not forwarding `Authorization` header (recommend `proxy_set_header Authorization $http_authorization;`)

### 5. A fully corrected, clean, final version
Produce a complete and fully functioning corrected snippet for:
- `main.py` (full relevant sections to initialize OpenAPI security)
- `security.py` (bearer scheme + helpers)
- Any needed auth dependency functions
- Example protected route showing the security applied
- A sample Swagger request with the exact Authorization header that will succeed

## Requirements
- Provide explicit, copy-pastable code (not pseudocode).
- No partial patches — the code should be ready to commit.
- Explanations should be concise, senior-level, and actionable.
- If you detect additional auth-related issues or smells in the provided context, call them out and propose fixes.

## End
Produce the full fix now.

---

# Claude 4.5 Prompt — Fix Non-Persistent UI Switch State After Save (Visual Desync Issue)

You are a senior front-end engineer. I need you to diagnose and fix a **visual state desynchronization bug** affecting the Interest Settings page. The backend successfully saves updates, but **the UI switch components sometimes revert to their previous positions immediately after clicking “Save Changes.”** Reloading the page shows the correct, updated values—confirming the issue is front-end state handling, not backend logic.

## Context
- User toggles interest switches (ON/OFF).
- User clicks **Save Changes**.
- Frontend sends a successful PUT/PATCH request.
- Backend updates the database correctly.
- UI should reflect the updated state instantly.
- **Observed issue:** switch positions revert visually before showing saved values. This occurs inconsistently.

## Diagnosis Requirements
Identify and reason about all plausible causes of **front-end state desync**, including:
1. **Optimistic UI not synchronized** with backend response.
2. **Stale state closure** in React components or event handlers.
3. **Incorrect state derivation**: using props instead of authoritative state sources.
4. **Race conditions** between state updates, local UI updates, and incoming re-fetches.
5. **Asynchronous re-rendering** that overwrites updated UI values with old ones.
6. **Query library issues (React Query/SWR)** reloading stale cached data after mutation.
7. **Latency artifacts** due to sequential vs. parallel updates.
8. **Form library behavior** resetting values due to a re-render cycle.

## What I Need You to Produce

### 1. A complete root-cause analysis  
Explain exactly which pattern or anti-pattern is most likely responsible based on common switch-toggle behavior in SPAs.

### 2. A corrected state-management design  
Provide a definitive strategy for robust state synchronization, covering:
- How UI state should be sourced and updated.
- How Save Changes should update local state.
- How to prevent stale data from overwriting the UI.
- How to enforce exact correctness between backend → cache → UI.

### 3. Corrected code samples  
Provide **precise**, minimal, production-grade React code demonstrating:
- A properly controlled switch component.
- A mutation handler that updates both server data and local state deterministically.
- Cache invalidation or cache replacement flows (React Query or SWR).
- Prevention of race conditions and double state updates.

### 4. A fully stable post-save UX flow  
Deliver an improved interaction design that guarantees:
- Immediate visual confirmation of saved state.
- No flicker, no reversion of switches, no ambiguous UI states.
- Clear success/error handling.
- A defensively coded re-fetch process that cannot reintroduce stale values.

### 5. An implementation checklist  
Provide a final checklist addressing:
- Client-side authoritative state source
- Mutation → optimistic update → server reconciliation
- Cache invalidation strategy
- Prevention of unnecessary re-renders
- Ensuring consistent switch behavior across all browsers and latencies

## Deliverable
A full, senior-level, ready-to-implement solution that permanently eliminates the visual flip-back issue and guarantees an accurate, stable, predictable UI state immediately after saving changes.

---

# Claude 4.5 Prompt — Fix Next.js Build Error for Set Iteration in Interest Settings Page

You are a senior front-end engineer with expertise in React, Next.js, and TypeScript. We previously fixed a visual desync bug on the Interest Settings page using `Set<string>` to track selected interest slugs. That fix is correct functionally, but **the production build now fails**:

Error: 
Type 'Set<string>' can only be iterated through when using the '--downlevelIteration' flag or with a '--target' of 'es2015' or higher.  

## Context
- Project uses **Next.js 14** with **TypeScript**.
- `selectedSlugs` and `savedSlugsRef` are both `Set<string>`.
- We iterate over these Sets for functions like `computeHasChanges`:

for (const slug of current) { if (!saved.has(slug)) return true; }

- Local dev builds succeed; error occurs only during production build (Dockerized `next build`).
- TypeScript config may have `target: es5` or missing `downlevelIteration`.

## Diagnosis Requirements
1. Identify **why the build fails** despite the code working locally.
2. Explain **all ways to safely iterate Sets in TypeScript/Next.js** in production.
3. Determine **whether to adjust tsconfig, convert Sets to Arrays, or refactor iteration** for maximum compatibility without breaking state logic.
4. Ensure **all previous fixes to the switch desync bug remain intact**.

## Deliverables

### 1. Root-cause analysis
- Explain exactly why the `for...of` over `Set<string>` triggers a build-time TypeScript error.
- Cover differences between local dev compilation and production Docker build.

### 2. Corrected TypeScript-compatible implementation
- Rewrite `computeHasChanges` and any other iteration over `Set<string>` for full Next.js/TypeScript compatibility.
- Preserve `Set` usage for efficient membership checks (`has`) where appropriate.
- Ensure no visual desync or UX regressions occur.

### 3. Suggested tsconfig adjustments (if necessary)
- Explain trade-offs between setting `"target": "es2015"` vs `"downlevelIteration": true`.
- Provide recommended tsconfig snippet that will allow `Set` iteration safely in production.

### 4. Minimal, production-ready code sample
- Show a fully working, type-safe version of `computeHasChanges` and the toggle/save logic.
- Ensure it is compatible with Dockerized `next build` for Next.js 14 and TypeScript.

### 5. Implementation checklist
- Build passes with no TypeScript errors.
- UI state remains stable post-save.
- No regressions from previous fixes.
- Code is compatible across all browsers supported by Next.js project.

Goal: Produce a fully corrected, production-ready solution that fixes the `Set` iteration build error while maintaining the visual switch state stability previously implemented.

---

# Claude 4.5 Prompt — Fix Bullet-Point Formatting Issue in Markdown Preview

You are a senior front-end engineer with expertise in React and Markdown rendering. We have a **bullet-point formatting issue** in our project where the **first bullet of a section renders incorrectly in the preview**, but renders correctly in the full content view.

## Context
- `latestDigest.content` is rendered in **two ways**:
  1. **Preview renderer** (short snippet)
  2. **Full renderer** (entire content)
- Observed behavior:
  - **Preview:** first bullet has an extra line break, misaligned indentation.
  - **Full content:** bullets render correctly with `<li>` tags.
- Current implementation:
  - Preview:
    `.replace(/\n/g, '<br />')`  // happens BEFORE bullet handling
  - Full content:
    `.replace(/^\- (.*$)/gim, '<li>...</li>')`  

- The mismatch causes the **first bullet to wrap in unexpected `<br />` tags** before being converted to `<li>`.

## Diagnosis Requirements
1. Explain **why the first bullet in preview is misformatted** while others render correctly.
2. Identify **all regex, render order, and DOM transformation issues** causing this behavior.
3. Suggest a strategy to **unify preview and full content rendering** without breaking existing formatting.
4. Consider performance and maintainability when handling markdown transformations.

## Deliverables

### 1. Root-cause analysis
- Explain why `.replace(/\n/g, '<br />')` before bullet processing creates extra `<br>` on the first bullet.
- Cover differences between preview and full render paths.
- Identify any other potential edge cases (e.g., multiple consecutive bullets, nested bullets).

### 2. Corrected implementation
- Provide a **single, reusable `renderDigestMarkdown()` function** that works for both preview and full content.
- Ensure correct bullet rendering with `<li>` tags.
- Preserve line breaks, spacing, and other Markdown formatting.

### 3. Minimal, production-ready code sample
- Demonstrate how to process:
  - Newlines
  - Bullet points (`- item`)
  - Nested lists (if relevant)
- Show usage in both preview and full content rendering.

### 4. Implementation checklist
- First and subsequent bullets render correctly in preview and full content.
- No extra `<br />` tags on first bullet.
- Reusable, maintainable function.
- Compatible with existing CSS and text styling.

Goal: Deliver a robust, production-ready fix that ensures **consistent bullet-point rendering** across all Markdown views, eliminating first-bullet indentation issues.

---

# Claude 4.5 Prompt — Remove Quick Summary Card to Avoid Duplicate Executive Summary

You are a senior front-end engineer with expertise in React and UI rendering. We have a **duplication issue** in our digest component:

- `digest.summary` (Quick Summary) is derived from the Executive Summary text inside `digest.content`.
- As a result:
  - Quick Summary card displays the same text as the Executive Summary section.
  - Users see redundant content in the UI.

## Context
- `digest.content` contains the full markdown, including the Executive Summary.
- `digest.summary` is extracted via `_extract_summary()`:
  - Finds the Executive Summary line.
  - Returns the next line (same as text already in content).
- Current UI renders both:
  - Quick Summary card
  - Full digest with Executive Summary section

## Diagnosis Requirements
1. Confirm that Quick Summary card is redundant because its content duplicates the Executive Summary in `digest.content`.
2. Identify all components, templates, or rendering logic that reference `digest.summary`.
3. Ensure removing the Quick Summary card does **not break layout, styling, or other functionality**.

## Deliverables

### 1. Root-cause analysis
- Explain why the Quick Summary duplicates the Executive Summary.
- Identify any edge cases where removal could affect other UI parts.

### 2. Corrected implementation
- Remove the Quick Summary card entirely from all UI views.
- Ensure digest content still renders correctly.
- Maintain all existing styles and spacing for the remaining sections.

### 3. Minimal, production-ready code sample
- Show the updated component(s) with Quick Summary card removed.
- Include any adjustments to props, state, or template logic.

### 4. Implementation checklist
- Quick Summary card no longer appears in the UI.
- Executive Summary section remains intact and fully functional.
- No broken layout or styling regressions.
- Code is clean, maintainable, and compatible with current digest rendering logic.

Goal: Permanently eliminate the redundant Quick Summary card while keeping the Executive Summary fully visible and correctly formatted in the digest.

---

# Claude 4.5 Prompt — Remove Claude-Generated Header to Eliminate Date Mismatch in Digest

You are a senior front-end engineer specializing in content pipelines and markdown rendering. Our digest page is showing **two different dates** because the system mixes:

1. Our canonical date → `digest.digest_date`
2. A markdown header generated by you inside the digest content:
   `# Daily News Digest – [Date]`

This generates inconsistent output:
- UI header uses `digest.digest_date`
- Markdown header uses a different date that you generate internally

To fix this cleanly, we are choosing **Option C**:  
**Stop generating the internal header entirely.**  
The UI will supply its own header, and the markdown content should not include any date header.

## Requirements

### 1. Root-cause analysis
- Confirm why the duplicate dates occur.
- Identify all template or formatting sections of your output that introduce the markdown header.

### 2. Updated content-generation rules
Implement this change:

**Do not generate any top-level date header inside the digest content.**  
Specifically, remove lines such as:
`# Daily News Digest – …`

The UI will handle all header and date rendering externally.

### 3. Revised output specification
When generating a digest, follow these rules:
- Begin directly with the section structure (e.g., Executive Summary → Key Developments → etc.)
- Do not include any markdown `#` headers that represent the digest title or digest date.
- Do not infer or produce any date inside the markdown body.
- Assume the UI will prepend its own title and date outside of your generated markdown.

### 4. Provide corrected examples
Show before/after markdown structures:
- Before: markdown including a top-level header with a date.
- After: markdown starting directly with the Executive Summary section.

### 5. Implementation checklist
- No date appears anywhere inside the markdown you generate.
- No title header is produced.
- Digest begins at the Executive Summary section.
- All other sections remain unaffected.
- Output remains stable, consistent, and fully structured.

Goal: Produce a clean, date-neutral markdown digest so the UI-controlled header renders the only date shown to the user.

---

# Claude 4.5 Prompt — Restore Accurate Digest Date and Remove Incorrect UI Header Date

You are a senior engineer responsible for ensuring date accuracy and consistency in a news-digest pipeline. After implementing Option C earlier (removing the Claude-generated header), we uncovered a more fundamental problem:

**The date shown in the UI header (`Latest Digest – <date>`) is incorrect, while the date previously generated inside your markdown was actually the accurate one.**

Example of the issue:

- Digest content is based on articles from **November 30, 2025**.
- UI header shows: **Saturday, November 29, 2025** (incorrect).
- Previously, your markdown correctly showed: **Daily News Digest – November 30, 2025**.

Since we removed your internally generated header, we also accidentally removed the accurate date.  
We now need to reverse that decision in a controlled way.

## Goal
**Restore the Claude-generated digest date as the canonical authoritative date, and remove the UI-generated date that is currently misleading.**

## Requirements

### 1. Root-cause analysis
- Explain why the UI date (`digest.digest_date`) is inaccurate.
- Confirm why the date inside your generated markdown was actually correct (e.g., based on source article timestamps).
- Identify where in your output template the data-derived digest date belongs.

### 2. Updated date-handling rules
Implement the following:

**Rule A — Claude must once again generate the top-level digest header:**

Format:
`# Daily News Digest – <Full Month Name> <Day>, <Year>`

This date must:
- Reflect the date of the articles actually summarized.
- Be derived from the content, article metadata, or the digest_date passed into the prompt (if that value has already been corrected upstream).

**Rule B — The UI "Latest Digest – <date>" header must be removed entirely.**

The UI should no longer display its own date because it is producing inaccurate values.

Your generated header inside the markdown will be the **only** digest date displayed.

### 3. Revised output specification
When generating a digest:
- Start with the top-level header:
  `# Daily News Digest – <correct date>`
- Then continue with:  
  **Executive Summary → Key Developments → additional sections**
- Do not produce any second date inside the markdown.
- Do not rely on the UI to render the date.

### 4. Provide updated examples
Show:
- The corrected version including your restored header.
- What the UI should display (no date in UI header; date appears only in your markdown).

### 5. Implementation checklist
- Digest always displays exactly one authoritative date.
- That date always matches the underlying article set date.
- No secondary UI header date appears.
- Markdown begins with the restored digest header.
- All other content formats remain unchanged.
- Output is stable, predictable, and correct for all digest runs.

Goal: Produce a digest system where your generated markdown header provides the single, accurate, canonical date, eliminating misleading or incorrect UI-generated dates entirely.

---

# Formatting of Dates Fix - Claude Opus 4.5 Promp

You are assisting in debugging and correcting a deterministic news-digest generation pipeline. The pipeline consists of:

1. Backend date assignment
2. Input headline formatting
3. System prompt template for the LLM
4. LLM output formatting
5. Executive Summary extraction
6. Digest creation and storage (digest_date, created_at, summary, content)
7. Frontend rendering

A regression recently occurred during a date-mismatch fix. Instead of removing the incorrect digest, the system removed the correct one. As a result, a digest containing articles from November 30, 2025 is now labeled:

    Latest Digest – Saturday, November 29, 2025

The correct previous behavior was:

    Latest Digest – Saturday, November 29, 2025
    Daily News Digest – November 30, 2025

Your task is to:
- Identify the minimal change needed to restore the original behavior.
- Confirm that **Option A (digest_date = yesterday)** remains the enforced logic.
- Ensure that the digest_date always equals the intended “digest for yesterday,” regardless of article timestamps.
- Ensure that no logic accidentally substitutes the article publication date or generation date into the digest header.
- Ensure that the LLM output header always matches the digest_date passed into the system prompt.
- Validate that no trimming, cleaning, or whitespace normalization step alters the first two lines:
    # Daily News Digest – {digest_date}
    **Executive Summary:** …
- Audit for any source of newline insertion, backspace characters, stray whitespace, or markdown formatting anomalies, especially near the Executive Summary and the first bullet of the first category.
- Ensure that summary extraction does not mutate or remove the digest header lines.
- Verify that the system can safely “swap back” to the correct digest without introducing duplicates or overwriting legitimate digests.

Context and artifacts for analysis include:
- The system prompt controlling digest formatting.
- The function that formats headlines into category sections.
- The summary extraction logic using regular expressions.
- The digest_date defaulting behavior (date.today() - 1 day).
- The database schema containing digest_date and created_at.
- An example of a digest showing the formatting bug (the content provided in this prompt).
- An example of correct prior output showing proper date alignment.

Using the above, produce a concrete, step-by-step correction plan:
1. Identify the exact cause of the regression.
2. State the required changes to restore Option A behavior.
3. Provide specific code corrections (fully rewritten functions or blocks).
4. Provide a one-time remediation procedure to remove the incorrect digest and restore the correct one.
5. Provide safeguards to prevent the system from accidentally reversing digest order in future runs.
6. Validate final pipeline consistency by walking through a hypothetical generation cycle (system date Nov 30 → digest_date Nov 29 → NewsAPI returns Nov 30 headlines → digest must still say Nov 29).

All code blocks must be returned using only a single triple-backtick delimiter (no internal triple-backtick blocks). Output your final answer as a single markdown file.

---

# Front-end /Register Page Fix - Claude Prompt

You are helping diagnose and fix defects in a Next.js + FastAPI application’s /register workflow. The registration page shows inconsistent and misleading error notifications when creating the first user in a clean environment (fresh Docker container with no volumes). Your task is to identify the root cause and propose professional, production-grade fixes.

Observed issues:

1. When a new user registers (all fields correct), the client displays:
   "Registration failed – [object Object]"
   even though the request succeeds or partially succeeds.
2. In other cases, the UI displays:
   "Registration failed – Account created! go to the login page to login"
   even though the backend actually created the account successfully.
3. These issues occur primarily for the first user created in a clean environment.
4. Once the first user exists, creating a second user:
   - Does not show erroneous notifications
   - Automatically logs the user in and sends them directly to the dashboard, bypassing /login (unexpected behavior depending on design)
   - Suggests inconsistent response handling, race conditions, or improper auth-session creation logic after registration.

Your objectives:

1. Identify the root cause(s). Evaluate all plausible failure points:
   - Backend /register API response shape, status codes, and error-handling conventions
   - Frontend fetch/axios wrapper error parsing logic
   - JSON vs. non-JSON error payloads
   - Cases where the API returns 200 or 201 but includes an “error” structure
   - Next.js server action or client-side mutation logic that incorrectly treats success as failure
   - First-boot initialization behavior (e.g., first user becomes admin, triggers unique auth path, DB migrations not fully applied on first request, race conditions on DB creation)
   - Session or token logic that automatically creates a session on registration, bypassing the login page
   - Live deployment differences between first user vs. subsequent users
   - Any missing try/catch blocks that default to stringifying an error object → “[object Object]”

2. For every identified root cause, propose the exact fix:
   - Update to backend response model (success response must be stable, deterministic, and JSON-only)
   - Update to frontend error handling to properly distinguish:
       * Network failures
       * Validation failures
       * Backend business-logic failures
       * Actual successes
   - Remove any ambiguous “message” fields that mix success and failure in the same shape
   - Add explicit success branch and explicit redirect behavior
   - Prevent auto-login unless explicitly intended
   - Ensure the first-user creation path follows the same code as all later users

3. Provide a complete troubleshooting process:
   - Reproduce in a clean environment
   - Log raw backend responses (status, body, headers)
   - Log the frontend’s parsed error/success payload
   - Confirm whether the frontend’s `catch(error)` path is triggered due to a non-2xx code or an exception during JSON parsing
   - Confirm DB initialization timing and user-creation constraints

4. Provide all corrected code (frontend + backend) in a single triple-backtick block:
   - Corrected /register API route handler
   - Corrected status codes and return shapes
   - Corrected frontend submit handler with explicit branching and no ambiguous parsing paths
   - Corrected redirect behavior
   - Optional: a minimal testing script demonstrating correct behavior in a fresh container

5. Include a final section describing validation steps:
   - Test plan for creating the first user in a clean container
   - Test plan for creating subsequent users
   - Verification that no erroneous notifications ever appear
   - Verification that auto-login occurs only if intended by specification

Deliverables:
- Root cause analysis
- Professional-grade fixes
- Updated code
- A clear test/validation plan

---

# Claude Prompt Used to Fix Front-end Routing

You are an expert in Next.js 14 (App Router), SSR/CSR boundaries, route segment rendering, caching, and deployment diagnostics. Fix the following production bug:

Problem:
- Reloading /dashboard/ renders the landing-page UI instead of the dashboard UI.
- The URL stays at /dashboard/.
- This only occurs on hard reloads or direct navigation.
- Client-side navigation works correctly.
- The project uses Next.js App Router, server components for most pages, and a custom middleware.ts.

Your Tasks:
1. Identify all root causes that can make Next.js serve the wrong route tree on reload.
   Include:
   - Misconfigured routing structure (e.g., nested layouts, default.js, intercepting routes).
   - Middleware rewriting conditions that redirect non-matching paths to /(landing) unintentionally.
   - Issues with static rendering, prerender caching, or improperly cached HTML.
   - Deploy environment configuration errors (Vercel, Node, container) that cause fallback HTML to be returned.
   - Wrong export or default-export collisions.
   - Missing `dynamic = "force-dynamic"` where required.

2. Provide a step-by-step diagnostic workflow with exact file checks:
   - app/dashboard/page.tsx
   - app/dashboard/layout.tsx
   - app/page.tsx
   - app/(marketing)/page.tsx (if applicable)
   - middleware.ts rewrite/redirect logic
   - next.config.js experimental flags
   - `.next` build output structure
   - Vercel routes config (if applicable)

3. Provide targeted code fixes with minimal edits.
   Examples:
   - Correcting middleware rewrite conditions.
   - Adjusting segment config: `export const dynamic = "force-dynamic"` or removing static generation.
   - Fixing layout nesting issues.
   - Removing conflicting default routes.
   - Ensuring dashboard is not pre-rendered into static HTML.

4. Provide a final “Implementation Patch” containing the corrected middleware, route structure, and config variants.

Deliver the answer as a structured, authoritative technical breakdown with full reasoning and code blocks.
