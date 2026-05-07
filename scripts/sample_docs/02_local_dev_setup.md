# Think Tank Platform — Local Development Setup

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js 20+** (use nvm: `nvm install 20`)
- **Docker Desktop** (v4.25+) with at least 8 GB RAM allocated
- **PostgreSQL 15** client tools (`brew install postgresql@15`)
- **AWS CLI v2** configured with MHP dev credentials
- **Git** with SSH key added to GitHub

## Quick Start

```bash
# 1. Clone the repository
git clone git@github.com:mhp-digital/think-tank-platform.git
cd think-tank-platform

# 2. Copy environment files
cp .env.example .env
# Edit .env and fill in your KEYCLOAK_CLIENT_SECRET and AWS credentials

# 3. Start infrastructure (PostgreSQL, Redis, Elasticsearch, RabbitMQ)
docker compose up -d postgres redis elasticsearch rabbitmq

# 4. Run database migrations
cd api-gateway && npm run migrate:up && cd ..
cd knowledge-service && npm run migrate:up && cd ..

# 5. Install dependencies for all services
npm install --workspaces

# 6. Start all services in development mode
npm run dev
```

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| API Gateway | 4000 | http://localhost:4000 |
| Knowledge Service | 4001 | http://localhost:4001 |
| Search Service | 4002 | http://localhost:4002 |
| Notification Service | 4003 | http://localhost:4003 |
| User Service | 4004 | http://localhost:4004 |
| Frontend | 3000 | http://localhost:3000 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| Elasticsearch | 9200 | http://localhost:9200 |
| RabbitMQ Management | 15672 | http://localhost:15672 |

## Common Issues

### "Connection refused" on PostgreSQL
Ensure Docker is running and the postgres container is healthy:
```bash
docker compose ps postgres
docker compose logs postgres
```

### Elasticsearch keeps crashing
Increase Docker memory to at least 8 GB. Elasticsearch needs `vm.max_map_count=262144`:
```bash
# macOS (inside Docker VM)
docker run --privileged --pid=host debian nsenter -t 1 -m -u -n -i -- sysctl -w vm.max_map_count=262144
```

### Keycloak redirect issues in local dev
Add this to your `/etc/hosts`:
```
127.0.0.1 keycloak.local
```
Then set `KEYCLOAK_URL=http://keycloak.local:8080` in your `.env`.
