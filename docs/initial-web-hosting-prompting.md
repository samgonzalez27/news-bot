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

