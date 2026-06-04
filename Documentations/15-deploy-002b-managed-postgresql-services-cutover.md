# DEPLOY-002B: Managed PostgreSQL Provisioning and Vercel Services Cutover

## Purpose

`DEPLOY-002B` moves the Technical Proposal Demo from a frontend-only Vercel deployment toward a cloud-backed SaaS demo with:

- FastAPI deployed as a Vercel API service under `/api`
- Managed PostgreSQL for persistent workspace data and audit events
- DB-backed workflow fallback instead of Redis for the first production demo cutover
- Frontend API calls routed to the production API service

## Current Execution Status

Completed:

- Linked the local repository to `vincent-lius-projects-de5eeb92/ai-growth-ops-platform`.
- Verified current Vercel project settings:
  - Root Directory: `apps/web`
  - Framework Preset: Next.js
  - Node.js Version: 24.x
- Verified no managed Marketplace resources are currently connected.
- Confirmed production env did not yet include `DATABASE_URL`, `POSTGRES_URL`, or `REDIS_URL`.
- Added production fallback runtime env:
  - `APP_ENV=production`
  - `WORKFLOW_QUEUE_MODE=database`
  - `REDIS_REQUIRED=false`
- Added development fallback runtime env:
  - `APP_ENV=development`
  - `WORKFLOW_QUEUE_MODE=database`
  - `REDIS_REQUIRED=false`
- Updated frontend API URL priority so Vercel Services generated variables win:
  - Server-side: `API_URL` before `API_INTERNAL_BASE_URL`
  - Browser-side: `NEXT_PUBLIC_API_URL` before `NEXT_PUBLIC_API_BASE_URL`

Blocked:

- Neon Marketplace provisioning requires marketplace terms acceptance by the account owner.
- The CLI returned `integration_terms_acceptance_required`.
- This is a legal/account action and must be completed manually in the Vercel browser session.

## Manual Action Required

Open the Vercel Neon terms acceptance URL and accept the terms if the account owner agrees:

```text
https://vercel.com/vincent-lius-projects-de5eeb92/~/integrations/accept-terms/neon?source=cli
```

Policy links returned by Vercel:

- Vercel Marketplace Addendum: `https://vercel.com/legal/integration-marketplace-end-users-addendum`
- Neon Privacy Policy: `https://neon.tech/privacy-policy`
- Neon Terms of Service: `https://neon.tech/terms-of-service`

After terms are accepted, retry:

```powershell
vercel integration add neon `
  --plan free_v3 `
  --name ai-growth-ops-platform-postgres `
  -m region=iad1 `
  -m auth=false `
  -e production `
  -e preview `
  -e development `
  --format=json `
  --scope vincent-lius-projects-de5eeb92
```

## Redis Decision

For this cutover, use DB-backed workflow fallback instead of provisioning Redis.

Reason:

- MVP-006 and MVP-007 already persist workflow jobs, notification outbox rows, retry state, and operational events in PostgreSQL.
- The Technical Proposal Demo needs deterministic cloud persistence more than continuously running workers.
- This avoids adding a second managed provider before the backend service and database are proven in production.

Redis can be added later through Upstash or Redis Marketplace when a persistent background worker runtime is selected.

## Cutover Steps After Neon Provisioning

1. Pull production environment variables:

```powershell
vercel env pull .env.production.local --environment=production --yes --scope vincent-lius-projects-de5eeb92
```

2. Verify managed Postgres variables exist locally without printing secrets:

```powershell
Select-String -Path .env.production.local -Pattern "^(DATABASE_URL|POSTGRES_URL|POSTGRES_URL_NON_POOLING)="
```

3. Run Alembic migration against managed PostgreSQL:

```powershell
Push-Location apps/api
$env:APP_ENV = "production"
python -m alembic upgrade head
python -m alembic current
Pop-Location
```

4. Change Vercel project settings:

```text
Root Directory: repository root
Framework Preset: Services
```

5. Deploy production from `main`:

```powershell
vercel --prod --scope vincent-lius-projects-de5eeb92
```

6. Validate production API:

```powershell
Invoke-WebRequest -Uri "https://ai-growth-ops-platform.vercel.app/api/health" -UseBasicParsing
Invoke-WebRequest -Uri "https://ai-growth-ops-platform.vercel.app/api/health/deep" -UseBasicParsing
```

Expected deep health:

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

7. Validate frontend workflow:

- `/` loads proposal dashboard.
- `/proposal` loads Technical Proposal Demo.
- `/workspace` loads API-backed metrics.
- Creating a demo organization writes to managed PostgreSQL.
- Audit events are created for mutations.

## Do Not Cut Over Before These Are True

- Neon terms are accepted and the managed database is provisioned.
- `DATABASE_URL` or `POSTGRES_URL` exists in Vercel production env.
- Alembic migration succeeds against managed PostgreSQL.
- Vercel Services framework preset is selected.

Cutting over before these checks would likely produce a partially working frontend with failing `/api/health/deep` and broken workspace mutations.
