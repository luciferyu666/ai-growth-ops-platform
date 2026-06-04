# ADR-0002: Technology Stack

## Status

Accepted

## Date

2026-06-03

## Context

The project is a new AI-assisted growth operations platform. It will likely need:

- A browser-based operator dashboard
- CRM-style records and workflow screens
- API services for product workflows
- LLM integration with prompt, response, and approval auditability
- Background jobs for imports, evaluations, reports, and scheduled tasks
- Relational data modeling for organizations, contacts, consent records, campaigns, approvals, and audit logs
- A local development setup that Codex and human maintainers can run consistently

Two broad stack options were considered:

1. A single full-stack framework, such as Next.js with database access inside the web app.
2. A split application stack, with a TypeScript frontend and a Python API/backend.

## Decision

Use a split stack:

- Frontend: Next.js with App Router and TypeScript
- UI foundation: Tailwind CSS, with shadcn/ui considered when component scaffolding starts
- Backend API: FastAPI
- Backend language: Python 3.12 for initial compatibility with AI/data tooling
- Database: PostgreSQL
- Backend ORM and migrations: SQLAlchemy 2.x and Alembic
- Background jobs: Celery with Redis as the initial broker/result backend
- Local development: Docker Compose
- Testing:
  - Frontend: Vitest or Playwright depending on UI surface
  - Backend: pytest
  - End-to-end: Playwright once user flows exist
- LLM integration: Provider adapter layer, with model choice treated as configuration rather than hard-coded architecture

## Rationale

Next.js is a strong fit for the operator-facing dashboard, authenticated application screens, tables, forms, and future reporting interfaces. Its TypeScript-first workflow also works well for AI-assisted frontend iteration.

FastAPI is a strong fit for the backend because the project will likely contain Python-heavy AI, data processing, integrations, and background workflow code. It also gives automatic OpenAPI documentation, which helps keep frontend/backend contracts explicit.

PostgreSQL is the default relational database because the expected domain has structured operational data, audit records, consent records, workflow events, and reporting needs.

Redis and Celery give the project a straightforward path for asynchronous work without introducing Kubernetes or a managed workflow engine too early.

Docker Compose is the initial runtime standard because it can run the frontend, API, worker, database, and Redis locally with predictable service boundaries.

## Alternatives Considered

### Single Next.js Full-Stack Application

Pros:

- Faster initial scaffolding
- Fewer services to run
- Simpler deployment for small applications

Cons:

- Python AI/data workflow support would become secondary or require separate scripts later
- Long-running background jobs are less natural inside a web app runtime
- API boundaries and audit-heavy backend workflows can become blurred

Decision: not selected for the main architecture.

### Django Monolith

Pros:

- Mature admin, ORM, auth, and backend conventions
- Strong fit for data-heavy internal tools

Cons:

- Frontend experience would either be less flexible or still require a separate React/Next.js layer
- Less natural for highly interactive product dashboards compared with a dedicated TypeScript frontend

Decision: not selected for the initial architecture.

### Microservices from the Start

Pros:

- Clear independent service ownership
- Better isolation for large teams

Cons:

- Too much operational overhead for an early R&D workspace
- Premature service boundaries would slow product discovery

Decision: deferred until scale or ownership boundaries justify it.

## Initial Repository Implications

The current root folders will evolve toward:

```text
.
├── apps/
│   ├── web/                Next.js frontend
│   └── api/                FastAPI backend
├── workers/                Celery worker modules, if not kept inside apps/api
├── packages/               Shared schemas or tooling, if needed
├── infra/                  Docker Compose and deployment assets
├── scripts/                Developer utilities
├── tests/                  Cross-service and integration tests
└── Documentations/         Product, architecture, compliance, and ADRs
```

The exact code layout should be created when the first application scaffold is added.

## Version Policy

- Pin major versions in project manifests.
- Prefer current LTS runtimes over bleeding-edge releases.
- Upgrade intentionally through ADRs or release notes when framework changes affect architecture.
- Keep generated lockfiles committed once applications are scaffolded.

Initial runtime targets:

- Node.js 22 LTS or newer version supported by the chosen Next.js and package tooling
- Python 3.12
- PostgreSQL 18 for new local development, unless deployment constraints require an older supported version

## Compliance and Safety Implications

The stack must support auditability from the start:

- Store generated content drafts and approvals.
- Store prompt versions and LLM response metadata.
- Store consent and opt-out records for messaging workflows.
- Keep outbound publishing or messaging behind explicit approval and provider policy checks.
- Avoid architecture that enables unauthorized platform automation or evasion workflows.

## Open Follow-Up Decisions

- ADR-0003: Repository layout and application scaffolding
- ADR-0004: Authentication and authorization approach
- ADR-0005: Data model and audit log foundation
- ADR-0006: LLM provider abstraction and prompt audit design
- ADR-0007: Local development environment and Docker Compose services

## Reference Links

- Next.js installation and system requirements: https://nextjs.org/docs/pages/getting-started/installation
- FastAPI documentation: https://fastapi.tiangolo.com/
- PostgreSQL documentation: https://www.postgresql.org/docs/
- Docker Compose documentation: https://docs.docker.com/compose/
