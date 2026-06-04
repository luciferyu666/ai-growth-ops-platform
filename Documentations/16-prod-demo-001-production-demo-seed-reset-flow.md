# PROD-DEMO-001: Production Demo Seed and Reset Flow

## Purpose

`PROD-DEMO-001` makes the cloud-backed workspace demo repeatable for proposal meetings.

The goal is to avoid an empty production dashboard while keeping demo data controlled, compliant, and easy to reset before a walkthrough.

## Scope

Implemented:

- `POST /workspace/demo/seed`
  - Creates demo records only when the workspace has no organization or content draft records.
  - Returns existing metrics when demo data is already present.
- `POST /workspace/demo/reset`
  - Clears current workspace demo records.
  - Rebuilds a complete CRM to approval to audit demo slice.
- Workspace UI actions:
  - `Seed demo data`
  - `Reset & seed demo`
- Production guard:
  - In `APP_ENV=production`, demo data tools only work with `demo-header` auth.
  - In `APP_ENV=production`, allowed workspace slugs are restricted to:
    - `demo-growth-ops`
    - `demo-sandbox`

## Seeded Data

The seed flow creates a compliant demonstration slice:

- Organization: `Acme Wellness Clinic`
- Contact: opted-in demo contact
- Consent record: email consent with lawful basis `consent`
- Content draft: compliant opt-in review invitation follow-up
- Approval record: human-reviewed approval
- Approval snapshot: immutable review evidence
- Audit events:
  - organization created
  - contact created
  - consent record created
  - content draft created
  - policy evaluated
  - content draft approved
  - approval snapshot created
  - demo data seeded or reset

## Compliance Boundary

The seeded data is synthetic and uses `.example` domains or local demo identities. It does not include:

- Real customer personal data
- Fake reviews
- Platform automation
- Account matrix behavior
- Unauthorized scraping
- External message delivery

## Production Usage

Use the workspace UI:

```text
https://ai-growth-ops-platform.vercel.app/workspace
```

Or call the API directly:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri https://ai-growth-ops-platform.vercel.app/api/workspace/demo/seed `
  -Headers @{
    "X-Demo-User-Email" = "operator@ai-growth-ops.local"
    "X-Demo-Workspace-Slug" = "demo-growth-ops"
    "X-Demo-Role" = "owner"
  }
```

Reset and rebuild:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri https://ai-growth-ops-platform.vercel.app/api/workspace/demo/reset `
  -Headers @{
    "X-Demo-User-Email" = "operator@ai-growth-ops.local"
    "X-Demo-Workspace-Slug" = "demo-growth-ops"
    "X-Demo-Role" = "owner"
  }
```

Validate metrics:

```powershell
Invoke-RestMethod `
  -Uri https://ai-growth-ops-platform.vercel.app/api/workspace/metrics `
  -Headers @{
    "X-Demo-User-Email" = "operator@ai-growth-ops.local"
    "X-Demo-Workspace-Slug" = "demo-growth-ops"
    "X-Demo-Role" = "owner"
  }
```

## Acceptance Criteria

- Production `/workspace` can seed non-zero demo data.
- Re-running seed does not duplicate existing seed data.
- Reset clears and rebuilds the demo workspace data.
- Production guard blocks non-demo workspace slugs.
- Metrics show non-zero values after seed/reset.
- Audit events show the seeded CRM, content approval, snapshot, and demo lifecycle actions.

## Follow-Up

Next production hardening task:

- Add a signed server-side demo admin action or protected route before exposing the demo reset control outside trusted proposal sessions.
