# NewsDigest Frontend

A production-ready Next.js frontend for the NewsDigest application. Built with TypeScript, Tailwind CSS, and shadcn/ui components.

## Features

- 🔐 JWT authentication with localStorage persistence
- 📱 Responsive design with Tailwind CSS
- 🎨 Modern UI with shadcn/ui components
- 📰 Personalized news digest reader
- ⚡ Static export for optimal performance
- 🐳 Docker-ready with Nginx production server

## Prerequisites

- Node.js 18+ or 20+
- npm or pnpm
- Docker (for containerized deployment)

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment:**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your API URL
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Using Docker Compose (Development)

```bash
# From the project root
docker compose -f frontend/docker-compose.yml -f frontend/docker-compose.override.yml up frontend
```

## Building for Production

### Local Build

```bash
# Build and export static files
npm run build

# The static files are in the `out/` directory
```

### Docker Build

```bash
# Build the Docker image
docker build -t newsdigest-frontend:latest ./frontend

# Run the container
docker run -p 80:80 newsdigest-frontend:latest
```

### Build with Custom API URL

```bash
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  -t newsdigest-frontend:latest \
  ./frontend
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with AuthProvider
│   ├── page.tsx           # Landing page
│   ├── login/             # Login page
│   ├── register/          # Registration page
│   ├── dashboard/         # User dashboard
│   ├── digest/            # Digest list and detail pages
│   ├── interests/         # Interest selection page
│   └── settings/          # User settings page
├── src/
│   ├── components/        # React components
│   │   ├── ui/           # shadcn/ui components
│   │   └── navbar.tsx    # Navigation component
│   ├── context/          # React Context providers
│   │   └── AuthContext.tsx
│   ├── hooks/            # Custom React hooks
│   │   ├── useFetch.ts
│   │   └── use-toast.ts
│   ├── lib/              # Utilities and API client
│   │   ├── api.ts        # API client with auth
│   │   ├── types.ts      # TypeScript interfaces
│   │   └── utils.ts      # Utility functions
│   └── styles/           # Global styles
│       └── globals.css
├── public/               # Static assets
├── nginx/                # Nginx configuration
├── Dockerfile            # Multi-stage Docker build
└── docker-compose.yml    # Docker Compose config
```

## Environment Variables

| Variable              | Description          | Default                 |
| --------------------- | -------------------- | ----------------------- |
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |

## Available Scripts

| Script           | Description                  |
| ---------------- | ---------------------------- |
| `npm run dev`    | Start development server     |
| `npm run build`  | Build and export static site |
| `npm run lint`   | Run ESLint                   |
| `npm run format` | Format code with Prettier    |
| `npm test`       | Run tests                    |

## Deployment to DigitalOcean

### Using GHCR (Recommended)

1. **Push to main branch** - CI/CD will build and push image to GHCR

2. **SSH into droplet:**
   ```bash
   ssh user@your-droplet-ip
   ```

3. **Pull and run:**
   ```bash
   # Login to GHCR
   echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
   
   # Pull latest image
   docker pull ghcr.io/YOUR_USERNAME/news-bot/frontend:latest
   
   # Stop old container
   docker stop news-digest-frontend || true
   docker rm news-digest-frontend || true
   
   # Run new container
   docker run -d \
     --name news-digest-frontend \
     --restart unless-stopped \
     -p 80:80 \
     --network news-digest-network \
     ghcr.io/YOUR_USERNAME/news-bot/frontend:latest
   ```

### Manual Docker Build

```bash
# On your local machine
docker build -t newsdigest-frontend:latest ./frontend
docker save newsdigest-frontend:latest | gzip > frontend.tar.gz
scp frontend.tar.gz user@droplet:/tmp/

# On the droplet
docker load < /tmp/frontend.tar.gz
docker run -d -p 80:80 --name news-digest-frontend newsdigest-frontend:latest
```

## Authentication Flow

1. User submits login form
2. Frontend sends POST to `/auth/login`
3. Backend returns JWT token
4. Token stored in `localStorage` as `newsdigest_token`
5. All subsequent API calls include `Authorization: Bearer <token>`
6. On 401 response, token is cleared and user redirected to login

## API Integration

The frontend communicates with the backend API at `NEXT_PUBLIC_API_URL`. Key endpoints:

- `POST /auth/login` - User authentication
- `POST /auth/register` - User registration
- `GET /users/me` - Get current user profile
- `GET /interests` - List available interests
- `PUT /users/me/interests` - Update user interests
- `GET /digests` - List user's digests
- `POST /digests/generate` - Generate new digest
- `GET /digests/:id` - Get digest details

## Troubleshooting

### CORS Issues
Ensure the backend has the frontend origin in `CORS_ORIGINS`:
```
CORS_ORIGINS=http://localhost:3000,http://your-domain.com
```

### Build Fails
- Clear `.next` and `out` directories
- Delete `node_modules` and reinstall
- Check Node.js version (18+ required)

### Docker Build Issues
- Ensure Docker has enough memory (4GB+ recommended)
- Check build args are passed correctly
- Verify nginx config syntax

## License

MIT
