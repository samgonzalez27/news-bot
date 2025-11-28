# News Bot API Documentation

## Overview

The News Bot API is a RESTful backend service that provides personalized daily news digests. Users can register, select their interests, and receive AI-generated summaries of relevant news headlines.

**Base URL:** `/api/v1`

**Authentication:** Bearer token (JWT)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Users](#users)
3. [Interests](#interests)
4. [Digests](#digests)
5. [Health Check](#health-check)
6. [Error Responses](#error-responses)
7. [Rate Limiting](#rate-limiting)

---

## Authentication

### Register a New User

Create a new user account.

**Endpoint:** `POST /api/v1/auth/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe",
  "preferred_time": "08:00",
  "timezone": "America/New_York"
}
```

| Field          | Type   | Required | Description                                            |
| -------------- | ------ | -------- | ------------------------------------------------------ |
| email          | string | Yes      | Valid email address                                    |
| password       | string | Yes      | Min 8 chars, must contain letters and numbers          |
| full_name      | string | Yes      | User's display name (max 100 chars)                    |
| preferred_time | string | No       | Preferred digest time in HH:MM format (default: 08:00) |
| timezone       | string | No       | Valid timezone string (default: UTC)                   |

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "preferred_time": "08:00",
  "timezone": "America/New_York",
  "is_active": true,
  "interests": [],
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Login

Authenticate and receive an access token.

**Endpoint:** `POST /api/v1/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

## Users

All user endpoints require authentication via Bearer token.

### Get Current User Profile

**Endpoint:** `GET /api/v1/users/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "preferred_time": "08:00",
  "timezone": "America/New_York",
  "is_active": true,
  "interests": [
    {"id": "...", "name": "Technology", "slug": "technology"}
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Update Current User

**Endpoint:** `PATCH /api/v1/users/me`

**Request Body:** (all fields optional)
```json
{
  "full_name": "Jane Doe",
  "email": "newemail@example.com"
}
```

**Response:** `200 OK` (returns updated user object)

---

### Update User Preferences

**Endpoint:** `PATCH /api/v1/users/me/preferences`

**Request Body:** (all fields optional)
```json
{
  "preferred_time": "18:30",
  "timezone": "Europe/London"
}
```

**Response:** `200 OK` (returns updated user object)

---

### Deactivate Account

**Endpoint:** `DELETE /api/v1/users/me`

**Response:** `204 No Content`

---

## Interests

### List All Available Interests

Get all interests that users can subscribe to.

**Endpoint:** `GET /api/v1/interests`

**Authentication:** Not required

**Response:** `200 OK`
```json
{
  "interests": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Technology",
      "slug": "technology",
      "is_active": true
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "Science",
      "slug": "science",
      "is_active": true
    }
  ],
  "total": 12
}
```

---

### Get My Interests

Get the current user's subscribed interests.

**Endpoint:** `GET /api/v1/interests/me`

**Response:** `200 OK`
```json
[
  {"id": "...", "name": "Technology", "slug": "technology", "is_active": true},
  {"id": "...", "name": "Science", "slug": "science", "is_active": true}
]
```

---

### Update All Interests

Replace all user's interests with a new set.

**Endpoint:** `PUT /api/v1/interests/me`

**Request Body:**
```json
{
  "interest_slugs": ["technology", "science", "economics"]
}
```

**Response:** `200 OK` (returns list of subscribed interests)

---

### Add Single Interest

Add one interest to user's subscriptions.

**Endpoint:** `POST /api/v1/interests/me/{slug}`

**Example:** `POST /api/v1/interests/me/technology`

**Response:** `201 Created`
```json
{
  "id": "...",
  "name": "Technology",
  "slug": "technology",
  "is_active": true
}
```

---

### Remove Single Interest

Remove one interest from user's subscriptions.

**Endpoint:** `DELETE /api/v1/interests/me/{slug}`

**Example:** `DELETE /api/v1/interests/me/technology`

**Response:** `204 No Content`

---

## Digests

All digest endpoints require authentication.

### List User's Digests

Get paginated list of user's digest history.

**Endpoint:** `GET /api/v1/digests`

**Query Parameters:**

| Parameter | Type    | Default | Description             |
| --------- | ------- | ------- | ----------------------- |
| page      | integer | 1       | Page number             |
| per_page  | integer | 10      | Items per page (max 50) |

**Response:** `200 OK`
```json
{
  "digests": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "digest_date": "2024-01-15",
      "summary": "Today's top stories include breakthroughs in AI...",
      "created_at": "2024-01-15T08:00:00Z"
    }
  ],
  "total": 30,
  "page": 1,
  "per_page": 10,
  "pages": 3
}
```

---

### Get Latest Digest

Get the most recent digest for the current user.

**Endpoint:** `GET /api/v1/digests/latest`

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "digest_date": "2024-01-15",
  "content": "# Your Daily News Digest\n\n## Technology\n\n...",
  "summary": "Today's digest covers AI breakthroughs...",
  "headlines_used": [...],
  "interests_included": ["technology", "science"],
  "generation_time_ms": 2340,
  "created_at": "2024-01-15T08:00:00Z"
}
```

**Error:** `404 Not Found` if no digests exist

---

### Get Digest by Date

Get a specific digest by date.

**Endpoint:** `GET /api/v1/digests/by-date/{date}`

**Path Parameter:** `date` in YYYY-MM-DD format

**Example:** `GET /api/v1/digests/by-date/2024-01-15`

**Response:** `200 OK` (same format as latest digest)

---

### Generate Digest

Manually trigger digest generation for the current user.

**Endpoint:** `POST /api/v1/digests/generate`

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "digest_date": "2024-01-15",
  "content": "# Your Daily News Digest\n\n...",
  "summary": "Today's digest covers...",
  "headlines_used": [
    {"title": "...", "source": "...", "url": "..."}
  ],
  "interests_included": ["technology"],
  "generation_time_ms": 2340,
  "created_at": "2024-01-15T14:30:00Z"
}
```

---

## Health Check

### Get Application Health

**Endpoint:** `GET /health`

**Authentication:** Not required

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

| Code | Description                                      |
| ---- | ------------------------------------------------ |
| 400  | Bad Request - Invalid input data                 |
| 401  | Unauthorized - Missing or invalid authentication |
| 403  | Forbidden - Access denied                        |
| 404  | Not Found - Resource doesn't exist               |
| 409  | Conflict - Resource already exists               |
| 422  | Unprocessable Entity - Validation error          |
| 429  | Too Many Requests - Rate limit exceeded          |
| 500  | Internal Server Error                            |
| 503  | Service Unavailable - External API failure       |

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Rate Limiting

The API implements rate limiting to prevent abuse:

| Endpoint Type            | Limit              |
| ------------------------ | ------------------ |
| Authentication endpoints | 5 requests/minute  |
| All other endpoints      | 60 requests/minute |

When rate limited, you'll receive:

**Response:** `429 Too Many Requests`
```json
{
  "detail": "Rate limit exceeded. Try again in X seconds."
}
```

**Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705312800
```

---

## Interactive Documentation

When running locally, access interactive API documentation at:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`
