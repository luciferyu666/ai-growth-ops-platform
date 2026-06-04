from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/proposal", tags=["proposal"])


@router.get("/demo")
def proposal_demo() -> dict[str, Any]:
    return {
        "title": "Technical Proposal Demo",
        "subtitle": "Compliant AI Growth Ops SaaS engineering foundation",
        "positioning": {
            "primary": "Technical capability and delivery readiness demo",
            "not_claiming": [
                "Full production product",
                "Completed CRM workflow",
                "Completed AI content workflow",
                "Platform evasion or fake review automation",
            ],
            "recommended_talk_track": (
                "This demo proves that the team can design and deliver a "
                "maintainable SaaS foundation for compliant AI-assisted growth "
                "operations. It shows the architecture, audit-first data model, "
                "runtime services, and productization roadmap."
            ),
        },
        "readiness": [
            {
                "label": "Engineering foundation",
                "score": 65,
                "status": "demo-ready",
                "evidence": "Web, API, DB, Redis, worker, Docker Compose, tests",
            },
            {
                "label": "Compliance alignment",
                "score": 70,
                "status": "proposal-ready",
                "evidence": "Explicit allowed/disallowed boundaries and audit schema",
            },
            {
                "label": "Business MVP",
                "score": 10,
                "status": "not-started",
                "evidence": "Domain tables exist; user workflows are not implemented yet",
            },
            {
                "label": "Demo confidence",
                "score": 55,
                "status": "technical-demo",
                "evidence": "Suitable for architecture and delivery capability review",
            },
        ],
        "capabilities": [
            {
                "area": "System architecture",
                "proof": "ADR-driven monorepo with separated web, API, infra, and docs",
                "state": "demonstrated",
            },
            {
                "area": "SaaS application foundation",
                "proof": "Next.js dashboard, FastAPI service, PostgreSQL, Redis, Celery",
                "state": "demonstrated",
            },
            {
                "area": "Data governance",
                "proof": "Consent records, approval records, and append-oriented audit events",
                "state": "foundation-ready",
            },
            {
                "area": "AI workflow readiness",
                "proof": "Content draft schema includes prompt version and model metadata",
                "state": "designed-not-implemented",
            },
            {
                "area": "Delivery operations",
                "proof": "Docker Compose runtime, tests, lint, migrations, health checks",
                "state": "demonstrated",
            },
        ],
        "architecture": [
            {
                "service": "Web",
                "stack": "Next.js 16 + TypeScript + Tailwind CSS",
                "demo_value": "Operator dashboard and proposal presentation surface",
            },
            {
                "service": "API",
                "stack": "FastAPI + Python 3.12",
                "demo_value": "Structured proposal data, health checks, future domain APIs",
            },
            {
                "service": "Database",
                "stack": "PostgreSQL + SQLAlchemy + Alembic",
                "demo_value": "Durable CRM, consent, approval, draft, and audit records",
            },
            {
                "service": "Automation",
                "stack": "Redis + Celery",
                "demo_value": "Foundation for scheduled imports, AI jobs, and reports",
            },
        ],
        "roadmap": [
            {
                "phase": "Phase 1",
                "name": "Demo vertical slice",
                "timeline": "1-2 weeks",
                "outcome": "CRM to content approval to audit event workflow",
                "deliverables": [
                    "Organization and contact CRUD",
                    "Consent record workflow",
                    "Content draft workflow with mock AI provider",
                    "Approval/rejection workflow",
                    "Dashboard metrics from real API data",
                ],
            },
            {
                "phase": "Phase 2",
                "name": "AI workflow productization",
                "timeline": "2-4 weeks",
                "outcome": "Prompt templates, provider abstraction, and review controls",
                "deliverables": [
                    "LLM provider adapter",
                    "Prompt versioning",
                    "Generated content audit trail",
                    "Human approval policy",
                    "Quality and compliance checks",
                ],
            },
            {
                "phase": "Phase 3",
                "name": "SaaS readiness",
                "timeline": "4-6 weeks",
                "outcome": "Multi-user, permissioned, deployable platform",
                "deliverables": [
                    "Authentication and RBAC",
                    "Tenant/workspace model",
                    "Production deployment pipeline",
                    "Observability and error monitoring",
                    "Backup and data retention plan",
                ],
            },
            {
                "phase": "Phase 4",
                "name": "Growth integrations",
                "timeline": "6+ weeks",
                "outcome": "Compliant API integrations and reporting workflows",
                "deliverables": [
                    "Official API integrations",
                    "Authorized data import flows",
                    "Review invitation management",
                    "Brand signal monitoring",
                    "Executive reporting",
                ],
            },
        ],
        "demo_script": [
            "Open the Technical Proposal Demo page.",
            "Show live API-backed proposal data and readiness scores.",
            "Explain the architecture map and health checks.",
            "Show the compliance boundary and what the product intentionally excludes.",
            "Walk through the productization roadmap and next vertical slice.",
            "Close by positioning this as a delivery capability demo, not a complete product claim.",
        ],
        "compliance_boundary": {
            "allowed": [
                "Official API integrations",
                "Authorized data imports",
                "Consent-based workflows",
                "Human-reviewed AI content drafts",
                "Real customer review invitation workflows",
                "Audit logs and data governance",
            ],
            "excluded": [
                "Fake reviews",
                "Unauthorized scraping",
                "Account farming",
                "Platform risk-control evasion",
                "CAPTCHA, OTP, or liveness bypass",
                "Unsolicited bulk messaging",
            ],
        },
    }
