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
