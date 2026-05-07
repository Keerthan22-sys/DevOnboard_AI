# Think Tank Platform — Architecture Overview

## Tech Stack

The Think Tank Platform is built with a modern microservices architecture:

- **Frontend:** React 18 with TypeScript, hosted on Vercel
- **Backend API:** Node.js 20 with Express.js, deployed on AWS ECS
- **Database:** PostgreSQL 15 on AWS RDS (primary), Redis 7 for caching
- **Search:** Elasticsearch 8.x for full-text knowledge search
- **Message Queue:** RabbitMQ for async processing (document indexing, notifications)
- **Storage:** AWS S3 for file uploads and document storage
- **Auth:** Keycloak for SSO/OIDC, integrated with MHP's Active Directory
- **CI/CD:** GitHub Actions → Docker → AWS ECR → ECS Fargate

## Service Architecture

The platform consists of five core services:

1. **API Gateway** (`api-gateway/`) — Routes requests, handles rate limiting, JWT validation
2. **Knowledge Service** (`knowledge-service/`) — CRUD for articles, wikis, and documentation
3. **Search Service** (`search-service/`) — Elasticsearch indexing and query processing
4. **Notification Service** (`notification-service/`) — Email, Slack, and in-app notifications
5. **User Service** (`user-service/`) — User profiles, teams, permissions

### Inter-Service Communication

Services communicate via:
- **Synchronous:** REST APIs between gateway and downstream services
- **Asynchronous:** RabbitMQ events for indexing, notifications, and analytics
- **Shared Cache:** Redis for session data and frequently accessed entities

## Infrastructure

All services run as Docker containers on AWS ECS Fargate. Infrastructure is managed with Terraform (see `infra/` directory). Each service has its own Dockerfile and health check endpoint at `/health`.

### Environment Configuration

| Environment | URL | Database |
|-------------|-----|----------|
| Development | dev.thinktank.mhp.internal | dev-db.rds.amazonaws.com |
| Staging | staging.thinktank.mhp.internal | staging-db.rds.amazonaws.com |
| Production | thinktank.mhp.com | prod-db.rds.amazonaws.com |
