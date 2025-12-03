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
