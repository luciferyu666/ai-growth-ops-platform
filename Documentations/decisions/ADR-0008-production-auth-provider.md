# ADR-0008: Production Authentication Provider

## Status

Accepted

## Context

MVP-002 and MVP-003 use header-based demo auth to prove workspace ownership, RBAC, review queues, and audit attribution. Before external users can access the system, that local development seam must be replaced with a verified authentication provider.

The production provider must support:

- Next.js App Router application login.
- FastAPI backend JWT validation.
- Workspace / organization membership mapping.
- Role and permission claims.
- Future enterprise SSO without changing the domain API contract.

## Decision

Use Auth0 by Okta as the first production authentication provider for MVP production planning.

Rationale:

- Auth0 provides an official Next.js SDK and quickstart for integrating login into Next.js applications.
- Auth0 has a FastAPI backend quickstart path for protected API endpoints.
- Auth0 provides documented JWT access-token validation guidance for APIs, including issuer, audience, expiration, and permission checks.
- OIDC/JWT keeps the FastAPI backend independent from the frontend framework.
- The current `AuthContext` contract can be preserved by replacing only the auth dependency.
- Auth0 keeps the first production path provider-managed while still preserving a standards-based exit path if enterprise requirements later demand Entra ID or another OIDC provider.

Microsoft Entra ID remains a secondary option for enterprise SSO and Azure-heavy deployments. If Azure API Management is introduced, its Microsoft Entra JWT validation policy can enforce token checks at the gateway layer before requests reach FastAPI.

## Scope Boundary

This ADR decides the production auth direction. MVP-005 adds Auth0 SDK wiring and backend bearer JWT validation behind `AUTH_PROVIDER=auth0`, but it does not include tenant secrets or hosted Auth0 configuration.

The current `X-Demo-*` header auth remains valid for local proposal demos and automated tests. It must be disabled outside local development before any external users are invited.

## Implementation Direction

MVP production auth should replace `app/services/auth.py` with a provider-backed implementation that:

1. Reads a bearer token from `Authorization`.
2. Validates issuer, signature, audience, expiration, and scopes.
3. Maps external subject and email to `users`.
4. Maps organization/workspace claims to `workspaces` and `workspace_memberships`.
5. Maps provider roles/scopes to the internal RBAC permissions in `app/services/rbac.py`.
6. Keeps local demo auth available only in development.

The backend remains the source of truth for workspace ownership and internal roles. Provider claims may identify the user and requested organization, but `workspace_memberships` must still decide the effective role.

## Environment Variables

Expected future variables:

```text
AUTH_PROVIDER=auth0
AUTH0_DOMAIN=
AUTH0_AUDIENCE=
AUTH0_CLIENT_ID=
AUTH0_CLIENT_SECRET=
AUTH0_ISSUER_BASE_URL=
AUTH0_SECRET=
AUTH0_SCOPE=openid profile email
APP_BASE_URL=
```

Secrets such as client secrets must not be committed.

## Sources

- Auth0 Next.js quickstart: `https://auth0.com/docs/quickstart/webapp/nextjs`
- Auth0 FastAPI API quickstart: `https://auth0.com/docs/quickstart/backend/fastapi/index`
- Auth0 access-token validation: `https://auth0.com/docs/secure/tokens/access-tokens/validate-access-tokens`
- Microsoft Entra token validation in Azure API Management: `https://learn.microsoft.com/en-us/azure/api-management/validate-azure-ad-token-policy`

## Consequences

- The current demo auth remains useful for local development and proposal demos.
- Production implementation can be staged without changing domain routes.
- Backend RBAC remains internal and testable.
- Enterprise SSO will require additional provider configuration and claim mapping.
- Auth0 tenant, callback URLs, logout URLs, API audience, and scopes become deployment prerequisites.

## Follow-Up Work

- Complete hosted Auth0 tenant configuration.
- Add production login/logout smoke tests.
- Add broader token claim mapping tests.
- Disable demo auth outside local development.
- Add CI checks that prevent production builds with `AUTH_PROVIDER=demo-header`.
