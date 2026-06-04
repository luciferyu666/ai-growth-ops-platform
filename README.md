# ai-growth-ops-platform

AI Growth Ops Platform is a new independent software R&D workspace for building a compliant AI-assisted growth operations system.

The project is intended for long-running AI agent collaboration, Git/GitHub version control, and incremental product discovery.

## Working Scope

- AI-assisted customer development workflows
- CRM and lead management automation
- Brand reputation monitoring and review response assistance
- LLM-powered content drafting with human approval
- Data governance, consent management, audit logs, and operational monitoring

## Operating Principles

- Use official APIs, licensed data, public data allowed by terms, or user-authorized data.
- Keep human review in the loop for outbound content and reputation workflows.
- Track architecture decisions and major product changes in documentation.
- Prefer small, verifiable iterations over large opaque changes.

## Repository Layout

```text
.
├── apps/
│   ├── web/                Next.js operator dashboard
│   └── api/                FastAPI backend and Celery worker package
├── Documentations/         Project docs, decisions, roadmap, and compliance notes
├── tests/                  Cross-service and end-to-end tests
├── scripts/                Local development and maintenance scripts
├── infra/                  Docker Compose and deployment assets
└── data/                   Local-only development data
```

## Current Status

The project now has an executable SaaS-shaped MVP foundation:

- Dockerized Next.js + FastAPI + PostgreSQL + Redis stack
- PostgreSQL schema managed by Alembic
- CRM/content approval/audit vertical slice
- Header-based local demo auth context
- Workspace-owned domain records and tenant-scoped API reads/mutations
- Role-based demo permissions
- Review queue and policy-gated content approval
- Paginated workspace list APIs with filters
- Update/delete workflows with audit events
- Production authentication provider decision captured in ADR-0008
- Auth0/OIDC production auth wiring behind `AUTH_PROVIDER=auth0`
- Workspace invitation create/list/accept workflow
- Immutable approval snapshots for reviewed content
- Notification outbox and background job ledger
- Operational events and structured request logging
- Workspace operations panel for workflow processing visibility
- Notification provider adapter boundary
- Retry scheduling, dead-letter handling, and operations alert thresholds
- Vercel Services readiness for production web/API deployment
- Cloud-backed Vercel Services deployment with FastAPI under `/api`
- Managed Neon PostgreSQL production persistence
- Production API configuration support for managed PostgreSQL and DB-backed workflow fallback
- Production demo seed/reset flow with guarded demo workspace scope

## Local Development

Copy `.env.example` to `.env` only when local overrides are needed. The Docker Compose defaults are enough for the first boot.

Start the full local stack:

```powershell
npm run dev
```

Or run the PowerShell helper:

```powershell
.\scripts\dev.ps1
```

Service URLs:

- Web: `http://localhost:3000`
- MVP Workspace: `http://localhost:3000/workspace`
- Technical Proposal Demo: `http://localhost:3000/proposal`
- API health: `http://localhost:8000/health`
- API deep health: `http://localhost:8000/health/deep`
- API proposal payload: `http://localhost:8000/proposal/demo`
- API auth context: `http://localhost:8000/workspace/auth/context`
- API workspace metrics: `http://localhost:8000/workspace/metrics`
- API review queue: `http://localhost:8000/workspace/review-queue`
- API invitations: `http://localhost:8000/workspace/invitations`
- API approval snapshots: `http://localhost:8000/workspace/approval-snapshots`
- API notification outbox: `http://localhost:8000/workspace/notification-outbox`
- API background jobs: `http://localhost:8000/workspace/background-jobs`
- API operational events: `http://localhost:8000/workspace/operational-events`
- API operation alerts: `http://localhost:8000/workspace/operations/alerts`
- API audit events: `http://localhost:8000/workspace/audit-events`
- API docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5433`
- Redis: `localhost:6379`

## Production Demo

Current public frontend:

- Web: `https://ai-growth-ops-platform.vercel.app`
- Technical Proposal Demo: `https://ai-growth-ops-platform.vercel.app/proposal`
- MVP Workspace UI: `https://ai-growth-ops-platform.vercel.app/workspace`

Current production status:

- Vercel project is configured as Services from the repository root.
- Next.js web is deployed at `/`.
- FastAPI is deployed under `/api`.
- Managed Neon PostgreSQL is provisioned and migrated to revision `20260604_0005`.
- Production `/api/health` and `/api/health/deep` return `ok`.
- Production `/workspace` can seed/reset repeatable demo data through guarded demo endpoints.
- Managed Redis is intentionally deferred; the cloud demo uses the DB-backed workflow fallback.

See `Documentations/14-deploy-002-production-backend-managed-persistence.md` for the deployment plan and acceptance criteria.
See `Documentations/15-deploy-002b-managed-postgresql-services-cutover.md` for the completed managed PostgreSQL and Services cutover record.
See `Documentations/16-prod-demo-001-production-demo-seed-reset-flow.md` for the production demo seed/reset workflow.

Run lightweight checks:

```powershell
npm run check
```

Run backend checks while the Docker stack is running:

```powershell
npm run api:lint
npm run api:test
```

## Local Demo Auth

MVP-002 uses local demo auth headers as a replaceable development seam:

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8000/workspace/auth/context `
  -Headers @{
    "X-Demo-User-Email" = "operator@ai-growth-ops.local"
    "X-Demo-Workspace-Slug" = "demo-growth-ops"
    "X-Demo-Role" = "owner"
  }
```

This is not production authentication. A verified identity provider should replace this dependency before external users access the system.

Production auth direction is documented in `Documentations/decisions/ADR-0008-production-auth-provider.md`: Auth0/OIDC is selected for the first production implementation, with Microsoft Entra ID reserved as a future enterprise SSO option.

Set `AUTH_PROVIDER=auth0` and `NEXT_PUBLIC_AUTH_PROVIDER=auth0` only after Auth0 tenant variables are configured. In Auth0 mode, the backend validates bearer JWTs and requires an existing workspace membership. New users join workspaces through `/workspace/invitations/accept`.

Demo roles currently supported:

- `owner`
- `admin`
- `operator`
- `reviewer`
- `viewer`

## Production Demo Data

Production demo data tools are available from `/workspace` for the demo workspaces only:

- `demo-growth-ops`
- `demo-sandbox`

The `Seed demo data` action creates a non-zero CRM, consent, approved content draft, approval snapshot, and audit trail without duplicating existing demo records. The `Reset & seed demo` action clears the current demo workspace records and rebuilds the same compliant demonstration data.

## Database Migrations

Schema changes are managed by Alembic from `apps/api`.

Apply migrations:

```powershell
npm run db:migrate
```

Check current migration revision:

```powershell
npm run db:current
```

List PostgreSQL tables:

```powershell
npm run db:tables
```

The API does not create tables on startup. Run migrations explicitly after pulling schema changes.

## Background Workflows

MVP-007 uses a database-backed notification outbox, provider adapter, retry policy, dead-letter handling, and background job ledger. Local demos can process queued work through:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri http://localhost:8000/workspace/background-jobs/process-pending `
  -Headers @{
    "X-Demo-User-Email" = "operator@ai-growth-ops.local"
    "X-Demo-Workspace-Slug" = "demo-growth-ops"
    "X-Demo-Role" = "owner"
  }
```

The Celery worker also exposes `app.worker.process_notification_job`, but local defaults intentionally use a mock notification provider and do not send real messages.

Notification workflow settings:

```powershell
$env:NOTIFICATION_PROVIDER = "mock"
$env:NOTIFICATION_RETRY_BASE_SECONDS = "60"
$env:NOTIFICATION_RETRY_MAX_SECONDS = "3600"
$env:NOTIFICATION_ALERT_DEAD_LETTER_THRESHOLD = "1"
$env:NOTIFICATION_ALERT_FAILED_JOB_THRESHOLD = "1"
$env:NOTIFICATION_ALERT_STALLED_MINUTES = "15"
```

Alert summaries are available through:

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8000/workspace/operations/alerts `
  -Headers @{
    "X-Demo-User-Email" = "operator@ai-growth-ops.local"
    "X-Demo-Workspace-Slug" = "demo-growth-ops"
    "X-Demo-Role" = "owner"
  }
```
