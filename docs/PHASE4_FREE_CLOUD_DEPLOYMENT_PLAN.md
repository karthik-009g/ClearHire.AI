# Phase 4: Six-Month Student-Credit Deployment

## Objective

Deploy ClearHire.AI as a portfolio application and operate it for six months using no more than USD 100 of cloud credits. Keep the service small, observable, recoverable, and easy to tear down. This is a low-traffic demonstration deployment, not a high-availability production service.

The monthly planning ceiling is USD 16.67. Target no more than USD 12 per month and retain the rest for storage, data transfer, price variance, and cleanup mistakes. Budgets and alerts are warnings, not guaranteed spending caps; select an account plan that prevents charges if credits run out where possible.

## Provider Selection Gate

Do not create paid resources until the account's eligibility, credit balance, expiration date, and service restrictions have been checked in the provider console.

- Prefer the AWS Free account plan if eligible and if the required compute and storage services are available under that plan. AWS currently describes USD 100 at signup, possible additional credits, and a Free plan lasting up to six months or until credits are exhausted. Do not join an AWS Organization or create a Control Tower landing zone for this project; those actions can change the account plan and affect credits.
- Use Azure for Students if the student eligibility requirements are met. Its current offer is USD 100 in credits usable within 12 months, with the subscription disabling resources if the credit is exhausted unless upgraded. Verify VM pricing in the chosen region before deciding.
- Do not use Google's standard USD 300 Free Trial as the six-month deployment foundation: its credit currently expires after 90 days. It remains an option only if a separate eligible program or a post-trial always-free design is confirmed.

Official offer terms:

- [AWS Free Tier FAQ](https://aws.amazon.com/free/free-tier-faqs/)
- [AWS Free Tier account plans](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html)
- [Azure for Students offer details](https://azure.microsoft.com/en-us/pricing/offers/ms-azr-0170p)
- [Google Cloud Free Trial FAQ](https://cloud.google.com/signup-faqs)

Offers and service eligibility change. Recheck the provider's terms immediately before account creation and provisioning.

## Deployment Shape

For the six-month portfolio run, prefer one small Linux VM running the existing Docker Compose stack: frontend, FastAPI backend, PostgreSQL, and Redis. Keep the backend at one process/replica because the current background queue is in-process. Store database files and uploaded resumes on persistent volumes, restrict inbound traffic to SSH (restricted to the developer's IP), HTTP, and HTTPS, and terminate TLS on the host or a lightweight reverse proxy.

Keep the existing local storage provider for uploaded resumes unless object storage pricing and lifecycle rules are verified. Back up the database and resume files to a private object-storage bucket on a schedule, encrypt backups, and test restoring one. Use a private environment file on the VM or a low-cost native parameter store for secrets; never commit credentials.

This deliberately avoids Kubernetes, NAT gateways, load balancers, managed PostgreSQL, managed Redis, and multiple always-on compute instances. Those improve availability or operations but can consume the credit before the six-month target. The single VM is a single point of failure and must be documented as such.

## Task Queue

### Task 1: Verify the local container toolchain

- Install and start Docker Desktop, then open a new PowerShell session.
- Run `docker --version` and `docker compose version`.
- From `job_automate`, run `docker compose -f deployment/docker/docker-compose.yml config`.
- Expected result: Docker and Compose respond, and Compose accepts the configuration. Fix any reported configuration or build-path errors before deploying.

### Task 2: Run the full local stack

- Run `docker compose -f deployment/docker/docker-compose.yml up --build`.
- Verify the frontend at `http://localhost:3000`, backend readiness at `http://localhost:8000/ready`, and backend health at `http://localhost:8000/health`.
- Exercise login, resume upload, matching, application review, and application tracking.
- Expected result: all four services start healthy; a user can complete the core flow; stopping and restarting containers preserves PostgreSQL data and uploaded files.

### Task 3: Confirm student-credit eligibility and cost envelope

- Check whether the user is eligible for AWS Free Plan or Azure for Students and record the exact credit, expiration date, account restrictions, and allowed compute products.
- Price the smallest suitable Linux VM, persistent disk, snapshot/object storage, public IPv4, and expected egress in the intended region. Include taxes if applicable.
- Set a USD 12/month target and alerts at USD 5, USD 10, and USD 15, plus credit-balance alerts. Confirm whether resources stop automatically when credits end; do not assume an alert enforces a cap.
- Expected result: a written six-month estimate at or below USD 100 with at least USD 28 unallocated. If the VM alone exceeds the envelope, use scheduled demo hours or select another eligible provider before provisioning.

### Task 4: Harden the deployable images and runtime configuration

**Implementation status: complete; execution status: pending CI and local container validation.**

- Frontend upgraded to Next.js 16 and Node 24; CI runs lint, type-check, and production build.
- CI builds both container images and scans them for fixable critical/high vulnerabilities.
- Production settings reject placeholder secrets/database credentials, debug mode, disabled auth, non-HTTPS origins, and incomplete enabled integrations.
- Backend exposes separate `/health` and database-aware `/ready` endpoints; tests cover readiness failure and production config validation.
- Docker Compose uses PostgreSQL with pgvector, Alembic migrations, persistent volumes, and localhost-only service ports by default.
- Remaining validation: run Docker Compose locally and obtain a successful CI image build/scan. Frontend `npm audit` still reports 7 high findings in development dependency chains; do not treat the audit as clean or deploy until reviewed and resolved or explicitly accepted.

- Upgrade the frontend from unsupported Next.js 14 to a supported release before public deployment; keep the container and CI Node runtime on a supported LTS release.
- Build both images in CI, pin/update supported base-image versions, run an image vulnerability scan, and fail CI on agreed critical findings.
- Remove development defaults from production Compose configuration. Require strong generated secrets, explicit allowed CORS origins, a reachable frontend API URL, persistent storage, and production database settings.
- Ensure health/readiness probes distinguish process health from database readiness.
- Expected result: CI builds and scans both production images; production startup fails clearly when mandatory settings are missing; no default password or secret is accepted in the production profile.

### Task 5: Provision the smallest suitable cloud host

- Create one VM in the chosen provider/region only after Task 3 passes. Enable provider billing alerts and MFA; use a dedicated deploy identity with minimum permissions.
- Configure firewall/security-group rules for SSH from the user's IP and public web traffic only. Add HTTPS, automatic security updates, and non-root containers.
- Expected result: the host is reachable securely, the VM and disk line items match the estimate, and no unnecessary network gateway/load-balancer resources exist.

### Task 6: Deploy through CI/CD

- Store deployment credentials in GitHub Actions secrets or use short-lived workload identity where supported. Build and test on pull requests; deploy only from the protected main branch.
- Use a health-checked rollout and preserve the prior image/config for rollback. Do not deploy database migrations automatically until backup and rollback behavior have been tested.
- Expected result: a merge deploys a known image revision; failed health checks stop promotion and the previous revision can be restored.

### Task 7: Backups, observability, and operations

- Configure encrypted database and resume backups, retention, and a tested restore procedure. Keep credentials and resume content out of logs.
- Verify request IDs, `/health`, `/ready`, `/metrics`, log retention, disk alerts, and cloud cost alerts. Add a simple uptime check without introducing a paid monitoring tier.
- Record a monthly operating checklist: cost/credit remaining, failed jobs, disk usage, backup restore check, patch status, and deployment revision.
- Expected result: a documented operator can diagnose a failed service, restore from backup, and see remaining credit before it is exhausted.

### Task 8: Month-six teardown or explicitly funded continuation

- At least two weeks before credit expiry, export data, verify the latest backup, decide whether to migrate or shut down, and notify anyone using the demo.
- If there is no approved funding, delete compute, disks/snapshots beyond retention, public IPs, buckets after export, and other billable resources. Verify the billing console shows no active resources.
- Expected result: no unexpected post-credit charges and a reproducible deployment record for a future redeploy.

## Phase 4 Completion Gate

Phase 4 is complete only when the application is deployed to the chosen eligible account, the six-month estimate is within the credit budget, CI deploys successfully, health checks and backups have been exercised, and the teardown/continuation decision is documented. Local tests and a successful frontend build alone do not satisfy this gate.

Phase 5 SaaS tenancy, organizations, billing, and admin controls remain queued until this deployment gate passes. Do not add a paid billing provider or multi-tenant operational promises to the student-credit demo.
