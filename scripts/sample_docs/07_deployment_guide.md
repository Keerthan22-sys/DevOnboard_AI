# Think Tank Platform — Deployment Guide

## CI/CD Pipeline

The platform uses GitHub Actions for continuous integration and deployment.

### Pipeline Stages

1. **Lint & Type Check** — ESLint + TypeScript compiler on every PR
2. **Unit Tests** — Jest tests for each service (must pass before merge)
3. **Build** — Docker images built and pushed to AWS ECR
4. **Deploy Staging** — Automatic on merge to `main`
5. **Integration Tests** — Run against staging environment
6. **Deploy Production** — Manual approval required, then ECS rolling update

### GitHub Actions Workflow

The main workflow file is `.github/workflows/deploy.yml`. Key jobs:

- `test`: Runs in parallel for each service
- `build`: Builds Docker images with git SHA tags
- `deploy-staging`: Updates ECS task definitions for staging
- `deploy-prod`: Requires manual approval via GitHub Environment protection rules

## AWS Infrastructure

### ECS Services

Each microservice runs as a separate ECS Fargate service:

| Service | CPU | Memory | Desired Count | Auto-Scaling |
|---------|-----|--------|---------------|--------------|
| api-gateway | 512 | 1024 MB | 2 | 2–6 (CPU > 70%) |
| knowledge-service | 256 | 512 MB | 2 | 2–4 |
| search-service | 512 | 1024 MB | 1 | 1–3 |
| notification-service | 256 | 512 MB | 1 | 1–2 |
| user-service | 256 | 512 MB | 1 | 1–2 |

### Database (RDS)

- Instance type: `db.r6g.large` (production)
- Multi-AZ: Enabled
- Automated backups: 7-day retention
- Read replica in eu-west-1 for reporting queries

### Monitoring

- **CloudWatch** for logs and metrics
- **Datadog** for APM and distributed tracing
- **PagerDuty** integration for production alerts
- Health check endpoints: `GET /health` on every service

## Rollback Procedure

If a deployment causes issues:

1. Go to the ECS console or use AWS CLI
2. Update the service to use the previous task definition revision
3. ECS will perform a rolling update back to the previous version

```bash
# Quick rollback via CLI
aws ecs update-service \
  --cluster think-tank-prod \
  --service api-gateway \
  --task-definition api-gateway:<previous-revision>
```
