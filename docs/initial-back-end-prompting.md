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

---

# Achieving 100% Coverage in the Testing Suite

Your task is to fix the full FastAPI test suite, eliminate all async warnings, and raise total coverage to 100%. Do not add unrelated options. Do not ask clarifying questions. Assume the backend containers build and run successfully.

---

## Existing Problems You Must Solve

- Multiple "coroutine was never awaited" warnings caused by using AsyncMock on synchronous SQLAlchemy Session methods.
- Several router modules are below required coverage (40–80%).
- Missing branch coverage in:
  - config.py
  - logging_config.py
  - main.py
  - rate_limiter.py
  - database.py
  - Routers: auth, users, interests, digests, health
- Missing exception-path tests:
  - External API failures (OpenAI + NewsAPI mocked)
  - Database operational errors
  - Authentication/authorization flows
  - Validation errors
  - Scheduler job failures
- Missing verification of:
  - Logging side effects
  - Response model correctness
  - Rate limiter edge cases
- All external integrations must be mocked and deterministic.

---

## High-Level Requirements (use exactly these)

- Replace all incorrect AsyncMock usage with MagicMock for synchronous SQLAlchemy calls (Session.add, Session.commit, etc.).
- Use AsyncMock only for true async functions.
- Achieve 100% coverage for:
  - All routers
  - All services
  - Exception handlers
  - Rate limiter middleware
  - Scheduler jobs
  - Config and logging
- For every route, create tests for:
  - Success
  - Validation failure
  - Missing auth
  - Wrong auth
  - Not found
  - Conflict
  - Service-layer exceptions
  - External API exceptions
  - Response model schema validation
- Mock the following:
  - openai_service.generate_digest
  - news_service.fetch_articles
  - Any outbound HTTP requests
  - SQLAlchemy session failures
  - Scheduler job failures
- Rate limiter tests must include:
  - Allowed request
  - Blocked request
  - Bucket reset behavior
  - Burst edge case
- Scheduler tests must include:
  - Successful job execution
  - Misfire
  - Raised exception
  - Logging asserts

---

## Output You Must Generate

### 1. New and updated test suites
Provide all missing test files and updated tests to remove warnings and close coverage gaps.

### 2. Correct mocking strategy
Document exactly which items use MagicMock vs AsyncMock and how patches should be applied.

### 3. Detailed explanations
Explain what each new test covers and why the async warnings disappear.

### 4. Final deliverable
A complete, corrected test suite with:
- Full 100% coverage
- Zero async warnings
- Deterministic, isolated tests
- No external API calls
- Validated response models
- Full router/service/exception/rate-limit/scheduler coverage

---

## Environment Assumptions

- Python 3.11
- FastAPI
- SQLAlchemy ORM
- Pytest + pytest-asyncio
- HTTPX AsyncClient
- Coverage run with: pytest --disable-warnings --maxfail=1 --cov=app --cov-report=term-missing
- Test DB + dependency overrides already functional
- No network requests allowed

---

## Your Task

Generate the final corrected test suite, close all remaining branches, fix all async warnings, and produce a fully green 100% coverage run.

---

# Fix CI Linter and Test Failures - Prompt

You are a senior Python engineer. I need you to fix our CI so that all tests pass when code is pushed to GitHub. Our CI uses Ruff for linting, and GitHub is failing because of 10 Ruff violations. I need a fully reasoned plan and concrete code fixes that permanently eliminate these linter errors.

## Current Ruff Errors

### E712 — Avoid comparing with `True`
Files containing this issue:
- src/services/interest_service.py:43:31
- src/scheduler/jobs.py:53:20
- src/scheduler/jobs.py:62:20

These lines currently look like:
if something == True:
They must become:
if something:
or, where applicable:
if model.is_active:

### F401 — Unused imports
Ruff reports unused imports in:
- src/services/digest_service.py:7:31 — typing.List
- src/scheduler/jobs.py:6:32 — datetime.time
- src/routers/users.py:5:20 — typing.List
- src/routers/users.py:11:34 — InterestResponse
- src/middleware/rate_limiter.py:10:26 — typing.Optional
- src/main.py:20:32 — get_logger
- src/dependencies.py:12:49 — NotFoundError

These must be removed unless they should actually be used. If a missing usage is a real bug (e.g., logger intended to be used), the code should be corrected instead of deleting the import.

## What I Need You To Produce

I want a complete, senior-level, commit-ready fix addressing all 10 Ruff errors.

### 1. Identify exact code fixes per file  
Specify precisely what needs to change for each file and show corrected code blocks or corrected lines.

### 2. Decide remove vs. use for imports  
Determine whether to:
- Remove the unused import, or  
- Restore its intended usage (e.g., logging, validation, raising errors).

### 3. Provide corrected code snippets  
Produce fully corrected versions of the affected sections with no broken context.

### 4. Ensure functional integrity  
Confirm:
- No tests break  
- No regression is introduced  
- All unused imports are removed or used correctly  
- All E712 violations are fixed using the correct model attributes  
- Formatting remains Ruff-compliant

### 5. Improve CI stability  
If necessary:
- Refine ruff.toml  
- Adjust GitHub Actions workflow so linting/test steps run in a stable, reproducible environment  
- Confirm pytest path resolution and dependency installation  
- Recommend adding pre-commit hooks using Ruff + Black

### 6. Provide the final patched code  
Supply final corrected versions of:
- interest_service.py  
- digest_service.py  
- scheduler/jobs.py  
- routers/users.py  
- middleware/rate_limiter.py  
- main.py  
- dependencies.py  

The output must be commit-ready and clean.

## Deliverables

1. Clear explanations for each Ruff error.  
2. Exact corrected lines or full corrected blocks.  
3. A final “no remaining Ruff violations” checklist.  
4. Optional improvements to prevent recurrence.

Produce the complete solution now.

---

# Fix CI Errors - Claude Prompt

You are assisting with diagnosing and fixing continuous-integration failures in a Python project using GitHub Actions. The CI pipeline runs Ruff linting and unit tests. The workflow is currently failing due to Ruff errors. Your task is to provide a complete, professional debugging and remediation plan.

Context:

GitHub Actions Output:
Annotations  
2 errors  
Test & Lint  
Process completed with exit code 1.

Ruff error:
F401 (unused import)  
File: tests/unit/test_markdown_sanitizer.py  
Line 5  
`pytest` imported but unused

Objectives:

1. Identify the root cause of the failure, including:
   - Whether `pytest` is actually required for side-effects or markers in that test file
   - Whether Ruff is correctly configured to allow or disallow unused imports in test files
   - Whether a fixture, decorator, or expected exception block implicitly requires pytest
   - Whether the test file structure incorrectly imports unused modules

2. Propose the best professional fix based on project standards:
   - Remove the unused `pytest` import if truly unnecessary
   - Or update the test to explicitly use pytest functionality if the import is needed
   - Or update Ruff configuration (if intentional) by:
       * Allowing unused pytest imports in tests, OR
       * Adding per-file ignores, OR
       * Adding noqa annotations to the specific line
   Choose the fix that aligns with sound engineering practices, not quick patches.

3. Explain whether this Ruff error is the only reason the CI failed or if additional cascading issues may occur:
   - Confirm if Ruff exits on first error
   - Confirm whether subsequent tests passed or were skipped
   - Recommend running Ruff and pytest locally to reproduce CI behavior:
       * `ruff check .`
       * `pytest -q`

4. Provide corrected code in a triple-backtick block with the right option implemented:
   - If removing the import, show the cleaned test file
   - If adding usage, show the updated test
   - If using configuration, show the updated `pyproject.toml` snippet or noqa tag

5. Provide a clean, explicit validation plan:
   - Steps to run Ruff locally and verify zero lint errors
   - Steps to commit and push to trigger CI
   - Expected GitHub Actions output when fixed

Deliverables:
- Root cause analysis
- Correct fix
- Updated code/configuration
- Validation plan

---

# Add Timezone and Time Back-end Logic for /settings Page - Claude Prompt

You are updating the `/settings` page of a Next.js 14 (App Router) application. Your task is to fully implement and fix the **Digest Delivery** card, which is currently non-functional and visually inconsistent with the rest of the app.

Your objective is to professionally repair and complete this feature end-to-end. Follow these instructions precisely.

===================================================
PROJECT CONTEXT
===================================================
The Digest Delivery section currently has:
- A **Preferred Delivery Time** time-picker dropdown  
- A **Timezone** dropdown listing IANA timezones  
- A **Save Changes** button  

Current problems:
1. **Neither dropdown works.**  
   Selecting a timezone does not update state.  
   Selecting a time does not update state.

2. **Nothing is persisted.**  
   Changing the dropdowns does NOT make any API call, even after clicking Save.

3. **Styling does not match the rest of the UI.**  
   The time-picker and timezone dropdown are basic, unstyled, and visually disconnected.

4. **Expected behavior is simple and minimal:**  
   • Users may freely change the time or timezone.  
   • **No API calls are made until the user clicks “Save Changes.”**  
   • When Save is clicked, the frontend must send ONE PATCH request:  

     PATCH /users/me/preferences
     Content-Type: application/json  
     {
       "preferred_time": "<HH:MM in UTC>",
       "timezone": "America/New_York"
     }

5. **Important technical requirement:**  
   We store `preferred_time` internally in **UTC** only.  
   If the user selects 8:00 AM in America/Chicago, you must convert this to the correct HH:MM UTC time before PATCHing.

===================================================
YOUR TASK
===================================================
You must professionally diagnose and fix all root causes. Provide code and reasoning for:

1. **State Management**  
   - Ensure controlled React state for both fields.  
   - Timezone state must update immediately on selection.  
   - Time state must update immediately on selection.

2. **Time Conversion Logic**  
   - Convert local time → UTC HH:MM string reliably.  
   - Avoid DST pitfalls.  
   - Use a stable library (luxon or dayjs with timezone plugin).  
   - Ensure the UI always shows the “local” time while the backend receives UTC.

3. **API Integration**  
   - Implement the single PATCH request fired ONLY on “Save Changes.”  
   - Give complete Next.js App Router-compatible code for:  
     - The component  
     - The onSubmit handler  
     - The fetch call  
   - Handle both success and failure professionally.

4. **Styling Improvements**  
   - Rewrite the dropdowns so they match the app’s design system (classNames, spacing, typography).  
   - Include hover/active/focus states.  
   - Make the timepicker visually consistent with common UI libraries.

5. **Edge Cases**  
   - First render with existing preferences (if any).  
   - Midnight edge cases (“12:00 AM” vs “00:00”, UTC conversion).  
   - Invalid timezone fallback.

6. **Final Output**  
   Provide a **drop-in replacement** for the Digest Delivery card containing:
   - Fully working JSX  
   - Fully working time conversion logic  
   - Fully working Save button behavior  
   - Clean styling  
   - Specific notes about where to integrate with our backend  
   - Zero pseudocode  
   - No guesses or vague statements
