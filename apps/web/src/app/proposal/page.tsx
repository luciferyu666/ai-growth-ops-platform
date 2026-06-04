import { ProposalClient, type ProposalDemo } from "./proposal-client";

type ProposalResponse = {
  data: ProposalDemo;
  source: "api" | "fallback";
};

export const dynamic = "force-dynamic";

const fallbackProposal: ProposalDemo = {
  title: "Technical Proposal Demo",
  subtitle: "Compliant AI Growth Ops SaaS engineering foundation",
  positioning: {
    primary: "Technical capability and delivery readiness demo",
    not_claiming: [
      "Full production product",
      "Completed CRM workflow",
      "Completed AI content workflow",
      "Platform evasion or fake review automation",
    ],
    recommended_talk_track:
      "This page presents the current engineering foundation and the compliant productization roadmap. It is a delivery capability demo, not a complete product claim.",
  },
  readiness: [
    {
      label: "Engineering foundation",
      score: 65,
      status: "demo-ready",
      evidence: "Web, API, DB, Redis, worker, Docker Compose, tests",
    },
    {
      label: "Compliance alignment",
      score: 70,
      status: "proposal-ready",
      evidence: "Explicit boundaries and audit-first schema",
    },
    {
      label: "Business MVP",
      score: 10,
      status: "not-started",
      evidence: "Domain tables exist; workflows are not implemented yet",
    },
    {
      label: "Demo confidence",
      score: 55,
      status: "technical-demo",
      evidence: "Suitable for architecture and delivery capability review",
    },
  ],
  capabilities: [
    {
      area: "System architecture",
      proof: "ADR-driven monorepo with separated web, API, infra, and docs",
      state: "demonstrated",
    },
    {
      area: "SaaS application foundation",
      proof: "Next.js dashboard, FastAPI service, PostgreSQL, Redis, Celery",
      state: "demonstrated",
    },
    {
      area: "Data governance",
      proof: "Consent records, approval records, and audit events",
      state: "foundation-ready",
    },
  ],
  architecture: [
    {
      service: "Web",
      stack: "Next.js 16 + TypeScript + Tailwind CSS",
      demo_value: "Operator dashboard and proposal presentation surface",
    },
    {
      service: "API",
      stack: "FastAPI + Python 3.12",
      demo_value: "Structured proposal data and future domain APIs",
    },
    {
      service: "Database",
      stack: "PostgreSQL + SQLAlchemy + Alembic",
      demo_value: "Durable CRM, consent, approval, draft, and audit records",
    },
  ],
  roadmap: [
    {
      phase: "Phase 1",
      name: "Demo vertical slice",
      timeline: "1-2 weeks",
      outcome: "CRM to content approval to audit event workflow",
      deliverables: [
        "Organization and contact CRUD",
        "Consent record workflow",
        "Content draft workflow with mock AI provider",
        "Approval/rejection workflow",
      ],
    },
    {
      phase: "Phase 2",
      name: "AI workflow productization",
      timeline: "2-4 weeks",
      outcome: "Prompt templates, provider abstraction, and review controls",
      deliverables: [
        "LLM provider adapter",
        "Prompt versioning",
        "Generated content audit trail",
      ],
    },
  ],
  demo_script: [
    "Open the Technical Proposal Demo page.",
    "Show API-backed readiness scores.",
    "Explain architecture and compliance boundaries.",
    "Walk through the productization roadmap.",
  ],
  compliance_boundary: {
    allowed: [
      "Official API integrations",
      "Authorized data imports",
      "Consent-based workflows",
      "Human-reviewed AI content drafts",
    ],
    excluded: [
      "Fake reviews",
      "Unauthorized scraping",
      "Account farming",
      "Platform risk-control evasion",
    ],
  },
};

async function getProposalDemo(): Promise<ProposalResponse> {
  const apiBaseUrl =
    process.env.API_INTERNAL_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000";

  try {
    const response = await fetch(`${apiBaseUrl}/proposal/demo`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Proposal API returned ${response.status}`);
    }

    return {
      data: (await response.json()) as ProposalDemo,
      source: "api",
    };
  } catch {
    return {
      data: fallbackProposal,
      source: "fallback",
    };
  }
}

export default async function ProposalPage() {
  const { data, source } = await getProposalDemo();

  return <ProposalClient data={data} source={source} />;
}
