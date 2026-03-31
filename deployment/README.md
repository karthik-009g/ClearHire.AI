# Deployment Segment

## Overview
Complete deployment infrastructure and configuration for development, staging, and production environments.

## Structure

```
deployment/
├── docker/
│   ├── Dockerfile              # Backend image
│   ├── docker-compose.yml      # Local dev stack
│   ├── docker-compose.prod.yml # Production stack
│   ├── .dockerignore
│   ├── nginx.conf              # Reverse proxy config
│   └── init-db.sql             # Database initialization
│
├── aws/
│   ├── terraform/
│   │   ├── main.tf             # VPC, networking
│   │   ├── backend.tf          # Backend service
│   │   ├── database.tf         # RDS PostgreSQL
│   │   ├── storage.tf          # S3 buckets
│   │   ├── cdn.tf              # CloudFront CDN
│   │   ├── security.tf         # Security groups
│   │   ├── variables.tf        # Input variables
│   │   ├── outputs.tf          # Output values
│   │   └── terraform.tfvars    # Configuration
│   │
│   └── scripts/
│       ├── deploy.sh           # Deployment script
│       ├── health-check.sh     # Health monitoring
│       └── backup.sh           # Database backups
│
├── kubernetes/
│   ├── namespace.yaml          # K8s namespace
│   ├── configmap.yaml          # App configuration
│   ├── secrets.yaml            # Sensitive data
│   ├── backend-deployment.yaml # Backend pods
│   ├── postgres-deployment.yaml # Database
│   ├── redis-deployment.yaml   # Cache layer
│   ├── service.yaml            # ClusterIP service
│   ├── ingress.yaml            # Load balancer
│   └── hpa.yaml                # Auto-scaling
│
├── monitoring/
│   ├── prometheus.yml          # Metrics config
│   ├── grafana-dashboards.json # Grafana setup
│   └── alerts.yaml             # Alert rules
│
└── ci-cd/
    ├── .github/workflows/
    │   ├── build.yml           # Build & test
    │   ├── deploy-dev.yml      # Deploy to dev
    │   ├── deploy-prod.yml     # Deploy to prod
    │   └── security-scan.yml   # Security checks
    └── gitlab-ci.yml           # GitLab CI alternative
```

## Deployment Options

### Option 1: Docker Compose (Development)
**Best for:** Local development, testing

```bash
cd docker
docker-compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# PostgreSQL: localhost:5432
# Redis: localhost:6379
```

### Option 2: AWS (Production)
**Infrastructure:**
- **Compute:** EC2 + Auto Scaling Group
- **Database:** RDS PostgreSQL
- **Storage:** S3 for resumes & files
- **CDN:** CloudFront for static assets
- **Load Balancer:** ALB + Route53
- **Container Registry:** ECR
- **Monitoring:** CloudWatch + SNS alerts

**Deployment Steps:**
```bash
cd aws/terraform
terraform init
terraform plan
terraform apply
```

**Or use Lambda (Serverless):**
- AWS Lambda for API
- RDS for database
- S3 for storage
- API Gateway for routing

### Option 3: Kubernetes
**For:** Scalable, cloud-agnostic deployment

```bash
cd kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml
```

## Environment Configuration

### Development (.env.dev)
```
DATABASE_URL=postgresql://user:pass@postgres:5432/job_automation
REDIS_URL=redis://redis:6379/0
DEBUG=true
ENVIRONMENT=development
CLAUDE_API_KEY=sk-ant-xxxx
```

### Production (.env.prod)
```
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/job_automation
REDIS_URL=redis://elasticache-endpoint:6379/0
DEBUG=false
ENVIRONMENT=production
CLAUDE_API_KEY=sk-ant-xxxx
SENTRY_DSN=https://xxxx@sentry.io/xxxx
```

## Database Migrations

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add joblistings table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Monitoring & Logging

- **Logs:** CloudWatch, ELK Stack, or Datadog
- **Metrics:** Prometheus + Grafana
- **Tracing:** Jaeger or AWS X-Ray
- **Alerts:** SNS, PagerDuty integration

## Backup & Disaster Recovery

- **Database Backups:** Daily automated RDS snapshots
- **Storage Backups:** S3 versioning enabled
- **Recovery Time Objective (RTO):** < 1 hour
- **Recovery Point Objective (RPO):** < 15 minutes

## Security Best Practices

✅ SSL/TLS certificates (AWS ACM)
✅ VPC with private subnets
✅ Security groups with minimal ports
✅ Secrets management (AWS Secrets Manager)
✅ WAF (Web Application Firewall)
✅ DDoS protection (AWS Shield)
✅ Regular security audits

## Cost Optimization

- **On-demand resources** with Auto Scaling
- **Reserved Instances** for baseline load
- **S3 Intelligent-Tiering** for storage
- **CloudFront caching** for CDN
- **RDS automated backups** (included)

## Deployment Checklist

- [ ] All secrets in Secrets Manager
- [ ] Database migrations tested
- [ ] Health checks configured
- [ ] Monitoring & alerts active
- [ ] Backup strategy verified
- [ ] SSL certificates valid
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Runbooks documented
- [ ] Team trained on deployment

## Rollback Procedure

```bash
# For Docker Compose
docker-compose down
git checkout previous-tag
docker-compose up -d

# For AWS
./scripts/deploy.sh --rollback --version=previous-tag

# For Kubernetes
kubectl rollout undo deployment/backend
kubectl rollout undo deployment/frontend
```

## Post-Deployment

1. **Health Checks**
   ```bash
   ./scripts/health-check.sh
   ```

2. **Smoke Tests**
   - Test login flow
   - Test job scraping
   - Test resume upload
   - Test application submission

3. **Monitor**
   - Check CPU, Memory, Network
   - Monitor API response times
   - Track error rates
   - Monitor database connections

## Support & Documentation

- See parent `README.md` for overview
- AWS setup: `aws/terraform/README.md`
- K8s setup: `kubernetes/README.md`
- Monitoring: `monitoring/README.md`
