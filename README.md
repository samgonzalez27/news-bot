# News Bot 📰

A production-ready FastAPI backend that delivers personalized daily news digests. Users select their interests, and the system fetches relevant headlines via NewsAPI and generates AI-powered summaries using OpenAI.

## Features

- **🔐 JWT Authentication**: Secure token-based auth with Argon2 password hashing
- **📊 Personalized Digests**: AI-generated summaries based on user interests
- **⏰ Scheduled Delivery**: Automatic digest generation at user-preferred times
- **🎯 Interest Management**: 12 predefined categories (Technology, Science, Economics, etc.)
- **📈 Rate Limiting**: Token bucket algorithm to prevent abuse
- **📝 Comprehensive Logging**: Structured logging with rotation
- **✅ Full Test Coverage**: Unit, integration, and E2E tests

## Tech Stack

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL with async SQLAlchemy
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose) + Argon2
- **Scheduler**: APScheduler
- **External APIs**: NewsAPI, OpenAI
- **Testing**: pytest, pytest-asyncio

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- NewsAPI key ([get one here](https://newsapi.org/))
- OpenAI API key ([get one here](https://platform.openai.com/))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/news-bot.git
cd news-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

### Database Setup

```bash
# Create PostgreSQL database
createdb newsbot

# Run migrations
alembic upgrade head
```

### Running the Application

```bash
# Development mode
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## API Documentation

Once running, access interactive docs at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

See [docs/api.md](docs/api.md) for detailed API documentation.

## Project Structure

```
news-bot/
├── alembic/                 # Database migrations
│   ├── versions/           # Migration files
│   └── env.py             # Alembic configuration
├── docs/                   # Documentation
│   ├── api.md             # API documentation
│   ├── architecture.md    # System architecture
│   ├── database-schema.md # Database design
│   └── infrastructure.md  # Deployment guide
├── src/                    # Application source code
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── routers/           # API endpoints
│   ├── middleware/        # Custom middleware
│   ├── scheduler/         # Background jobs
│   ├── config.py          # App configuration
│   ├── database.py        # DB connection
│   ├── dependencies.py    # FastAPI deps
│   ├── exceptions.py      # Error handling
│   └── main.py            # App entry point
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── e2e/               # End-to-end tests
│   └── conftest.py        # Pytest fixtures
├── .env.example           # Environment template
├── alembic.ini            # Alembic config
├── requirements.txt       # Dependencies
└── README.md
```

## Configuration

Key environment variables (see `.env.example` for all options):

| Variable                | Description                  | Default  |
| ----------------------- | ---------------------------- | -------- |
| `DATABASE_URL`          | PostgreSQL connection string | Required |
| `JWT_SECRET_KEY`        | Secret for JWT signing       | Required |
| `NEWSAPI_KEY`           | NewsAPI access key           | Required |
| `OPENAI_API_KEY`        | OpenAI API key               | Required |
| `SCHEDULER_ENABLED`     | Enable background jobs       | `true`   |
| `RATE_LIMIT_PER_MINUTE` | API rate limit               | `60`     |

## Available Interests

Users can subscribe to any combination of:

| Interest              | Category      |
| --------------------- | ------------- |
| Technology            | technology    |
| Science               | science       |
| Economics             | business      |
| World News            | general       |
| Politics              | politics      |
| Climate               | environment   |
| Health                | health        |
| Sports                | sports        |
| Entertainment         | entertainment |
| Startups              | startups      |
| AI & Machine Learning | ai            |
| Cryptocurrency        | crypto        |

## Deployment

See [docs/infrastructure.md](docs/infrastructure.md) for:

- DigitalOcean droplet setup
- Nginx reverse proxy configuration
- SSL/TLS with Let's Encrypt
- Systemd service configuration
- PostgreSQL production setup

## Development

### Code Style

```bash
# Format code (install ruff first)
ruff format src/ tests/

# Lint
ruff check src/ tests/
```

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## API Endpoints

| Method | Endpoint                         | Description          |
| ------ | -------------------------------- | -------------------- |
| POST   | `/api/v1/auth/register`          | Register new user    |
| POST   | `/api/v1/auth/login`             | Login and get token  |
| GET    | `/api/v1/users/me`               | Get current user     |
| PATCH  | `/api/v1/users/me`               | Update profile       |
| PATCH  | `/api/v1/users/me/preferences`   | Update preferences   |
| DELETE | `/api/v1/users/me`               | Deactivate account   |
| GET    | `/api/v1/interests`              | List all interests   |
| GET    | `/api/v1/interests/me`           | Get user's interests |
| PUT    | `/api/v1/interests/me`           | Set all interests    |
| POST   | `/api/v1/interests/me/{slug}`    | Add interest         |
| DELETE | `/api/v1/interests/me/{slug}`    | Remove interest      |
| GET    | `/api/v1/digests`                | List user's digests  |
| GET    | `/api/v1/digests/latest`         | Get latest digest    |
| GET    | `/api/v1/digests/by-date/{date}` | Get digest by date   |
| POST   | `/api/v1/digests/generate`       | Generate new digest  |
| GET    | `/health`                        | Health check         |

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
