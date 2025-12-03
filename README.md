# NewsDigest 📰

A full-stack, production-ready application that delivers personalized AI-powered daily news digests. Users select their interests, and the system fetches relevant headlines via NewsAPI and generates intelligent summaries using OpenAI.

## ✨ Features

- **🔐 JWT Authentication**: Secure token-based auth with Argon2 password hashing
- **📊 Personalized Digests**: AI-generated summaries based on user interests
- **⏰ Scheduled Delivery**: Automatic digest generation at user-preferred times
- **🎯 Interest Management**: 8 predefined categories (Technology, Science, Economics, etc.)
- **📈 Rate Limiting**: Token bucket algorithm to prevent abuse
- **📝 Structured Logging**: JSON-formatted logs with request tracing
- **✅ Full Test Coverage**: Unit, integration, and E2E tests
- **🐳 Docker Ready**: One-command deployment with Docker Compose

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL 16 with async SQLAlchemy
- **Authentication**: JWT (python-jose) + Argon2
- **Scheduler**: APScheduler
- **External APIs**: NewsAPI, OpenAI

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui + Radix UI
- **Build**: Static export

### Infrastructure
- **Reverse Proxy**: Nginx
- **Containerization**: Docker Compose
- **Database Admin**: pgAdmin

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- NewsAPI key ([get one here](https://newsapi.org/))
- OpenAI API key ([get one here](https://platform.openai.com/))

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/news-bot.git
cd news-bot

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys

# Start everything
docker compose up --build
```

That's it! Access the application at:

| Service          | URL                     |
| ---------------- | ----------------------- |
| **Frontend**     | http://localhost        |
| **API Docs**     | http://localhost/docs   |
| **Health Check** | http://localhost/health |
| **pgAdmin**      | http://localhost:5050   |

### Default Credentials

- **pgAdmin**: admin@newsdigest.local / admin
- **Database**: newsdigest / newsdigest_secret

## 📖 Project Structure

```
news-bot/
├── src/                    # Backend source code
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── routers/           # API endpoints
│   ├── middleware/        # Rate limiting, etc.
│   ├── scheduler/         # Background jobs
│   └── main.py            # App entry point
├── frontend/              # Next.js frontend
│   ├── app/              # App Router pages
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── context/      # Auth context
│   │   ├── hooks/        # Custom hooks
│   │   └── lib/          # API client, types
│   └── nginx/            # Frontend nginx config
├── nginx/                 # Reverse proxy config
├── tests/                # Backend test suite
├── docs/                 # Documentation
├── docker-compose.yml    # Full stack definition
└── .env.example          # Environment template
```

## 🔧 Development

### Backend Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn src.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Running Tests

```bash
# Backend tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Frontend tests
cd frontend && npm test
```

## 🌐 API Endpoints

| Method | Endpoint                       | Description         |
| ------ | ------------------------------ | ------------------- |
| POST   | `/api/v1/auth/register`        | Register new user   |
| POST   | `/api/v1/auth/login`           | Login and get token |
| GET    | `/api/v1/users/me`             | Get current user    |
| PATCH  | `/api/v1/users/me/preferences` | Update preferences  |
| GET    | `/api/v1/interests`            | List all interests  |
| PUT    | `/api/v1/users/me/interests`   | Set user interests  |
| GET    | `/api/v1/digests`              | List user's digests |
| GET    | `/api/v1/digests/{id}`         | Get specific digest |
| POST   | `/api/v1/digests/generate`     | Generate new digest |
| GET    | `/health`                      | Health check        |
| GET    | `/health/db`                   | Database health     |
| GET    | `/health/scheduler`            | Scheduler status    |

## ⚙️ Configuration

Key environment variables (see `.env.example` for all options):

| Variable            | Description                           | Required           |
| ------------------- | ------------------------------------- | ------------------ |
| `JWT_SECRET_KEY`    | Secret for JWT signing (min 32 chars) | ✅                  |
| `NEWSAPI_KEY`       | NewsAPI access key                    | ✅                  |
| `OPENAI_API_KEY`    | OpenAI API key                        | ✅                  |
| `POSTGRES_PASSWORD` | Database password                     | ✅                  |
| `SCHEDULER_ENABLED` | Enable background jobs                | No (default: true) |
| `LOG_LEVEL`         | Logging level                         | No (default: INFO) |

## 📋 Available Interests

Users can subscribe to any combination of:

- 💼 Economics
- 🏛 Politics
- 🌍 Foreign Affairs
- ⚽ Sports
- 💻 Technology
- 🔬 Science
- 🏥 Health
- 🎬 Entertainment

## 🚢 Deployment

### DigitalOcean Droplet

1. Create a droplet (Ubuntu 22.04+, 2GB RAM minimum)
2. Install Docker and Docker Compose
3. Clone the repository
4. Configure `.env` with production values
5. Run `docker compose up -d`

### SSL/HTTPS (Production)

For production, modify `nginx/nginx.conf` to include SSL:

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    # ... rest of config
}
```

See [docs/deployment.md](docs/deployment.md) for detailed instructions.

## 🧪 Testing

The project includes comprehensive tests:

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/

# With verbose output
pytest -v --tb=short
```

## 📚 Documentation

- [API Documentation](docs/api.md)
- [Architecture Overview](docs/architecture.md)
- [Database Schema](docs/database-schema.md)
- [Deployment Guide](docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
