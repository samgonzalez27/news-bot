# NewsDigest 📰

A full-stack application that delivers personalized AI-powered daily news digests. Users select their interests, and the system fetches relevant headlines via NewsAPI and generates intelligent summaries using OpenAI.

## Features

- **JWT Authentication** — Secure token-based auth with Argon2 password hashing
- **Personalized Digests** — AI-generated summaries based on user interests
- **Scheduled Delivery** — Automatic digest generation at user-preferred times (UTC)
- **Interest Management** — 8 predefined categories to choose from
- **Rate Limiting** — Token bucket algorithm to prevent abuse
- **Structured Logging** — JSON-formatted logs with request tracing
- **Full Test Coverage** — Unit, integration, and E2E tests (~640 tests)
- **Docker Ready** — One-command deployment with Docker Compose

## Tech Stack

### Backend
- **Framework**: FastAPI (async Python)
- **Database**: PostgreSQL 16 with async SQLAlchemy
- **Authentication**: JWT (python-jose) + Argon2
- **Scheduler**: APScheduler (AsyncIOExecutor)
- **External APIs**: NewsAPI, OpenAI

### Frontend
- **Framework**: Next.js 14 (App Router, static export)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui + Radix UI

### Infrastructure
- **Reverse Proxy**: Nginx
- **Containerization**: Docker Compose
- **Database Admin**: pgAdmin (optional)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- [NewsAPI key](https://newsapi.org/)
- [OpenAI API key](https://platform.openai.com/)

### Setup

```bash
# Clone the repository
git clone https://github.com/samgonzalez27/news-bot.git
cd news-bot

# Copy environment template and add your API keys
cp .env.example .env

# Start all services
docker compose up --build -d
```

Access the application:

| Service      | URL                     |
| ------------ | ----------------------- |
| Frontend     | http://localhost        |
| API Docs     | http://localhost/docs   |
| Health Check | http://localhost/health |
| pgAdmin      | http://localhost:5050   |

## Project Structure

```
news-bot/
├── src/                  # Backend source code
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── routers/          # API endpoints
│   ├── middleware/       # Rate limiting
│   ├── scheduler/        # Background jobs
│   └── main.py           # App entry point
├── frontend/             # Next.js frontend
│   ├── app/              # App Router pages
│   └── src/
│       ├── components/   # React components
│       ├── context/      # Auth context
│       └── lib/          # API client, types
├── tests/                # Backend test suite
├── nginx/                # Reverse proxy config
├── docs/                 # Documentation
└── docker-compose.yml    # Full stack definition
```

## Development

### Backend

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# All tests with coverage
pytest --cov=src --cov-report=term-missing

# Specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## API Endpoints

| Method | Endpoint                       | Description         |
| ------ | ------------------------------ | ------------------- |
| POST   | `/api/v1/auth/register`        | Register new user   |
| POST   | `/api/v1/auth/login`           | Login and get token |
| GET    | `/api/v1/users/me`             | Get current user    |
| PATCH  | `/api/v1/users/me/preferences` | Update preferences  |
| PUT    | `/api/v1/users/me/interests`   | Set user interests  |
| GET    | `/api/v1/interests`            | List all interests  |
| GET    | `/api/v1/digests`              | List user's digests |
| GET    | `/api/v1/digests/{id}`         | Get specific digest |
| POST   | `/api/v1/digests/generate`     | Generate new digest |

## Configuration

Key environment variables (see `.env.example` for all options):

| Variable            | Description                            | Required |
| ------------------- | -------------------------------------- | -------- |
| `JWT_SECRET_KEY`    | Secret for JWT signing (min 32 chars)  | Yes      |
| `NEWSAPI_KEY`       | NewsAPI access key                     | Yes      |
| `OPENAI_API_KEY`    | OpenAI API key                         | Yes      |
| `POSTGRES_PASSWORD` | Database password                      | Yes      |
| `SCHEDULER_ENABLED` | Enable background jobs (default: true) | No       |

## Available Interests

- 💼 Economics
- 🏛 Politics
- 🌍 Foreign Affairs
- ⚽ Sports
- 💻 Technology
- 🔬 Science
- 🏥 Health
- 🎬 Entertainment

## License

MIT
