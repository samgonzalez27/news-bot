# Backend Architecture Document

## Overview

This document describes the architecture of the News Digest Backend API, a FastAPI-based service that generates personalized daily news digests for users based on their selected interests.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DigitalOcean Droplet                           │
│  ┌─────────────┐    ┌──────────────────────────────────────────────────┐   │
│  │   Nginx     │    │              FastAPI Application                  │   │
│  │  (HTTPS +   │───▶│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │   │
│  │   Reverse   │    │  │  Routers │──│ Services │──│  APScheduler │   │   │
│  │   Proxy)    │    │  └──────────┘  └──────────┘  └──────────────┘   │   │
│  └─────────────┘    │        │             │               │           │   │
│                     │        ▼             ▼               ▼           │   │
│                     │  ┌──────────────────────────────────────────┐   │   │
│                     │  │            PostgreSQL Database            │   │   │
│                     │  └──────────────────────────────────────────┘   │   │
│                     └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                      ▼
            ┌──────────────┐                      ┌──────────────┐
            │   NewsAPI    │                      │  OpenAI API  │
            │  (Headlines) │                      │   (GPT-4)    │
            └──────────────┘                      └──────────────┘
```

## Component Responsibilities

### 1. FastAPI Application (`main.py`)

The entry point that:
- Initializes the FastAPI app with metadata
- Registers all routers
- Configures CORS middleware
- Sets up exception handlers
- Manages application lifespan (startup/shutdown events)
- Starts/stops the APScheduler

### 2. Configuration (`config.py`)

Centralized settings management using Pydantic's `BaseSettings`:
- Loads environment variables from `.env`
- Validates required configuration
- Provides typed access to all settings
- Supports different environments (dev/staging/prod)

### 3. Database Layer (`database.py`)

SQLAlchemy async setup:
- Creates async engine with connection pooling
- Provides session factory
- Manages database lifecycle

### 4. Models (`models/`)

SQLAlchemy ORM models representing database tables:
- **User**: Account information, hashed password, preferences
- **Interest**: Available interest categories (predefined)
- **UserInterest**: Many-to-many relationship between users and interests
- **Digest**: Generated news digests with content and metadata

### 5. Schemas (`schemas/`)

Pydantic models for request/response validation:
- Request body validation with type hints
- Response serialization
- Automatic OpenAPI documentation

### 6. Routers (`routers/`)

FastAPI route handlers organized by domain:
- **auth.py**: Registration, login, token refresh
- **users.py**: Profile retrieval and updates
- **interests.py**: Interest selection and management
- **digests.py**: Digest retrieval and history

### 7. Services (`services/`)

Business logic layer (pure functions where possible):
- **auth_service.py**: Password hashing (argon2), JWT creation/validation
- **user_service.py**: User CRUD operations
- **interest_service.py**: Interest management
- **news_service.py**: NewsAPI client with caching
- **openai_service.py**: OpenAI chat completions for digest generation
- **digest_service.py**: Orchestrates news fetching and digest creation

### 8. Scheduler (`scheduler/`)

APScheduler configuration:
- **scheduler.py**: BackgroundScheduler instance, lifecycle management
- **jobs.py**: Job definitions for digest generation

### 9. Middleware (`middleware/`)

Custom FastAPI middleware:
- **rate_limiter.py**: Request rate limiting per IP/user

## Authentication Flow

```
┌──────────┐         ┌──────────────┐         ┌──────────────┐
│  Client  │         │   FastAPI    │         │  PostgreSQL  │
└────┬─────┘         └──────┬───────┘         └──────┬───────┘
     │                      │                        │
     │  POST /auth/register │                        │
     │─────────────────────▶│                        │
     │                      │  Hash password (argon2)│
     │                      │────────────────────────│
     │                      │  INSERT user           │
     │                      │───────────────────────▶│
     │                      │◀───────────────────────│
     │  201 Created         │                        │
     │◀─────────────────────│                        │
     │                      │                        │
     │  POST /auth/login    │                        │
     │─────────────────────▶│                        │
     │                      │  SELECT user           │
     │                      │───────────────────────▶│
     │                      │◀───────────────────────│
     │                      │  Verify password       │
     │                      │  Generate JWT          │
     │  200 OK + JWT token  │                        │
     │◀─────────────────────│                        │
     │                      │                        │
     │  GET /users/me       │                        │
     │  Authorization: Bearer <token>                │
     │─────────────────────▶│                        │
     │                      │  Validate JWT          │
     │                      │  Extract user_id       │
     │                      │  SELECT user           │
     │                      │───────────────────────▶│
     │  200 OK + user data  │◀───────────────────────│
     │◀─────────────────────│                        │
     │                      │                        │
```

### JWT Token Structure

```json
{
  "sub": "user_id_uuid",
  "exp": 1234567890,
  "iat": 1234567800,
  "type": "access"
}
```

- **Access Token Only**: Single token type for simplicity
- **Expiration**: 24 hours (configurable)
- **Algorithm**: HS256 with secret key from environment

## Digest Generation Flow

```
┌────────────────┐    ┌─────────────┐    ┌──────────┐    ┌────────────┐
│  APScheduler   │    │DigestService│    │NewsService│   │OpenAIService│
└───────┬────────┘    └──────┬──────┘    └─────┬────┘    └──────┬─────┘
        │                    │                 │                 │
        │ trigger job        │                 │                 │
        │───────────────────▶│                 │                 │
        │                    │                 │                 │
        │                    │ get users due   │                 │
        │                    │ for digest      │                 │
        │                    │                 │                 │
        │                    │ for each user:  │                 │
        │                    │                 │                 │
        │                    │ fetch headlines │                 │
        │                    │────────────────▶│                 │
        │                    │                 │ GET /top-headlines
        │                    │                 │──────▶ NewsAPI  │
        │                    │                 │◀──────          │
        │                    │◀────────────────│                 │
        │                    │                 │                 │
        │                    │ generate digest │                 │
        │                    │────────────────────────────────▶ │
        │                    │                 │   chat.completions
        │                    │                 │   ──────▶ OpenAI│
        │                    │                 │   ◀──────       │
        │                    │◀────────────────────────────────  │
        │                    │                 │                 │
        │                    │ save digest to DB                 │
        │                    │                 │                 │
        │◀───────────────────│                 │                 │
```

### Scheduling Strategy

1. **Job runs every 15 minutes** checking for users whose preferred delivery time falls within the current window
2. **24-hour delay**: News from `yesterday 00:00` to `yesterday 23:59` (due to NewsAPI free tier)
3. **Per-user digests**: Each user gets personalized content based on their interests
4. **Idempotency**: Check if digest already exists for date before generating

## Error Handling Strategy

### Exception Hierarchy

```python
class NewsDigestException(Exception):
    """Base exception for application"""
    pass

class AuthenticationError(NewsDigestException):
    """Authentication failures"""
    pass

class AuthorizationError(NewsDigestException):
    """Authorization/permission failures"""
    pass

class ValidationError(NewsDigestException):
    """Request validation failures"""
    pass

class ExternalAPIError(NewsDigestException):
    """External API failures (NewsAPI, OpenAI)"""
    pass

class DatabaseError(NewsDigestException):
    """Database operation failures"""
    pass
```

### HTTP Status Code Mapping

| Exception Type      | HTTP Status | Response Body                         |
| ------------------- | ----------- | ------------------------------------- |
| ValidationError     | 400         | `{"detail": "...", "errors": [...]}`  |
| AuthenticationError | 401         | `{"detail": "..."}`                   |
| AuthorizationError  | 403         | `{"detail": "..."}`                   |
| Not Found           | 404         | `{"detail": "..."}`                   |
| Rate Limited        | 429         | `{"detail": "...", "retry_after": n}` |
| ExternalAPIError    | 502         | `{"detail": "..."}`                   |
| Unexpected          | 500         | `{"detail": "Internal server error"}` |

### Error Response Format

```json
{
  "detail": "Human-readable error message",
  "error_code": "UNIQUE_ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z",
  "path": "/api/v1/resource",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

## Logging Architecture

### Log Levels

| Level    | Usage                               |
| -------- | ----------------------------------- |
| DEBUG    | Detailed debugging (dev only)       |
| INFO     | Normal operations, request/response |
| WARNING  | Recoverable issues, deprecations    |
| ERROR    | Errors that need attention          |
| CRITICAL | System failures                     |

### Log Format

```
%(asctime)s | %(levelname)-8s | %(name)s | %(message)s | %(extra)s
```

Example:
```
2024-01-15 10:30:45 | INFO     | news_service | Fetched 25 headlines | {"category": "politics", "user_id": "abc123"}
```

### Log Handlers

1. **StreamHandler**: stdout for container/systemd logs
2. **RotatingFileHandler**: `/var/log/news-digest/app.log`
   - Max file size: 10MB
   - Backup count: 5

## Rate Limiting

### Strategy

- **Per-IP rate limiting** for unauthenticated endpoints
- **Per-user rate limiting** for authenticated endpoints
- Implemented via custom middleware with in-memory storage (suitable for single-instance deployment)

### Limits

| Endpoint Category                  | Rate Limit                  |
| ---------------------------------- | --------------------------- |
| Auth (register/login)              | 5 requests/minute per IP    |
| API (authenticated)                | 60 requests/minute per user |
| Digest generation (manual trigger) | 1 request/hour per user     |

## Security Considerations

### Implemented Measures

1. **Password Hashing**: Argon2id with secure parameters
2. **JWT Security**: 
   - Short expiration (24h)
   - Secure secret key (256-bit minimum)
   - Algorithm pinned to HS256
3. **Input Validation**: Pydantic schemas for all inputs
4. **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
5. **Rate Limiting**: Prevent brute force and DoS
6. **HTTPS Only**: Nginx with Let's Encrypt
7. **Environment Secrets**: Never committed, loaded from `.env`
8. **CORS Configuration**: Restrictive origins in production

### Headers (via Nginx)

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## API Versioning

- **URL-based versioning**: `/api/v1/...`
- Current version: v1
- Future versions can coexist during migration periods

## Performance Considerations

### Database

- **Connection pooling**: SQLAlchemy async pool (5-20 connections)
- **Indexes**: On frequently queried columns (user_id, email, created_at)
- **Pagination**: All list endpoints paginated

### Caching

- **News headlines**: Cached for 1 hour (in-memory, per category)
- **User data**: No caching (always fresh from DB)

### Async Operations

- All database operations use async SQLAlchemy
- HTTP clients use `httpx` with async support
- Scheduler jobs run in thread pool to avoid blocking

## Deployment Architecture

```
                    ┌─────────────────────────────┐
                    │      DigitalOcean Droplet   │
                    │         (Ubuntu 22.04)      │
                    │                             │
  HTTPS (443) ─────▶│  ┌─────────────────────┐   │
                    │  │       Nginx          │   │
                    │  │  (Reverse Proxy +    │   │
                    │  │   SSL Termination)   │   │
                    │  └──────────┬──────────┘   │
                    │             │               │
                    │             ▼               │
                    │  ┌─────────────────────┐   │
                    │  │   Uvicorn + FastAPI │   │
                    │  │   (systemd service) │   │
                    │  │   Port 8000         │   │
                    │  └──────────┬──────────┘   │
                    │             │               │
                    │             ▼               │
                    │  ┌─────────────────────┐   │
                    │  │     PostgreSQL      │   │
                    │  │     Port 5432       │   │
                    │  └─────────────────────┘   │
                    │                             │
                    └─────────────────────────────┘
```

## File Structure Reference

```
src/
├── __init__.py
├── main.py                    # FastAPI app entry point
├── config.py                  # Pydantic settings
├── database.py                # SQLAlchemy setup
├── dependencies.py            # FastAPI dependencies
├── exceptions.py              # Custom exceptions
├── logging_config.py          # Logging setup
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── interest.py
│   └── digest.py
├── schemas/
│   ├── __init__.py
│   ├── user.py
│   ├── auth.py
│   ├── interest.py
│   └── digest.py
├── routers/
│   ├── __init__.py
│   ├── auth.py
│   ├── users.py
│   ├── interests.py
│   └── digests.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── user_service.py
│   ├── interest_service.py
│   ├── news_service.py
│   ├── openai_service.py
│   └── digest_service.py
├── scheduler/
│   ├── __init__.py
│   ├── scheduler.py
│   └── jobs.py
└── middleware/
    ├── __init__.py
    └── rate_limiter.py
```
