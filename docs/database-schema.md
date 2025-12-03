# Database Schema Design

## Overview

This document describes the PostgreSQL database schema for the News Digest application. The schema is designed to be simple, normalized where appropriate, and optimized for the application's query patterns.

## Entity Relationship Diagram

```
┌─────────────────────┐       ┌─────────────────────┐
│       users         │       │     interests       │
├─────────────────────┤       ├─────────────────────┤
│ id (PK, UUID)       │       │ id (PK, UUID)       │
│ email (UNIQUE)      │       │ name (UNIQUE)       │
│ hashed_password     │       │ slug (UNIQUE)       │
│ full_name           │       │ description         │
│ preferred_time      │       │ created_at          │
│ timezone            │       └──────────┬──────────┘
│ is_active           │                  │
│ created_at          │                  │
│ updated_at          │                  │
└──────────┬──────────┘                  │
           │                             │
           │         ┌───────────────────┘
           │         │
           ▼         ▼
┌─────────────────────────────┐
│      user_interests         │
├─────────────────────────────┤
│ user_id (PK, FK)            │
│ interest_id (PK, FK)        │
│ created_at                  │
└─────────────────────────────┘
           │
           │
           ▼
┌─────────────────────────────┐
│        digests              │
├─────────────────────────────┤
│ id (PK, UUID)               │
│ user_id (FK)                │
│ digest_date (DATE)          │
│ content (TEXT)              │
│ summary (TEXT)              │
│ headlines_used (JSONB)      │
│ interests_included (JSONB)  │
│ status                      │
│ created_at                  │
│ updated_at                  │
└─────────────────────────────┘
```

## Table Definitions

### 1. users

Stores user account information and preferences.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    preferred_time TIME NOT NULL DEFAULT '08:00:00',
    -- timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',  -- Disabled: all users use UTC
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_preferred_time ON users(preferred_time);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);
```

**Column Descriptions:**

| Column            | Type            | Description                                        |
| ----------------- | --------------- | -------------------------------------------------- |
| `id`              | UUID            | Primary key, auto-generated                        |
| `email`           | VARCHAR(255)    | User's email address, used for login               |
| `hashed_password` | VARCHAR(255)    | Argon2id hashed password                           |
| `full_name`       | VARCHAR(100)    | User's display name                                |
| `preferred_time`  | TIME            | Preferred digest delivery time (user's local time) |
| ~~`timezone`~~    | ~~VARCHAR(50)~~ | ~~IANA timezone~~ (disabled - all users use UTC)   |
| `is_active`       | BOOLEAN         | Whether the account is active                      |
| `created_at`      | TIMESTAMPTZ     | Account creation timestamp                         |
| `updated_at`      | TIMESTAMPTZ     | Last update timestamp                              |

### 2. interests

Stores predefined interest categories. This is a reference table populated at application startup.

```sql
CREATE TABLE interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    newsapi_category VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index
CREATE INDEX idx_interests_slug ON interests(slug);
CREATE INDEX idx_interests_is_active ON interests(is_active);
```

**Column Descriptions:**

| Column             | Type        | Description                                  |
| ------------------ | ----------- | -------------------------------------------- |
| `id`               | UUID        | Primary key                                  |
| `name`             | VARCHAR(50) | Display name (e.g., "Economics")             |
| `slug`             | VARCHAR(50) | URL-friendly identifier (e.g., "economics")  |
| `description`      | TEXT        | Brief description of the category            |
| `newsapi_category` | VARCHAR(50) | Corresponding NewsAPI category if applicable |
| `is_active`        | BOOLEAN     | Whether this interest is currently available |
| `display_order`    | INTEGER     | Order for display in UI                      |
| `created_at`       | TIMESTAMPTZ | Creation timestamp                           |

**Predefined Interests:**

| Name            | Slug            | NewsAPI Category         |
| --------------- | --------------- | ------------------------ |
| Economics       | economics       | business                 |
| Politics        | politics        | general + keyword filter |
| Foreign Affairs | foreign-affairs | general + keyword filter |
| Sports          | sports          | sports                   |
| Technology      | technology      | technology               |
| Science         | science         | science                  |
| Health          | health          | health                   |
| Entertainment   | entertainment   | entertainment            |

### 3. user_interests

Junction table for the many-to-many relationship between users and interests.

```sql
CREATE TABLE user_interests (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    interest_id UUID NOT NULL REFERENCES interests(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, interest_id)
);

-- Indexes
CREATE INDEX idx_user_interests_user_id ON user_interests(user_id);
CREATE INDEX idx_user_interests_interest_id ON user_interests(interest_id);
```

**Column Descriptions:**

| Column        | Type        | Description                       |
| ------------- | ----------- | --------------------------------- |
| `user_id`     | UUID        | Foreign key to users table        |
| `interest_id` | UUID        | Foreign key to interests table    |
| `created_at`  | TIMESTAMPTZ | When the user added this interest |

### 4. digests

Stores generated news digests for users.

```sql
CREATE TABLE digests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    digest_date DATE NOT NULL,
    content TEXT NOT NULL,
    summary VARCHAR(500),
    headlines_used JSONB NOT NULL DEFAULT '[]',
    interests_included JSONB NOT NULL DEFAULT '[]',
    word_count INTEGER,
    generation_time_ms INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, digest_date)
);

-- Indexes
CREATE INDEX idx_digests_user_id ON digests(user_id);
CREATE INDEX idx_digests_digest_date ON digests(digest_date);
CREATE INDEX idx_digests_status ON digests(status);
CREATE INDEX idx_digests_user_date ON digests(user_id, digest_date DESC);
CREATE INDEX idx_digests_created_at ON digests(created_at);
```

**Column Descriptions:**

| Column               | Type         | Description                                |
| -------------------- | ------------ | ------------------------------------------ |
| `id`                 | UUID         | Primary key                                |
| `user_id`            | UUID         | Foreign key to users table                 |
| `digest_date`        | DATE         | The date the news is from (previous day)   |
| `content`            | TEXT         | Full digest content (Markdown formatted)   |
| `summary`            | VARCHAR(500) | Brief summary/headline of the digest       |
| `headlines_used`     | JSONB        | Array of headline objects used to generate |
| `interests_included` | JSONB        | Array of interest slugs included           |
| `word_count`         | INTEGER      | Word count of the digest                   |
| `generation_time_ms` | INTEGER      | Time taken to generate (milliseconds)      |
| `status`             | VARCHAR(20)  | Status: pending, completed, failed         |
| `error_message`      | TEXT         | Error message if generation failed         |
| `created_at`         | TIMESTAMPTZ  | When the digest was created                |
| `updated_at`         | TIMESTAMPTZ  | Last update timestamp                      |

**Status Values:**

- `pending`: Digest generation is in progress
- `completed`: Digest was successfully generated
- `failed`: Digest generation failed (see error_message)

**JSONB Schema for `headlines_used`:**

```json
[
  {
    "title": "Article headline",
    "source": "Source name",
    "url": "https://...",
    "published_at": "2024-01-15T10:00:00Z",
    "category": "politics"
  }
]
```

**JSONB Schema for `interests_included`:**

```json
["politics", "economics", "technology"]
```

## Migration Strategy

### Initial Migration (001_initial.sql)

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    preferred_time TIME NOT NULL DEFAULT '08:00:00',
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create interests table
CREATE TABLE interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    newsapi_category VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create user_interests junction table
CREATE TABLE user_interests (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    interest_id UUID NOT NULL REFERENCES interests(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, interest_id)
);

-- Create digests table
CREATE TABLE digests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    digest_date DATE NOT NULL,
    content TEXT NOT NULL,
    summary VARCHAR(500),
    headlines_used JSONB NOT NULL DEFAULT '[]',
    interests_included JSONB NOT NULL DEFAULT '[]',
    word_count INTEGER,
    generation_time_ms INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, digest_date)
);

-- Create indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_preferred_time ON users(preferred_time);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

CREATE INDEX idx_interests_slug ON interests(slug);
CREATE INDEX idx_interests_is_active ON interests(is_active);

CREATE INDEX idx_user_interests_user_id ON user_interests(user_id);
CREATE INDEX idx_user_interests_interest_id ON user_interests(interest_id);

CREATE INDEX idx_digests_user_id ON digests(user_id);
CREATE INDEX idx_digests_digest_date ON digests(digest_date);
CREATE INDEX idx_digests_status ON digests(status);
CREATE INDEX idx_digests_user_date ON digests(user_id, digest_date DESC);
CREATE INDEX idx_digests_created_at ON digests(created_at);
```

### Seed Data (002_seed_interests.sql)

```sql
INSERT INTO interests (name, slug, description, newsapi_category, display_order) VALUES
    ('Economics', 'economics', 'Business, markets, and economic news', 'business', 1),
    ('Politics', 'politics', 'Political news and policy updates', 'general', 2),
    ('Foreign Affairs', 'foreign-affairs', 'International relations and global news', 'general', 3),
    ('Sports', 'sports', 'Sports news and updates', 'sports', 4),
    ('Technology', 'technology', 'Tech industry and innovation news', 'technology', 5),
    ('Science', 'science', 'Scientific discoveries and research', 'science', 6),
    ('Health', 'health', 'Health, medicine, and wellness news', 'health', 7),
    ('Entertainment', 'entertainment', 'Entertainment and celebrity news', 'entertainment', 8);
```

## Database Initialization

The application uses direct table creation via SQLAlchemy's `Base.metadata.create_all()` in the `init_db()` function, rather than migration tools. This approach is suitable for the current project scope.

**Database setup:**
- Tables are created automatically on application startup if they don't exist
- Interest seeding is handled by `seed_interests()` function
- For schema changes, update the models and recreate the database (or manually alter tables in production)

## Query Patterns

### Common Queries

**1. Get user with interests:**
```sql
SELECT u.*, array_agg(i.slug) as interests
FROM users u
LEFT JOIN user_interests ui ON u.id = ui.user_id
LEFT JOIN interests i ON ui.interest_id = i.id
WHERE u.id = $1
GROUP BY u.id;
```

**2. Get users due for digest at current time:**
```sql
SELECT u.id, u.email, u.preferred_time, u.timezone,
       array_agg(i.slug) as interests
FROM users u
JOIN user_interests ui ON u.id = ui.user_id
JOIN interests i ON ui.interest_id = i.id
WHERE u.is_active = TRUE
  AND u.preferred_time >= $1  -- current time window start
  AND u.preferred_time < $2   -- current time window end
  AND NOT EXISTS (
      SELECT 1 FROM digests d
      WHERE d.user_id = u.id
      AND d.digest_date = $3  -- yesterday's date
  )
GROUP BY u.id;
```

**3. Get user's digest history:**
```sql
SELECT id, digest_date, summary, status, created_at
FROM digests
WHERE user_id = $1
ORDER BY digest_date DESC
LIMIT $2 OFFSET $3;
```

**4. Get specific digest:**
```sql
SELECT *
FROM digests
WHERE user_id = $1 AND digest_date = $2;
```

## Performance Considerations

### Index Strategy

1. **Primary lookups**: UUID primary keys with default indexes
2. **Email lookups**: Index on `users.email` for login queries
3. **Time-based queries**: Index on `preferred_time` for scheduler
4. **Digest retrieval**: Composite index on `(user_id, digest_date DESC)` for history

### Connection Pooling

- Min connections: 5
- Max connections: 20
- Connection timeout: 30 seconds
- Idle timeout: 300 seconds

### JSONB Considerations

- `headlines_used` and `interests_included` use JSON for cross-database compatibility (SQLite in tests)
- PostgreSQL still provides good performance with JSON type
- Keep JSON fields reasonably sized (< 1MB per row)

## Backup Strategy

### Recommended Approach

1. **Daily automated backups** via `pg_dump`
2. **Retain 7 daily backups**
3. **Weekly backup retained for 4 weeks**
4. **Store backups in DigitalOcean Spaces or local encrypted storage**

### Backup Command

```bash
pg_dump -Fc -h localhost -U newsdigest newsdigest_db > backup_$(date +%Y%m%d).dump
```

### Restore Command

```bash
pg_restore -h localhost -U newsdigest -d newsdigest_db backup_20240115.dump
```
