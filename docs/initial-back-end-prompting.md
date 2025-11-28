# Backend Development Prompt for Claude Opus 4.5

You are acting as a senior backend engineer responsible for designing and implementing a production-ready RESTful backend using **Python + FastAPI**.  
This project is a personal-scale but professionally architected application that generates a **daily previous-day news digest** for users based on their interests.  
You must apply professional SWE standards: clean architecture, atomic commits, thorough documentation, and high test coverage.

## Project Context

### Backend Responsibilities
- User account registration, login, and JWT **access-token-only** authentication  
- Secure password hashing (bcrypt or argon2)  
- Storing and updating user-selected interests (economics, politics, foreign affairs, sports, etc.)  
- Scheduling daily tasks via **APScheduler**  
- Pulling top headlines from **NewsAPI** (24-hour delay due to free plan limits)  
- Generating cohesive news digests via **OpenAI Chat Completions API**  
- Returning final content via the REST API to the front end  
- No notifications or email sending

### Digest Model
- A “**previous-day digest**”: every user selects a preferred delivery time, and the app compiles the news from the prior 24-hour window.

### Tech Stack
- **FastAPI**  
- **PostgreSQL**  
- **APScheduler** for scheduled jobs  
- Hosted on **DigitalOcean droplet**  
- NewsAPI + OpenAI API integrations  
- Use Python’s built-in `logging` module with:
  - stdout logging
  - a rotating file handler

### Security Requirements
- JWT access-token-only flow  
- Secure password hashing (bcrypt or argon2)  
- Pydantic request validation  
- Rate limiting (FastAPI middleware or Nginx-level)  
- HTTPS via Nginx + Let’s Encrypt  
- Secrets stored in `.env`, never committed

### Monitoring and Logging
- DigitalOcean monitoring for CPU/memory/disk  
- Application logs stored via Python logging: stdout + rotating file handler  
- Simple, readable, production-appropriate logging structure

### Testing Requirements
- **pytest**  
- Unit tests, integration tests, and end-to-end tests  
- Use `pytest-cov` but **no CI coverage gate**  
- Mock external APIs (NewsAPI, OpenAI)

### Architecture
- Production-ready but simple  
- Flat module structure (no DDD or multi-layer overengineering)  
- Keep separation of concerns clear  
- Highly readable code  
- Well-documented endpoints  
- Atomic commits throughout development

### Current Repository Layout
```
.
├── README.md
├── docs/
├── requirements.txt
├── src/
└── tests/
```

## What You Should Produce

You will act as the lead backend engineer and generate the following over time:

1. **Backend architecture plan**  
   - Final directory layout under `src/`  
   - How FastAPI, APScheduler, and database layers fit together  
   - JWT auth approach  
   - Models and schemas  
   - Service functions for NewsAPI + OpenAI  
   - Logging setup  
   - Error-handling strategy  

2. **Infrastructure setup**  
   - How to configure the DigitalOcean droplet  
   - How to run FastAPI with uvicorn + systemd  
   - Nginx reverse proxy + HTTPS  
   - Environment variable structure (`.env.example`)

3. **Database schema design**  
   - Users table  
   - Interests table or JSON field  
   - Scheduled-digest preferences  
   - Stored reports if needed

4. **Implementation of the backend**  
   - Complete FastAPI routes  
   - Authentication flow  
   - CRUD for user interests  
   - Scheduler job definitions  
   - News retrieval pipeline  
   - OpenAI report generation logic  
   - Logging configuration  
   - Error handlers

5. **API documentation**  
   - Each endpoint clearly documented  
   - Parameter descriptions  
   - Response schemas  
   - Error codes

6. **Testing suite**  
   - Unit tests for utilities and services  
   - Integration tests for endpoints using FastAPI TestClient  
   - E2E tests for full flow  
   - Mocking strategy for external APIs  
   - Achieve near-100% coverage

Your responses must be:
- Clear, structured, implementation-focused  
- Production-minded (security, maintainability, robustness)  
- Detailed enough for immediate coding  
- Delivered with senior-level reasoning when making design decisions  

Start by proposing the **finalized backend folder structure** inside `src/` based on all requirements above.  
Then proceed step-by-step through architecture, infrastructure, database schema, and implementation.

Do not generate frontend code.  
Do not simplify requirements.  
Produce work as if building a real, production-capable FastAPI service.
