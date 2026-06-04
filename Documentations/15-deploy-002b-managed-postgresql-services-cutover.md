# DEPLOY-002B: Managed PostgreSQL Provisioning and Vercel Services Cutover

## Purpose

`DEPLOY-002B` moves the Technical Proposal Demo from a frontend-only Vercel deployment to a cloud-backed SaaS demo with:

- FastAPI deployed as a Vercel API service under `/api`
- Managed PostgreSQL for persistent workspace data and audit events
- DB-backed workflow fallback instead of Redis for the first production demo cutover
- Frontend API calls routed to the production API service

## Final Status

Status: completed

Production URLs:

- Web: `https://ai-growth-ops-platform.vercel.app`
- API health: `https://ai-growth-ops-platform.vercel.app/api/health`
- API deep health: `https://ai-growth-ops-platform.vercel.app/api/health/deep`
- Proposal API: `https://ai-growth-ops-platform.vercel.app/api/proposal/demo`
- Workspace API: `https://ai-growth-ops-platform.vercel.app/api/workspace/metrics`

Production deployment:

- Deployment URL: `https://ai-growth-ops-platform-4lw0p5tv9-vincent-lius-projects-de5eeb92.vercel.app`
- Deployment ID: `dpl_CfC2jiVvKA2nK7NVGfB2o3xRydLj`
- Vercel project: `vincent-lius-projects-de5eeb92/ai-growth-ops-platform`
- Framework Preset: Services
- Root Directory: repository root

Managed PostgreSQL:

- Provider: Neon through Vercel Marketplace
- Resource name: `ai-growth-ops-platform-postgres`
- Resource ID: `store_glFBoYv5H5lQJSYz`
- External resource ID: `lucky-rain-17272464`
- Plan: `free_v3`
- Region: `iad1`
- Connected environments: production, preview, development

Migration:

- Alembic revision: `20260604_0005`
- Table count: 15
- Tables:
  - `alembic_version`
  - `approval_records`
  - `approval_snapshots`
  - `audit_events`
  - `background_jobs`
  - `consent_records`
  - `contacts`
  - `content_drafts`
  - `notification_outbox`
  - `operational_events`
  - `organizations`
  - `users`
  - `workspace_invitations`
  - `workspace_memberships`
  - `workspaces`

## Completed Work

- Accepted Neon Marketplace terms in the Vercel browser flow.
- Provisioned Neon through Vercel Marketplace.
- Pulled production environment variables to `.env.production.local`.
- Verified production env includes `DATABASE_URL`, `POSTGRES_URL`, and `POSTGRES_URL_NON_POOLING`.
- Ran Alembic migrations against managed PostgreSQL from the Docker API container.
- Verified the managed PostgreSQL schema and migration revision.
- Set production workflow fallback env:
  - `APP_ENV=production`
  - `WORKFLOW_QUEUE_MODE=database`
  - `REDIS_REQUIRED=false`
- Updated Vercel project settings:
  - Root Directory: repository root
  - Framework Preset: Services
  - Build Command: none
  - Install Command: none
  - Output Directory: none
- Deployed production from the repository root.
- Verified production web routes return 200:
  - `/`
  - `/proposal`
  - `/workspace`
- Verified production API routes:
  - `/api/health`
  - `/api/health/deep`
  - `/api/proposal/demo`
  - `/api/workspace/metrics`
- Verified production error logs show no critical runtime errors.

## Health Results

`GET /api/health`:

```json
{
  "status": "ok",
  "service": "api",
  "environment": "production",
  "database_configured": true,
  "redis_configured": false,
  "workflow_queue_mode": "database"
}
```

`GET /api/health/deep`:

```json
{
  "status": "ok",
  "service": "api",
  "environment": "production",
  "checks": {
    "database": { "status": "ok" },
    "queue": { "status": "ok", "mode": "database" }
  }
}
```

## Redis Decision

For this cutover, Redis remains deferred and the production demo uses DB-backed workflow fallback.

Reason:

- MVP-006 and MVP-007 already persist workflow jobs, notification outbox rows, retry state, and operational events in PostgreSQL.
- The Technical Proposal Demo needs deterministic cloud persistence more than continuously running workers.
- This avoids adding a second managed provider before the backend service and database are proven in production.

Redis can be added later through Upstash or Redis Marketplace when a persistent background worker runtime is selected.

## Acceptance Criteria

- Vercel production deployment uses Services: completed.
- `GET /api/health` returns `status: ok`: completed.
- `GET /api/health/deep` returns database `ok`: completed.
- Queue check returns database queue fallback `ok`: completed.
- Alembic migrations have run against managed PostgreSQL: completed.
- `/workspace` loads from the production deployment: completed.
- Dashboard and workspace API calls can reach production API under `/api`: completed.
- Production error logs show no critical runtime failures: completed.

## Remaining Production Hardening

- Add a managed Redis provider only when a persistent worker runtime is selected.
- Add production seed/demo reset tooling for controlled proposal demos.
- Add observability drains or external log retention.
- Add Auth0 production tenant secrets before external users access the workspace.
- Add backup and retention policy documentation for Neon.
