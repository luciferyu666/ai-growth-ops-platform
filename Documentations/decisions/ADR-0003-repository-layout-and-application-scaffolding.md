# ADR-0003: Repository Layout and Application Scaffolding

## Status

Accepted

## Date

2026-06-03

## Context

ADR-0002 selected a split stack:

- Next.js frontend
- FastAPI backend
- PostgreSQL database
- Redis/Celery background jobs
- Docker Compose local development

The repository now needs a concrete layout that can support long-running Codex sessions, Git/GitHub review, local development, and future application growth.

## Decision

Use a monorepo layout with separate application roots:

```text
.
├── apps/
│   ├── web/                Next.js operator dashboard
│   └── api/                FastAPI backend and Celery worker package
├── infra/
│   └── docker-compose.yml  Local multi-service runtime
├── scripts/                Developer entrypoints
├── tests/                  Cross-service and end-to-end test area
├── data/                   Local-only development data
└── Documentations/         Charter, roadmap, compliance notes, and ADRs
```

The first scaffold includes:

- `apps/web`: Next.js App Router, TypeScript, Tailwind CSS
- `apps/api`: FastAPI app with `/health`
- `infra/docker-compose.yml`: web, api, worker, PostgreSQL, and Redis services
- `.env.example`: non-secret local configuration template
- `scripts/dev.ps1`: Docker Compose local startup helper
- `scripts/check.ps1`: frontend lint and Compose config check helper

## Rationale

Separate app roots keep frontend and backend dependencies explicit. This matters because the frontend is TypeScript-heavy while the backend is Python-heavy and will likely own AI, data, integration, and background workflow logic.

Keeping the Celery worker in the API package is acceptable at this stage because it shares configuration and domain code with the backend. A separate `workers/` root can be introduced later if worker ownership or deployment boundaries become clearer.

Docker Compose gives the team a repeatable local runtime without forcing Kubernetes, cloud infrastructure, or managed services before the product boundaries are stable.

## Validation Criteria

The scaffold is valid when:

- `docker compose -f infra/docker-compose.yml config --quiet` succeeds.
- `npm run lint --prefix apps/web` succeeds.
- The FastAPI `/health` route returns `status: ok`.
- The Next.js dashboard opens on `http://localhost:3000`.
- No local secrets, database files, or generated dependency folders are tracked by Git.

## Consequences

- Future application code should be added under `apps/web` or `apps/api` unless a new ownership boundary justifies a new root.
- Shared contracts should not be invented prematurely. Add `packages/` only when there is real duplication or generated API schema tooling.
- Root-level `src/` is no longer part of the planned repository layout.
- Local data remains under `data/` and should stay untracked except for `.gitkeep`.

## Follow-Up Decisions

- ADR-0004: Authentication and authorization approach
- ADR-0005: Data model and audit log foundation
- ADR-0006: LLM provider abstraction and prompt audit design
- ADR-0007: Local development environment hardening
