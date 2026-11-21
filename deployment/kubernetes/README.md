# Kubernetes foundation

This directory contains a minimal starter deployment for ClearHire.AI. It is intentionally simple and is meant to demonstrate a production deployment shape without claiming a live cluster is configured.

## Files

- backend-deployment.yaml
- frontend-deployment.yaml
- configmap.yaml
- secrets-template.yaml

## Notes

- Replace placeholder values in secrets-template.yaml before applying to a real cluster.
- Backing services such as PostgreSQL and Redis should be external managed services in production.
- Build the frontend image with `NEXT_PUBLIC_API_URL` set to a browser-reachable API URL; Next.js embeds this value during the image build, so a pod environment variable cannot change it later.
- Keep the backend at one replica while background-job state remains in-process. Add a durable shared queue before scaling it.
- Readiness and liveness probes target real application endpoints: `/ready`, `/health`, and `/`.
- Resource requests and limits are intentionally conservative starter values.
