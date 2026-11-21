# Deployment Segment

## Overview
This folder contains the local container foundation and staged production architecture for ClearHire.AI. The project is still intentionally local-first by default, but the deployment assets below document a production shape that can be run in AWS or Kubernetes without hard-coding secrets or cloud-only assumptions.

## Target AWS production architecture

- Frontend: Next.js in ECS/Fargate or EC2 with CloudFront in front of it
- Backend: FastAPI service in ECS/Fargate or App Runner/ECS, exposing port 8000
- Database: Amazon RDS PostgreSQL
- Cache: Amazon ElastiCache Redis
- Object storage: S3-compatible storage for uploaded resumes and exported artifacts
- Secrets: AWS Secrets Manager or SSM Parameter Store
- Logs: CloudWatch logs + structured JSON logs from the API
- Monitoring: health checks, readiness checks, alerting on 5xxs and queue backlogs

Recommended deployment flow:

1. Store secrets in AWS Secrets Manager.
2. Deploy PostgreSQL and Redis as managed services.
3. Keep the application in a non-root container image with env-based configuration.
4. Configure health/readiness probes to `/health` and `/ready`.
5. Use separate production env values for `ENVIRONMENT=production`, `DEBUG=false`, and explicit S3/Redis configuration.

## Local docker workflow

```bash
cd job_automate/deployment/docker
docker compose up --build
```

Endpoints:

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Production config example

Use placeholders only. Never commit real credentials. See [job_automate/backend/.env.example](../backend/.env.example) and [job_automate/frontend/.env.example](../frontend/.env.example).

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=replace-with-a-random-secret
DATABASE_URL=postgresql://user:pass@prod-db.endpoint:5432/job_automation
REDIS_URL=redis://prod-cache.endpoint:6379/0
STORAGE_PROVIDER=s3
STORAGE_BUCKET=clearhire-prod-storage
STORAGE_REGION=us-east-1
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
```

## AWS deployment checklist

- [ ] RDS database created with backups enabled
- [ ] Redis cache configured with TLS enabled
- [ ] S3 bucket created with private access and lifecycle rules
- [ ] Secrets Manager values populated for DB, Redis, and API keys
- [ ] CI workflow passes before deploying
- [ ] Docker images built, scanned, and published to a container registry
- [ ] Health checks pass for backend and frontend
- [ ] CloudWatch log groups established
- [ ] Alerting configured for 5xx errors and failed jobs
- [ ] Backups and restore procedure documented

## Kubernetes foundation

The repo contains minimal manifests under [job_automate/deployment/kubernetes](kubernetes). These are starter manifests, not a fully managed cluster deployment.

## Production safety notes

- Local development defaults remain in place.
- Production validation fails fast if required config is missing.
- No app secrets are committed to source.
- Resume content and uploaded file payloads are never intentionally logged in the application layer.

## Monitoring and observability

The backend now exposes:

- `/health` for service health
- `/ready` for dependency readiness
- `/metrics` for Prometheus request counters and latency histograms (per process/pod)

A request ID can be passed as `X-Request-ID` and is echoed back in headers and response payloads. Structured logs include request metadata without raw resume payloads or secrets.

## CI/CD gates

GitHub Actions runs the backend test suite, frontend production build, Docker Compose configuration check, and strict Kubernetes schema validation on pushes to `main`/`master` and pull requests. This is continuous integration only: it does not publish images or deploy to AWS. The AWS architecture below and Kubernetes manifests are deployment foundations; no cloud account, infrastructure provisioning, or live deployment is configured in this repository.

## Database Migrations

```bash
cd job_automate/backend
alembic upgrade head
```

## Security best practices

- Secrets are passed via environment variables or AWS Secrets Manager.
- `.env` files are excluded from source control.
- API keys are hashed before persistence and never logged.
- Production config validation fails fast if required values are absent.

## Rollback procedure

```bash
# Local Docker
cd job_automate/deployment/docker
docker compose down

# Kubernetes
kubectl rollout undo deployment/clearhire-backend
kubectl rollout undo deployment/clearhire-frontend
```

## Post-deployment smoke tests

- Test backend health and readiness endpoints
- Test frontend home page loads
- Test resume upload path with a small sample file
- Confirm logs show request IDs and no raw secret data
