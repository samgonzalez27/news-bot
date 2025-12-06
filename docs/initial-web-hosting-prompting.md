# Role
You are a senior full-stack engineer.

# Objective
Produce a complete, professional deployment plan for hosting our application on a DigitalOcean droplet.

# Context
- The application is ready for distribution.
- Use this reference repository as an authoritative guide: https://github.com/kaw393939/mywebclass_hosting/tree/master  
- Assume you have full access to inspect that repository’s structure, scripts, deployment patterns, and recommended setup.
- Your goal is to identify every technical step required to deploy the app reliably, securely, and maintainably.

# Requirements

## 1. Reference Analysis
Analyze the reference repository and infer the deployment model it expects, including:
- Nginx reverse proxy configuration  
- Application runtime (Python, Node, etc.)  
- Gunicorn/Uvicorn, PM2, or other process managers  
- SSL provisioning  
- Environment variable handling  
- Directory layout and service files  

## 2. Droplet Preparation
Determine all steps required to prepare a fresh Ubuntu droplet:
- OS updates and security hardening  
- Installation of system dependencies  
- Installation of runtimes (Python, Node, or both)  
- Package managers  
- Web server setup  
- Reverse proxy configuration  
- Process manager or systemd unit files  

## 3. Deployment Procedure
Provide a clean, linear, start-to-finish deployment procedure usable on a brand-new droplet.

## 4. Implementation Details
Include detailed instructions for:
- Cloning the repo  
- Project environment configuration  
- Build or compilation steps  
- Managing static assets  
- Database setup (if applicable)  
- Firewall configuration  
- SSL/TLS setup (Let’s Encrypt or equivalent)  
- Operational commands: restarting services, viewing logs, updating code, enabling systemd services  

## 5. Reliability & Security
Identify potential issues and provide best-practice recommendations.

## 6. Output Format
Deliver everything as a clearly structured, professional deployment **runbook**.

# Constraint
Do not ask me questions. The output must be fully actionable on a new DigitalOcean droplet with no prior configuration.

---

# Fix Deployment Issues - Claude Prompt

You are acting as a senior DevOps engineer. Analyze and fix the following DigitalOcean deployment failure that occurred during our GitHub Actions CI pipeline when pushing to main:

## Error Log
error: The following untracked working tree files would be overwritten by merge:
    docker-compose.prod.yml
Please move or remove them before you merge.
Updating cb099f0..55d6e23
Aborting
Error: Process completed with exit code 1.

## Context
1. Deployment target is an Ubuntu 24.04 DigitalOcean droplet.
2. The CI pipeline SSHes into the droplet, runs `git pull`, then rebuilds Docker services.
3. The repository contains a tracked file named `docker-compose.prod.yml`.
4. The droplet already has a non-tracked `docker-compose.prod.yml` created manually in earlier testing.
5. When the pipeline runs `git pull`, Git halts because the untracked file conflicts with the tracked one coming from the repo.

## Objectives
1. Identify the exact root cause of the failure.
2. Propose a clean, production-safe fix that prevents this error permanently.
3. Provide updated CI steps if appropriate.
4. Provide updated server-side setup instructions if appropriate.
5. Consider best practices for:
   - Ensuring the droplet always has a clean working directory.
   - Preventing manual server edits from blocking future Git pulls.
   - Ensuring Docker Compose production files always come from GitHub as source of truth.
6. Deliver a final recommended approach for long-term stability.

## Deliverables
1. A precise explanation of why Git aborted the pull.
2. Three possible solutions, each with pros/cons.
3. A recommended production solution with exact commands.
4. Updated GitHub Actions deploy job if needed.

---

# Fix Connection Error Issues Upon Deployment - Claude Prompting

You are acting as a senior DevOps/SRE engineer. We have a production outage: the public domain `dailydigestbot.com` returns **ERR_CONNECTION_REFUSED**, even after cache clearing and browser resets. The issue persists across devices and networks.

## Facts
1. Claude previously tested the server:
   - Direct IP (45.55.141.61) returned HTTP 200.
   - Domain resolved correctly and returned HTTP 200.
   - DNS records for `A` root and `www` pointed to 45.55.141.61.
2. Despite that, **real users cannot connect to `http://dailydigestbot.com`**.
3. The domain still fails after:
   - Ctrl+Shift+R hard reload
   - Incognito mode
   - Browser change
   - Multiple physical devices
4. The server was modified in the most recent deployment.
5. Docker Compose is used for production; the API and frontend run inside containers.

## Required Diagnosis Tasks
Investigate all plausible causes for a domain-based **ERR_CONNECTION_REFUSED**, including:

### Networking
- Whether the server is binding only to `localhost` or an internal interface.
- Whether Docker services expose ports publicly or only internally.
- Whether UFW, iptables, or DigitalOcean firewall blocks port 80 or 443.

### Nginx / Reverse Proxy
- Whether Nginx is running.
- Whether Nginx is listening on the expected ports.
- Whether Nginx is forwarding traffic to the correct container/service.
- Whether the latest deployment overwrote or removed the Nginx config.

### Docker
- Whether the frontend container is actually running.
- Whether the service is mapped with `ports:` and not only `expose:`.
- Whether health checks fail and cause the service to restart repeatedly.

### DNS
- Whether DNS propagation changed.
- Whether DNS is resolving via IPv6 (AAAA) when only IPv4 is served.
- Whether the root domain correctly serves traffic without redirect loops.

## Deliverables
1. A ranked list of the most likely root causes based on the symptoms.
2. Exact Linux commands I should run on the droplet to confirm each cause.
3. Recommendations for what to check inside Docker (docker ps, logs, compose configs).
4. If the failure is likely due to Nginx, provide a correct production-safe config.
5. A final recommended fix with exact commands.

## Goal
Produce a structured, step-by-step, minimally ambiguous debugging plan to restore public access to `http://dailydigestbot.com` and prevent future connection-refused outages.

---

# Re-attempt at Fixing Connection Issues - Prompt

You are acting as a senior DevOps/SRE engineer. Your task is to identify the root cause of a production deployment failure. The domain is dailydigestbot.com, hosted on a DigitalOcean droplet running multiple Docker containers behind an nginx-alpine reverse proxy. The site currently returns ERR_CONNECTION_REFUSED from external browsers, even though DNS resolves correctly and Docker shows ports 80 and 443 exposed.

Available facts:
- DNS A record for dailydigestbot.com points to 45.55.141.61 and resolves correctly.
- Docker ps confirms an nginx-alpine container exposing 0.0.0.0:80->80/tcp and 0.0.0.0:443->443/tcp.
- ss -tulpn on host shows listeners on ports 80 and 443.
- DigitalOcean firewall has now been created; inbound ports 80 and 443 are allowed.
- The project includes a frontend, backend, and nginx reverse proxy container.
- The site does not load over HTTP or HTTPS from the public internet.
- Browser error: “ERR_CONNECTION_REFUSED”.
- We suspect a misconfiguration in one of: nginx config, listen/bind directives, upstream routing inside Docker, SSL/redirect config, DigitalOcean firewall assignment, droplet-level firewall rules, or container-level health.

Your goal:
1. Analyze potential root causes based on the architecture and symptoms.
2. Provide a structured step-by-step diagnostic plan to isolate the failure.
3. Provide the exact commands to run inside the droplet and inside the nginx container (curl tests, nginx -t, log paths, netstat/ss checks, docker exec checks, and minimal static web test).
4. Identify the most likely root causes given the evidence.
5. Provide the most efficient fix strategies for each likely root cause.
6. Provide a fallback “minimal working configuration” for nginx inside Docker to confirm external connectivity.

Your output must be:
- Highly technical.
- Structured into clear numbered sections.
- Focused only on root causes, diagnosis, and concrete fixes.
- Written as if actively guiding a DevOps engineer during a production incident.

Begin.
