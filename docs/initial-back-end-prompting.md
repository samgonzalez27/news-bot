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

---

# Fixing pytest issues

You are acting as a senior backend engineer helping diagnose and fix a FastAPI + pytest configuration issue. Provide deep reasoning and produce concrete patches.

## Summary of the Problem
Running `pytest` results in the following error:

ImportError while loading conftest:
ValidationError: 3 validation errors for Settings
jwt_secret_key — Field required
newsapi_key — Field required
openai_api_key — Field required

This occurs because `Settings()` (from Pydantic Settings) is being instantiated during import-time when pytest loads modules like `src/database.py` via `conftest.py`. Since pytest sets no environment variables by default, Pydantic raises missing-field validation errors and halts test collection.

## What You Must Do
1. Inspect the project’s configuration pattern (FastAPI + Pydantic Settings).  
2. Identify the exact cause of settings evaluation during module import.  
3. Redesign configuration loading to be **lazy, test-friendly, and import-safe**.  
4. Provide the correct fix using one or more of these approaches:
   - Lazy initialization pattern (only load settings inside functions or dependencies).
   - Provide a `TestSettings` class for pytest.
   - Set environment variables inside `conftest.py`.
   - Use FastAPI dependency overrides for configuration.
   - Refactor module imports so `Settings()` is not executed at import time.
5. Provide complete patched code for:
   - `src/config.py`
   - `tests/conftest.py`
   - Any other file that must be updated (e.g., `database.py`)
6. Provide explanations of:
   - Why this avoids early import errors
   - How the structure improves testability and correctness

Produce all output with staff-level engineering detail and clarity.

---

# Test Expansion Prompt

You are acting as a senior backend engineer responsible for expanding and tightening our FastAPI + Python + pytest test suite. The existing suite sits at ~90% coverage with 205 passing tests. Your task is to create the additional tests required to approach or achieve near-100% coverage across **all runtime surfaces**.

Your output must include:
- New test files  
- Updates to existing tests  
- Mocking strategies  
- Dependency overrides  
- Assertions for correct HTTP, logging, and behavior  
- Explanations of what each test adds to overall coverage  

No external APIs should be called. All tests must be deterministic, isolated, and fully self-contained.

---

## Project Context

The system includes:
- FastAPI app with multiple routers  
- Custom exception handlers  
- Settings via Pydantic  
- Service modules:
  - `auth_service`
  - `user_service`
  - `interest_service`
  - `digest` generator
  - `openai_service`
  - `news_service`
- APScheduler jobs
- JWT access token auth
- Rate limiter middleware  
- Logging system  
- Error classes for:
  - Authorization  
  - Validation  
  - External API failure  
  - Database errors  
  - Rate limit exceeded  

The remaining unconvered lines primarily include:
- Router bodies (async handlers)
- Exception handlers
- Rate limiter boundary conditions
- External API failure modes
- Scheduler misfire/error cases
- Configuration validation edge cases
- Authentication edge-case flows

All of these must be tested.

---

# Requirements

## 1. Router Handler Coverage

For **every route**, create tests for:

- Successful execution  
- Validation failures  
- Authentication missing  
- Authorization failure  
- Service-layer exceptions (mock service to raise each relevant error)  
- Response model validation  
- Logging side effects when applicable  

Use `AsyncClient` with an async context manager, e.g. the pattern below (adapt to your fixtures):

    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/some-route")

Override FastAPI dependencies via `app.dependency_overrides`.

Provide new or expanded tests in:

- `tests/test_routes_expanded.py`

---

## 2. Global Exception Handlers

Add tests for each custom exception, verifying:

- Correct status code  
- Correct JSON structure  
- Logging performed  
- Error handler path fully executed  

If necessary, define a temporary endpoint inside the test to raise the exception, for example:

    @app.get("/trigger_error")
    def trigger_error():
        raise AuthorizationError("Forced for test")

Expected new test file:

- `tests/test_exception_handlers.py`

---

## 3. Rate Limiter Boundary Testing

Test all edge conditions:

- First request of window → success  
- Exactly at the limit  
- Past the limit → 429  
- After window reset  
- Rapid-fire burst sequences  
- Multiple clients hitting the same route  

Mock time or use dependency override if the rate limiter depends on timestamps.

Expected test file:

- `tests/test_ratelimiter_edges.py`

---

## 4. External API Failure Mode Tests

Tests must simulate the following failure modes for external services. Use `respx`, `pytest_httpx`, or direct mocking of `httpx.AsyncClient` where appropriate.

NewsAPI scenarios:
- Invalid API key → 401  
- Timeout  
- Malformed or empty JSON  
- Network error  
- Rate limit error  
- Unexpected payload shape  

OpenAI scenarios:
- Timeout  
- Network error  
- Model not found  
- Rate limit error  
- Malformed response structure  

Expected test files:

- `tests/test_newsapi_failures.py`  
- `tests/test_openai_failures.py`

Each test must verify:
- Proper internal exception thrown by the service layer  
- Correct error handler response returned to the client  
- Logging emitted  
- No leakage of raw external error messages in API responses

---

## 5. APScheduler Edge Case Testing

Your tests should directly invoke scheduler job functions rather than relying on real-time scheduling behavior.

Test cases:
- Job misfire handling (if misfire_grace_time used)  
- Job raising an exception and being logged  
- Job retry or failure semantics, if implemented  
- Dependency failures inside jobs (e.g., DB unavailable)  
- Handling of malformed or unexpected data returned by services used in jobs

Expected file:

- `tests/test_scheduler_edges.py`

---

## 6. Settings & Configuration Validation

Test `Settings()` and configuration loading for:

- Missing required environment variables  
- Invalid data types (e.g., non-int where int expected)  
- Incorrect formats (URLs, JSON blobs)  
- Overridden test environment variables via `monkeypatch` or fixture  
- Optional variable fallback behavior

Expected file:

- `tests/test_settings_validation.py`

These tests must confirm that startup/config validation fails fast and predictably when invalid.

---

## 7. Authentication Edge Case Tests

Test JWT access token failure modes:

- Missing `Authorization` header  
- Wrong header format (e.g., "Basic ..." instead of "Bearer ...")  
- Expired token  
- Invalid signature (wrong signing key)  
- Tampered payload  
- Wrong issuer or audience if applicable  
- Wrong token type

Ensure the system:
- Rejects requests with appropriate status codes  
- Emits the correct error handler behavior and JSON schema

Expected file:

- `tests/test_auth_edge_cases.py`

---

# Required Output Structure

Your response must include:

## A. New test files
Provide full runnable code for:

- `tests/test_routes_expanded.py`  
- `tests/test_exception_handlers.py`  
- `tests/test_ratelimiter_edges.py`  
- `tests/test_newsapi_failures.py`  
- `tests/test_openai_failures.py`  
- `tests/test_scheduler_edges.py`  
- `tests/test_settings_validation.py`  
- `tests/test_auth_edge_cases.py`  

Each file must include:
- Fixtures (shared and per-test)
- Dependency overrides
- Mocks for external services
- Test cases covering success and failure paths
- Clear coverage of exception and success paths

---

## B. Updated existing tests

Patch existing test files to incorporate:
- Shared fixtures (DB session, test client, auth tokens)
- Mock factories for services
- Better test organization and naming
- Added tests for previously-uncovered router paths

---

## C. Centralized mocking utilities

Introduce a file such as `tests/mocks.py` with reusable mocks and helpers for:
- OpenAI client behavior (success, timeout, rate-limit)
- NewsAPI client behavior (success, 401, malformed JSON)
- Database session mocks / in-memory SQLite session
- User service behaviors and failures
- Auth token factories (create valid/expired/tampered tokens)

---

## D. Coverage Improvements Explanation

For each test file, include a concluding markdown comment block explaining:
- Newly covered lines and functions
- Why each test matters and what risk it reduces
- Which edge cases are sealed off
- Any future maintenance considerations

---

# Acceptance Criteria

- Near-100% coverage achieved or close to it, focusing on meaningful runtime surfaces  
- All router handlers, exception handlers, services, and failure paths exercised  
- Tests deterministic, isolated, and stable  
- No external network calls required  
- Production code changes only if absolutely necessary and documented  
- Test suite remains readable and maintainable  
- Explanations accompany all patches and new tests

---

# Deliverable Format

Produce your full output organized as follows:

- Explanation section describing strategy and fixtures
- Then file-by-file content blocks:

    <FILE: tests/test_routes_expanded.py>
    <complete code>

    <FILE: tests/test_exception_handlers.py>
    <complete code>

    ... continue for all test files ...

- Then updated existing files section (if any)
- Then `tests/mocks.py` factory code
- Then a coverage analysis summary block explaining what changed and what is now covered

The content must be ready for direct copy/paste into the repository.

