"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { buildApiUrl, getPublicApiBaseUrl } from "@/lib/api-base-url";

type Metrics = {
  organizations: number;
  contacts: number;
  consent_records: number;
  content_drafts: number;
  pending_drafts: number;
  approved_drafts: number;
  approval_records: number;
  approval_snapshots: number;
  pending_invitations: number;
  pending_notifications: number;
  retry_scheduled_notifications: number;
  delivered_notifications: number;
  dead_letter_notifications: number;
  queued_jobs: number;
  failed_jobs: number;
  open_operation_alerts: number;
  operational_events: number;
  audit_events: number;
};

type Pagination = {
  limit: number;
  offset: number;
  total: number;
  has_next: boolean;
  has_previous: boolean;
};

type PaginatedResponse<T> = {
  items: T[];
  pagination: Pagination;
};

type Organization = {
  id: string;
  workspace_id: string;
  name: string;
  domain: string | null;
  industry: string | null;
  status: string;
};

type Contact = {
  id: string;
  workspace_id: string;
  organization_id: string;
  name: string;
  email: string | null;
  role: string | null;
};

type ConsentRecord = {
  id: string;
  workspace_id: string;
  contact_id: string;
  channel: string;
  status: string;
  lawful_basis: string | null;
};

type ContentDraft = {
  id: string;
  workspace_id: string;
  organization_id: string;
  title: string;
  channel: string;
  status: string;
  draft_text: string;
  model_name: string | null;
  prompt_version: string | null;
  policy: {
    status: string;
    summary: string;
    violations: string[];
    warnings: string[];
    version: string;
  };
};

type ApprovalRecord = {
  id: string;
  workspace_id: string;
  content_draft_id: string;
  decision: string;
  reviewer_actor: string | null;
  comment: string | null;
};

type ApprovalSnapshot = {
  id: string;
  workspace_id: string;
  approval_record_id: string | null;
  content_draft_id: string;
  decision: string;
  reviewer_actor: string | null;
  snapshot_version: string;
  snapshot_data: {
    content_draft?: {
      title?: string;
      draft_text?: string;
    };
    policy?: {
      status?: string;
      summary?: string;
    };
    approval?: {
      decision?: string;
      reviewer_actor?: string | null;
    };
    reviewer_context?: {
      role?: string;
      auth_mode?: string;
    };
  };
  created_at: string | null;
};

type WorkspaceInvitation = {
  id: string;
  workspace_id: string;
  email: string;
  role: string;
  status: string;
  invited_by_actor: string | null;
  accepted_by_user_id: string | null;
  accepted_at: string | null;
  expires_at: string | null;
  token?: string;
};

type NotificationOutbox = {
  id: string;
  workspace_id: string;
  channel: string;
  recipient: string;
  subject: string | null;
  provider_name: string;
  status: string;
  attempt_count: number;
  max_attempts: number;
  next_attempt_at: string | null;
  last_attempt_at: string | null;
  provider_message_id: string | null;
  error_message: string | null;
  created_at: string | null;
};

type BackgroundJob = {
  id: string;
  workspace_id: string;
  job_type: string;
  queue_name: string;
  status: string;
  attempts: number;
  next_run_at: string | null;
  error_message: string | null;
  created_at: string | null;
};

type OperationalEvent = {
  id: string;
  workspace_id: string;
  severity: string;
  component: string;
  event_type: string;
  message: string;
  status: string;
  created_at: string | null;
};

type OperationAlert = {
  code: string;
  severity: string;
  message: string;
  count: number;
  threshold: number;
};

type OperationAlertSummary = {
  provider: string;
  thresholds: Record<string, number>;
  counts: Record<string, number>;
  alerts: OperationAlert[];
  generated_at: string | null;
};

type AuditEvent = {
  id: string;
  workspace_id: string;
  action: string;
  actor_id: string | null;
  resource_type: string | null;
  created_at: string | null;
};

type AuthContext = {
  auth_mode: string;
  actor_id: string;
  user: {
    id: string;
    email: string;
    display_name: string | null;
  };
  workspace: {
    id: string;
    slug: string;
    name: string;
  };
  membership: {
    id: string;
    role: string;
  };
};

type WorkspaceOption = {
  slug: string;
  name: string;
  label: string;
};

type RoleOption = {
  role: string;
  label: string;
};

const emptyMetrics: Metrics = {
  organizations: 0,
  contacts: 0,
  consent_records: 0,
  content_drafts: 0,
  pending_drafts: 0,
  approved_drafts: 0,
  approval_records: 0,
  approval_snapshots: 0,
  pending_invitations: 0,
  pending_notifications: 0,
  retry_scheduled_notifications: 0,
  delivered_notifications: 0,
  dead_letter_notifications: 0,
  queued_jobs: 0,
  failed_jobs: 0,
  open_operation_alerts: 0,
  operational_events: 0,
  audit_events: 0,
};

const apiBaseUrl = getPublicApiBaseUrl();
const authProvider = process.env.NEXT_PUBLIC_AUTH_PROVIDER ?? "demo-header";

const demoUserEmail = "operator@ai-growth-ops.local";
const demoUserName = "Demo Operator";
const workspaceOptions: WorkspaceOption[] = [
  {
    slug: "demo-growth-ops",
    name: "Demo Growth Ops Workspace",
    label: "Primary",
  },
  {
    slug: "demo-sandbox",
    name: "Demo Sandbox Workspace",
    label: "Sandbox",
  },
];
const roleOptions: RoleOption[] = [
  { role: "owner", label: "Owner" },
  { role: "operator", label: "Operator" },
  { role: "reviewer", label: "Reviewer" },
  { role: "viewer", label: "Viewer" },
];
const draftStatusOptions = [
  { value: "all", label: "All" },
  { value: "pending_review", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
];
const draftPageLimit = 5;

function emptyPaginatedResponse<T>(): PaginatedResponse<T> {
  return {
    items: [],
    pagination: {
      limit: 0,
      offset: 0,
      total: 0,
      has_next: false,
      has_previous: false,
    },
  };
}

async function apiRequest<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const auth0Headers =
    authProvider === "auth0" ? await getAuth0BearerHeaders() : {};
  const response = await fetch(buildApiUrl(apiBaseUrl, path), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...auth0Headers,
      ...(options?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = "";
    try {
      const payload = await response.json();
      detail =
        typeof payload.detail === "string"
          ? payload.detail
          : payload.detail?.message;
    } catch {
      detail = "";
    }
    throw new Error(
      detail ? `Request failed: ${response.status} - ${detail}` : `Request failed: ${response.status}`,
    );
  }

  return (await response.json()) as T;
}

async function getAuth0BearerHeaders(): Promise<Record<string, string>> {
  const response = await fetch("/auth/access-token", {
    cache: "no-store",
  });
  if (!response.ok) {
    return {};
  }
  const payload = (await response.json()) as {
    accessToken?: string;
    token?: string;
  };
  const token = payload.accessToken ?? payload.token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function MetricCard({
  label,
  value,
  detail,
}: Readonly<{
  label: string;
  value: number;
  detail: string;
}>) {
  return (
    <article className="rounded border border-zinc-200 bg-white p-5">
      <p className="text-sm text-zinc-500">{label}</p>
      <p className="mt-4 font-mono text-4xl font-semibold">{value}</p>
      <p className="mt-3 text-sm text-zinc-600">{detail}</p>
    </article>
  );
}

function TextInput({
  label,
  value,
  onChange,
}: Readonly<{
  label: string;
  value: string;
  onChange: (value: string) => void;
}>) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-zinc-700">{label}</span>
      <input
        className="h-10 rounded border border-zinc-300 bg-white px-3 outline-none transition-colors focus:border-teal-600"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function ActionButton({
  children,
  disabled,
  type = "button",
  onClick,
}: Readonly<{
  children: React.ReactNode;
  disabled?: boolean;
  type?: "button" | "submit";
  onClick?: () => void;
}>) {
  return (
    <button
      className="min-h-10 rounded bg-zinc-950 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-zinc-300"
      disabled={disabled}
      type={type}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export function WorkspaceClient() {
  const [workspaceSlug, setWorkspaceSlug] = useState(workspaceOptions[0].slug);
  const [demoRole, setDemoRole] = useState(roleOptions[0].role);
  const [authContext, setAuthContext] = useState<AuthContext | null>(null);
  const [metrics, setMetrics] = useState<Metrics>(emptyMetrics);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [consents, setConsents] = useState<ConsentRecord[]>([]);
  const [drafts, setDrafts] = useState<ContentDraft[]>([]);
  const [draftPagination, setDraftPagination] = useState<Pagination | null>(null);
  const [draftStatusFilter, setDraftStatusFilter] = useState("all");
  const [draftOffset, setDraftOffset] = useState(0);
  const [reviewQueue, setReviewQueue] = useState<ContentDraft[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRecord[]>([]);
  const [approvalSnapshots, setApprovalSnapshots] = useState<ApprovalSnapshot[]>([]);
  const [invitations, setInvitations] = useState<WorkspaceInvitation[]>([]);
  const [notificationOutbox, setNotificationOutbox] = useState<
    NotificationOutbox[]
  >([]);
  const [backgroundJobs, setBackgroundJobs] = useState<BackgroundJob[]>([]);
  const [operationalEvents, setOperationalEvents] = useState<OperationalEvent[]>(
    [],
  );
  const [operationAlerts, setOperationAlerts] =
    useState<OperationAlertSummary | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [statusMessage, setStatusMessage] = useState("Ready");
  const [isBusy, setIsBusy] = useState(false);

  const [organizationName, setOrganizationName] = useState("Demo Growth Studio");
  const [organizationDomain, setOrganizationDomain] = useState(
    "growth-studio.example",
  );
  const [contactName, setContactName] = useState("Alex Lin");
  const [contactEmail, setContactEmail] = useState("alex.lin@example.com");
  const [draftTitle, setDraftTitle] = useState("Human-reviewed growth follow-up");
  const [inviteEmail, setInviteEmail] = useState("reviewer@ai-growth-ops.local");
  const [inviteRole, setInviteRole] = useState("reviewer");
  const [latestInvitationToken, setLatestInvitationToken] = useState("");

  const selectedWorkspaceOption =
    workspaceOptions.find((option) => option.slug === workspaceSlug) ??
    workspaceOptions[0];
  const authHeaders = useMemo(
    () => ({
      "X-Demo-User-Email": demoUserEmail,
      "X-Demo-User-Name": demoUserName,
      "X-Demo-Workspace-Slug": workspaceSlug,
      "X-Demo-Workspace-Name": selectedWorkspaceOption.name,
      "X-Demo-Role": demoRole,
      "X-Workspace-Slug": workspaceSlug,
    }),
    [demoRole, selectedWorkspaceOption.name, workspaceSlug],
  );
  const selectedOrganization = organizations[0];
  const selectedContact = contacts[0];
  const latestDraft = useMemo(
    () =>
      reviewQueue[0] ??
      drafts.find((draft) => draft.status === "pending_review") ??
      drafts[0],
    [drafts, reviewQueue],
  );

  const workspaceRequest = useCallback(
    async <T,>(path: string, options?: RequestInit): Promise<T> =>
      apiRequest<T>(path, {
        ...options,
        headers: {
          ...authHeaders,
          ...(options?.headers ?? {}),
        },
      }),
    [authHeaders],
  );

  const refreshWorkspace = useCallback(async () => {
    const draftStatusQuery =
      draftStatusFilter === "all" ? "" : `&status=${draftStatusFilter}`;
    const [
      nextAuthContext,
      nextMetrics,
      nextOrganizations,
      nextContacts,
      nextConsents,
      nextDrafts,
      nextReviewQueue,
      nextApprovals,
      nextApprovalSnapshots,
      nextInvitations,
      nextNotificationOutbox,
      nextBackgroundJobs,
      nextOperationalEvents,
      nextOperationAlerts,
      nextAuditEvents,
    ] = await Promise.all([
      workspaceRequest<AuthContext>("/workspace/auth/context"),
      workspaceRequest<Metrics>("/workspace/metrics"),
      workspaceRequest<PaginatedResponse<Organization>>(
        "/workspace/organizations?limit=50",
      ),
      workspaceRequest<PaginatedResponse<Contact>>("/workspace/contacts?limit=50"),
      workspaceRequest<PaginatedResponse<ConsentRecord>>(
        "/workspace/consent-records?limit=50",
      ),
      workspaceRequest<PaginatedResponse<ContentDraft>>(
        `/workspace/content-drafts?limit=${draftPageLimit}&offset=${draftOffset}${draftStatusQuery}`,
      ),
      workspaceRequest<PaginatedResponse<ContentDraft>>(
        "/workspace/review-queue?limit=20",
      ),
      workspaceRequest<PaginatedResponse<ApprovalRecord>>(
        "/workspace/approval-records?limit=50",
      ),
      workspaceRequest<PaginatedResponse<ApprovalSnapshot>>(
        "/workspace/approval-snapshots?limit=10",
      ),
      demoRole === "owner"
        ? workspaceRequest<PaginatedResponse<WorkspaceInvitation>>(
            "/workspace/invitations?limit=10",
          )
        : Promise.resolve(emptyPaginatedResponse<WorkspaceInvitation>()),
      workspaceRequest<PaginatedResponse<NotificationOutbox>>(
        "/workspace/notification-outbox?limit=8",
      ),
      workspaceRequest<PaginatedResponse<BackgroundJob>>(
        "/workspace/background-jobs?limit=8",
      ),
      workspaceRequest<PaginatedResponse<OperationalEvent>>(
        "/workspace/operational-events?limit=8",
      ),
      workspaceRequest<OperationAlertSummary>("/workspace/operations/alerts"),
      workspaceRequest<PaginatedResponse<AuditEvent>>(
        "/workspace/audit-events?limit=12",
      ),
    ]);

    setAuthContext(nextAuthContext);
    setMetrics(nextMetrics);
    setOrganizations(nextOrganizations.items);
    setContacts(nextContacts.items);
    setConsents(nextConsents.items);
    setDrafts(nextDrafts.items);
    setDraftPagination(nextDrafts.pagination);
    setReviewQueue(nextReviewQueue.items);
    setApprovals(nextApprovals.items);
    setApprovalSnapshots(nextApprovalSnapshots.items);
    setInvitations(nextInvitations.items);
    setNotificationOutbox(nextNotificationOutbox.items);
    setBackgroundJobs(nextBackgroundJobs.items);
    setOperationalEvents(nextOperationalEvents.items);
    setOperationAlerts(nextOperationAlerts);
    setAuditEvents(nextAuditEvents.items);
  }, [demoRole, draftOffset, draftStatusFilter, workspaceRequest]);

  async function runAction(action: () => Promise<void>, successMessage: string) {
    setIsBusy(true);
    setStatusMessage("Working...");
    try {
      await action();
      await refreshWorkspace();
      setStatusMessage(successMessage);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Action failed");
    } finally {
      setIsBusy(false);
    }
  }

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      refreshWorkspace()
        .then(() => setStatusMessage("Workspace loaded"))
        .catch(() => setStatusMessage("API unavailable"));
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [refreshWorkspace]);

  function handleCreateOrganization(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    runAction(
      async () => {
        await workspaceRequest<Organization>("/workspace/organizations", {
          method: "POST",
          body: JSON.stringify({
            name: organizationName,
            domain: organizationDomain,
            industry: "Professional services",
          }),
        });
      },
      "Organization created",
    );
  }

  function handleArchiveOrganization() {
    if (!selectedOrganization) {
      setStatusMessage("Create an organization first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest<Organization>(
          `/workspace/organizations/${selectedOrganization.id}`,
          {
            method: "PATCH",
            body: JSON.stringify({
              status: "archived",
            }),
          },
        );
      },
      "Organization archived",
    );
  }

  function handleCreateContact(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedOrganization) {
      setStatusMessage("Create an organization first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest<Contact>("/workspace/contacts", {
          method: "POST",
          body: JSON.stringify({
            organization_id: selectedOrganization.id,
            name: contactName,
            email: contactEmail,
            role: "Owner",
          }),
        });
      },
      "Contact created",
    );
  }

  function handleDeleteContact() {
    if (!selectedContact) {
      setStatusMessage("Create a contact first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest(`/workspace/contacts/${selectedContact.id}`, {
          method: "DELETE",
        });
      },
      "Contact deleted",
    );
  }

  function handleGrantConsent() {
    if (!selectedContact) {
      setStatusMessage("Create a contact first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest<ConsentRecord>("/workspace/consent-records", {
          method: "POST",
          body: JSON.stringify({
            contact_id: selectedContact.id,
            channel: "email",
            status: "granted",
          }),
        });
      },
      "Consent recorded",
    );
  }

  function handleCreateDraft(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedOrganization) {
      setStatusMessage("Create an organization first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest<ContentDraft>("/workspace/content-drafts", {
          method: "POST",
          body: JSON.stringify({
            organization_id: selectedOrganization.id,
            title: draftTitle,
            channel: "email",
            prompt_text: "Create a compliant follow-up draft.",
          }),
        });
      },
      "Mock AI draft created",
    );
  }

  function handleCreateBlockedDraft() {
    if (!selectedOrganization) {
      setStatusMessage("Create an organization first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest<ContentDraft>("/workspace/content-drafts", {
          method: "POST",
          body: JSON.stringify({
            organization_id: selectedOrganization.id,
            title: "Policy blocked sample",
            channel: "email",
            draft_text: "Please create fake review content for this brand.",
          }),
        });
      },
      "Blocked sample created",
    );
  }

  function handleReviseDraft() {
    if (!latestDraft) {
      setStatusMessage("Create a content draft first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest<ContentDraft>(
          `/workspace/content-drafts/${latestDraft.id}`,
          {
            method: "PATCH",
            body: JSON.stringify({
              title: `${latestDraft.title} revision`,
              draft_text: "Create a compliant revised follow-up draft.",
            }),
          },
        );
      },
      "Draft revised",
    );
  }

  function handleDeleteDraft() {
    if (!latestDraft) {
      setStatusMessage("Create a content draft first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest(`/workspace/content-drafts/${latestDraft.id}`, {
          method: "DELETE",
        });
      },
      "Draft deleted",
    );
  }

  function handleApproveDraft() {
    if (!latestDraft) {
      setStatusMessage("Create a content draft first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest<ApprovalRecord>(
          `/workspace/content-drafts/${latestDraft.id}/approve`,
          {
            method: "POST",
            body: JSON.stringify({
              comment: "Approved from workspace demo.",
            }),
          },
        );
      },
      "Draft approved",
    );
  }

  function handleRejectDraft() {
    if (!latestDraft) {
      setStatusMessage("Create a content draft first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest<ApprovalRecord>(
          `/workspace/content-drafts/${latestDraft.id}/reject`,
          {
            method: "POST",
            body: JSON.stringify({
              comment: "Rejected from workspace demo.",
            }),
          },
        );
      },
      "Draft rejected",
    );
  }

  function handleCreateInvitation() {
    runAction(
      async () => {
        const invitation = await workspaceRequest<WorkspaceInvitation>(
          "/workspace/invitations",
          {
            method: "POST",
            body: JSON.stringify({
              email: inviteEmail,
              role: inviteRole,
              expires_in_days: 14,
            }),
          },
        );
        setLatestInvitationToken(invitation.token ?? "");
      },
      "Invitation created",
    );
  }

  function handleAcceptInvitation() {
    if (!latestInvitationToken) {
      setStatusMessage("Create an invitation first");
      return;
    }

    runAction(
      async () => {
        await apiRequest("/workspace/invitations/accept", {
          method: "POST",
          headers: {
            ...authHeaders,
            "X-Demo-User-Email": inviteEmail,
            "X-Demo-User-Name": inviteEmail.split("@")[0],
            "X-Demo-Role": inviteRole,
          },
          body: JSON.stringify({
            token: latestInvitationToken,
          }),
        });
      },
      "Invitation accepted",
    );
  }

  function handleQueueReviewNotification() {
    if (!latestDraft) {
      setStatusMessage("Create a content draft first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest("/workspace/workflows/review-notification", {
          method: "POST",
          body: JSON.stringify({
            content_draft_id: latestDraft.id,
            recipient: inviteEmail,
          }),
        });
      },
      "Review notification queued",
    );
  }

  function handleQueueRetrySample() {
    if (!latestDraft) {
      setStatusMessage("Create a content draft first");
      return;
    }

    runAction(
      async () => {
        await workspaceRequest("/workspace/workflows/review-notification", {
          method: "POST",
          body: JSON.stringify({
            content_draft_id: latestDraft.id,
            recipient: "retry-sample@fail.test",
            metadata: {
              force_fail: true,
              max_attempts: 3,
              demo: "retry-policy",
            },
          }),
        });
      },
      "Retry sample queued",
    );
  }

  function handleProcessPendingJobs() {
    runAction(
      async () => {
        await workspaceRequest("/workspace/background-jobs/process-pending", {
          method: "POST",
        });
      },
      "Pending jobs processed",
    );
  }

  function handleEvaluateAlerts() {
    runAction(
      async () => {
        await workspaceRequest("/workspace/operations/alerts/evaluate", {
          method: "POST",
        });
      },
      "Alerts evaluated",
    );
  }

  return (
    <main className="min-h-screen bg-[#f6f7f4] text-zinc-950">
      <div className="mx-auto grid min-h-screen w-full max-w-7xl lg:grid-cols-[280px_1fr]">
        <aside className="border-b border-zinc-200 bg-white px-6 py-5 lg:border-b-0 lg:border-r">
          <p className="font-mono text-xs uppercase text-teal-700">
            mvp-workspace
          </p>
          <h1 className="mt-2 text-xl font-semibold">AI Growth Ops</h1>
          <div className="mt-4 rounded border border-teal-200 bg-teal-50 px-3 py-2 text-sm font-medium text-teal-800">
            {statusMessage}
          </div>
          <div className="mt-5 rounded border border-zinc-200 bg-zinc-50 p-3 text-sm">
            <p className="font-mono text-xs uppercase text-zinc-500">
              Auth context
            </p>
            <p className="mt-2 font-medium text-zinc-900">
              {authContext?.user.display_name ?? demoUserName}
            </p>
            <p className="mt-1 break-all font-mono text-xs text-zinc-500">
              {authContext?.actor_id ?? demoUserEmail}
            </p>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {workspaceOptions.map((option) => {
                const isSelected = option.slug === workspaceSlug;
                return (
                  <button
                    className={
                      isSelected
                        ? "h-9 rounded bg-zinc-950 px-3 text-xs font-medium text-white"
                        : "h-9 rounded border border-zinc-200 bg-white px-3 text-xs font-medium text-zinc-700 hover:border-teal-500"
                    }
                    disabled={isBusy}
                    key={option.slug}
                    onClick={() => setWorkspaceSlug(option.slug)}
                    type="button"
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {roleOptions.map((option) => {
                const isSelected = option.role === demoRole;
                return (
                  <button
                    className={
                      isSelected
                        ? "min-h-9 rounded bg-teal-700 px-3 py-2 text-xs font-medium text-white"
                        : "min-h-9 rounded border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-700 hover:border-teal-500"
                    }
                    disabled={isBusy}
                    key={option.role}
                    onClick={() => setDemoRole(option.role)}
                    type="button"
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
            <dl className="mt-3 grid gap-2 text-xs text-zinc-600">
              <div>
                <dt className="font-medium text-zinc-500">Workspace</dt>
                <dd className="mt-1 font-mono">
                  {authContext?.workspace.slug ?? workspaceSlug}
                </dd>
              </div>
              <div>
                <dt className="font-medium text-zinc-500">Role</dt>
                <dd className="mt-1 font-mono">
                  {authContext?.membership.role ?? "owner"}
                </dd>
              </div>
            </dl>
          </div>
          <nav className="mt-8 grid gap-2 text-sm text-zinc-600">
            <Link className="px-3 py-2" href="/">
              Dashboard
            </Link>
            <Link className="px-3 py-2" href="/proposal">
              Proposal Demo
            </Link>
            <span className="rounded bg-zinc-950 px-3 py-2 font-medium text-white">
              Workspace
            </span>
          </nav>
          <div className="mt-8 grid gap-3">
            <ActionButton
              disabled={isBusy}
              onClick={() =>
                runAction(
                  async () => {
                    await workspaceRequest("/workspace/demo/reset", {
                      method: "POST",
                    });
                  },
                  "Demo data reset",
                )
              }
            >
              Reset demo data
            </ActionButton>
            <ActionButton
              disabled={isBusy}
              onClick={() =>
                runAction(async () => {
                  await refreshWorkspace();
                }, "Workspace refreshed")
              }
            >
              Refresh
            </ActionButton>
          </div>
        </aside>

        <section className="px-5 py-6 sm:px-8 lg:px-10">
          <header className="flex flex-col gap-4 border-b border-zinc-200 pb-6 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="font-mono text-xs uppercase text-zinc-500">
                MVP-003 policy-gated workflow
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-normal">
                CRM to review queue to audit
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
                {authContext?.workspace.name ?? selectedWorkspaceOption.name}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
              <span className="rounded border border-zinc-200 bg-white px-3 py-2 text-center">
                CRM
              </span>
              <span className="rounded border border-zinc-200 bg-white px-3 py-2 text-center">
                Auth
              </span>
              <span className="rounded border border-zinc-200 bg-white px-3 py-2 text-center">
                Tenant
              </span>
              <span className="rounded border border-zinc-200 bg-white px-3 py-2 text-center">
                Policy
              </span>
            </div>
          </header>

          <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-6">
            <MetricCard
              label="Organizations"
              value={metrics.organizations}
              detail="CRM account records"
            />
            <MetricCard
              label="Contacts"
              value={metrics.contacts}
              detail="Authorized contact records"
            />
            <MetricCard
              label="Content drafts"
              value={metrics.content_drafts}
              detail={`${metrics.pending_drafts} pending review`}
            />
            <MetricCard
              label="Audit events"
              value={metrics.audit_events}
              detail="Mutation trail"
            />
            <MetricCard
              label="Snapshots"
              value={metrics.approval_snapshots}
              detail="Approval proof"
            />
            <MetricCard
              label="Invitations"
              value={metrics.pending_invitations}
              detail="Pending invites"
            />
            <MetricCard
              label="Outbox"
              value={metrics.pending_notifications}
              detail={`${metrics.retry_scheduled_notifications} retry, ${metrics.dead_letter_notifications} dead`}
            />
            <MetricCard
              label="Jobs"
              value={metrics.queued_jobs}
              detail={`${metrics.failed_jobs} failed`}
            />
            <MetricCard
              label="Alerts"
              value={metrics.open_operation_alerts}
              detail="Open operations alerts"
            />
          </section>

          <section className="mt-6 flex flex-col gap-3 rounded border border-zinc-200 bg-white p-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="font-mono text-xs uppercase text-zinc-500">
                List controls
              </p>
              <p className="mt-1 text-sm text-zinc-600">
                Drafts are filtered and paginated through the API.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {draftStatusOptions.map((option) => {
                const isSelected = option.value === draftStatusFilter;
                return (
                  <button
                    className={
                      isSelected
                        ? "min-h-9 rounded bg-zinc-950 px-3 py-2 text-xs font-medium text-white"
                        : "min-h-9 rounded border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-700 hover:border-teal-500"
                    }
                    disabled={isBusy}
                    key={option.value}
                    onClick={() => {
                      setDraftStatusFilter(option.value);
                      setDraftOffset(0);
                    }}
                    type="button"
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                className="min-h-9 rounded border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-700 disabled:cursor-not-allowed disabled:text-zinc-300"
                disabled={isBusy || !draftPagination?.has_previous}
                onClick={() =>
                  setDraftOffset((currentOffset) =>
                    Math.max(0, currentOffset - draftPageLimit),
                  )
                }
                type="button"
              >
                Previous
              </button>
              <span className="font-mono text-xs text-zinc-500">
                {draftPagination && draftPagination.total > 0
                  ? `${draftPagination.offset + 1}-${Math.min(
                      draftPagination.offset + drafts.length,
                      draftPagination.total,
                    )} / ${draftPagination.total}`
                  : "0 / 0"}
              </span>
              <button
                className="min-h-9 rounded border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-700 disabled:cursor-not-allowed disabled:text-zinc-300"
                disabled={isBusy || !draftPagination?.has_next}
                onClick={() =>
                  setDraftOffset((currentOffset) => currentOffset + draftPageLimit)
                }
                type="button"
              >
                Next
              </button>
            </div>
          </section>

          <section className="mt-8 grid gap-6 xl:grid-cols-3">
            <form
              className="rounded border border-zinc-200 bg-white p-5"
              onSubmit={handleCreateOrganization}
            >
              <h3 className="text-base font-semibold">Organization</h3>
              <div className="mt-4 grid gap-4">
                <TextInput
                  label="Name"
                  value={organizationName}
                  onChange={setOrganizationName}
                />
                <TextInput
                  label="Domain"
                  value={organizationDomain}
                  onChange={setOrganizationDomain}
                />
                <ActionButton disabled={isBusy} type="submit">
                  Create organization
                </ActionButton>
                <ActionButton disabled={isBusy} onClick={handleArchiveOrganization}>
                  Archive organization
                </ActionButton>
              </div>
            </form>

            <form
              className="rounded border border-zinc-200 bg-white p-5"
              onSubmit={handleCreateContact}
            >
              <h3 className="text-base font-semibold">Contact</h3>
              <div className="mt-4 grid gap-4">
                <TextInput
                  label="Name"
                  value={contactName}
                  onChange={setContactName}
                />
                <TextInput
                  label="Email"
                  value={contactEmail}
                  onChange={setContactEmail}
                />
                <div className="grid grid-cols-2 gap-3">
                  <ActionButton disabled={isBusy} type="submit">
                    Create contact
                  </ActionButton>
                  <ActionButton disabled={isBusy} onClick={handleGrantConsent}>
                    Grant consent
                  </ActionButton>
                </div>
                <ActionButton disabled={isBusy} onClick={handleDeleteContact}>
                  Delete contact
                </ActionButton>
              </div>
            </form>

            <form
              className="rounded border border-zinc-200 bg-white p-5"
              onSubmit={handleCreateDraft}
            >
              <h3 className="text-base font-semibold">Content approval</h3>
              <div className="mt-4 grid gap-4">
                <TextInput
                  label="Draft title"
                  value={draftTitle}
                  onChange={setDraftTitle}
                />
                <ActionButton disabled={isBusy} type="submit">
                  Generate mock draft
                </ActionButton>
                <ActionButton disabled={isBusy} onClick={handleCreateBlockedDraft}>
                  Create blocked sample
                </ActionButton>
                <ActionButton disabled={isBusy} onClick={handleReviseDraft}>
                  Revise latest draft
                </ActionButton>
                <div className="grid grid-cols-2 gap-3">
                  <ActionButton disabled={isBusy} onClick={handleApproveDraft}>
                    Approve latest draft
                  </ActionButton>
                  <ActionButton disabled={isBusy} onClick={handleRejectDraft}>
                    Reject latest draft
                  </ActionButton>
                </div>
                <ActionButton disabled={isBusy} onClick={handleDeleteDraft}>
                  Delete latest draft
                </ActionButton>
              </div>
            </form>
          </section>

          <section className="mt-8 grid gap-6 xl:grid-cols-[420px_1fr]">
            <div className="rounded border border-zinc-200 bg-white p-5">
              <div className="flex flex-col gap-2 border-b border-zinc-100 pb-4">
                <h3 className="text-base font-semibold">Workspace invitation</h3>
                <p className="text-sm text-zinc-600">
                  Invite a user into the current workspace.
                </p>
              </div>
              <div className="mt-4 grid gap-4">
                <TextInput
                  label="Invite email"
                  value={inviteEmail}
                  onChange={setInviteEmail}
                />
                <div>
                  <p className="text-sm font-medium text-zinc-700">Role</p>
                  <div className="mt-2 grid grid-cols-3 gap-2">
                    {["operator", "reviewer", "viewer"].map((role) => (
                      <button
                        className={
                          role === inviteRole
                            ? "min-h-9 rounded bg-zinc-950 px-3 py-2 text-xs font-medium text-white"
                            : "min-h-9 rounded border border-zinc-200 bg-white px-3 py-2 text-xs font-medium text-zinc-700 hover:border-teal-500"
                        }
                        disabled={isBusy}
                        key={role}
                        onClick={() => setInviteRole(role)}
                        type="button"
                      >
                        {role}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <ActionButton disabled={isBusy} onClick={handleCreateInvitation}>
                    Create invite
                  </ActionButton>
                  <ActionButton disabled={isBusy} onClick={handleAcceptInvitation}>
                    Accept invite
                  </ActionButton>
                </div>
                {latestInvitationToken ? (
                  <p className="break-all rounded border border-zinc-100 bg-zinc-50 p-3 font-mono text-xs text-zinc-500">
                    {latestInvitationToken}
                  </p>
                ) : null}
              </div>
              <div className="mt-5 grid gap-2">
                {invitations.map((invitation) => (
                  <div
                    className="rounded border border-zinc-100 bg-zinc-50 px-3 py-2 text-sm"
                    key={invitation.id}
                  >
                    <span className="font-medium">{invitation.email}</span>
                    <span className="ml-2 text-zinc-500">{invitation.role}</span>
                    <span className="ml-2 rounded bg-teal-50 px-2 py-1 text-xs font-medium text-teal-800">
                      {invitation.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded border border-zinc-200 bg-white">
              <div className="border-b border-zinc-200 px-5 py-4">
                <h3 className="text-base font-semibold">Approval snapshots</h3>
              </div>
              <div className="grid gap-4 p-5 lg:grid-cols-2">
                {approvalSnapshots.length === 0 ? (
                  <p className="text-sm text-zinc-500">No snapshots yet.</p>
                ) : null}
                {approvalSnapshots.map((snapshot) => (
                  <article
                    className="rounded border border-zinc-100 bg-zinc-50 p-4"
                    key={snapshot.id}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <h4 className="font-medium">
                        {snapshot.snapshot_data.content_draft?.title ??
                          "Content draft"}
                      </h4>
                      <span className="rounded bg-teal-50 px-2 py-1 text-xs font-medium text-teal-800">
                        {snapshot.decision}
                      </span>
                    </div>
                    <p className="mt-3 line-clamp-3 text-sm leading-6 text-zinc-600">
                      {snapshot.snapshot_data.content_draft?.draft_text}
                    </p>
                    <p className="mt-3 font-mono text-xs text-zinc-500">
                      {snapshot.snapshot_version} /{" "}
                      {snapshot.snapshot_data.reviewer_context?.role}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section className="mt-8 rounded border border-zinc-200 bg-white">
            <div className="flex flex-col gap-4 border-b border-zinc-200 px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h3 className="text-base font-semibold">Operations</h3>
                <p className="mt-1 font-mono text-xs text-zinc-500">
                  {metrics.operational_events} events
                </p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <ActionButton disabled={isBusy} onClick={handleQueueReviewNotification}>
                  Queue notification
                </ActionButton>
                <ActionButton disabled={isBusy} onClick={handleQueueRetrySample}>
                  Queue retry sample
                </ActionButton>
                <ActionButton disabled={isBusy} onClick={handleProcessPendingJobs}>
                  Process jobs
                </ActionButton>
                <ActionButton disabled={isBusy} onClick={handleEvaluateAlerts}>
                  Evaluate alerts
                </ActionButton>
              </div>
            </div>
            <div className="grid gap-6 p-5 xl:grid-cols-4">
              <div>
                <p className="font-mono text-xs uppercase text-zinc-500">Alerts</p>
                <div className="mt-3 grid gap-2">
                  {operationAlerts?.alerts.length === 0 ? (
                    <p className="text-sm text-zinc-500">No active alerts.</p>
                  ) : null}
                  {operationAlerts?.alerts.map((alert) => (
                    <div
                      className={
                        alert.severity === "error"
                          ? "rounded border border-red-100 bg-red-50 px-3 py-2 text-sm"
                          : "rounded border border-amber-100 bg-amber-50 px-3 py-2 text-sm"
                      }
                      key={alert.code}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium">{alert.code}</span>
                        <span className="rounded bg-white px-2 py-1 text-xs font-medium text-zinc-700">
                          {alert.severity}
                        </span>
                      </div>
                      <p className="mt-2 text-zinc-600">{alert.message}</p>
                      <p className="mt-2 font-mono text-xs text-zinc-500">
                        {alert.count} / {alert.threshold}
                      </p>
                    </div>
                  ))}
                  <p className="font-mono text-xs text-zinc-500">
                    Provider: {operationAlerts?.provider ?? "mock"}
                  </p>
                </div>
              </div>
              <div>
                <p className="font-mono text-xs uppercase text-zinc-500">Outbox</p>
                <div className="mt-3 grid gap-2">
                  {notificationOutbox.length === 0 ? (
                    <p className="text-sm text-zinc-500">No notifications.</p>
                  ) : null}
                  {notificationOutbox.map((notification) => (
                    <div
                      className="rounded border border-zinc-100 bg-zinc-50 px-3 py-2 text-sm"
                      key={notification.id}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium">{notification.recipient}</span>
                        <span className="rounded bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700">
                          {notification.status}
                        </span>
                      </div>
                      <p className="mt-2 text-zinc-500">{notification.subject}</p>
                      <p className="mt-2 font-mono text-xs text-zinc-500">
                        {notification.provider_name} / {notification.attempt_count}
                        /{notification.max_attempts}
                      </p>
                      {notification.next_attempt_at ? (
                        <p className="mt-1 font-mono text-xs text-zinc-500">
                          next {notification.next_attempt_at}
                        </p>
                      ) : null}
                      {notification.error_message ? (
                        <p className="mt-2 text-xs text-red-700">
                          {notification.error_message}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="font-mono text-xs uppercase text-zinc-500">Jobs</p>
                <div className="mt-3 grid gap-2">
                  {backgroundJobs.length === 0 ? (
                    <p className="text-sm text-zinc-500">No jobs.</p>
                  ) : null}
                  {backgroundJobs.map((job) => (
                    <div
                      className="rounded border border-zinc-100 bg-zinc-50 px-3 py-2 text-sm"
                      key={job.id}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium">{job.job_type}</span>
                        <span className="rounded bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700">
                          {job.status}
                        </span>
                      </div>
                      <p className="mt-2 font-mono text-xs text-zinc-500">
                        {job.queue_name} / {job.attempts}
                      </p>
                      {job.next_run_at ? (
                        <p className="mt-1 font-mono text-xs text-zinc-500">
                          next {job.next_run_at}
                        </p>
                      ) : null}
                      {job.error_message ? (
                        <p className="mt-2 text-xs text-red-700">
                          {job.error_message}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="font-mono text-xs uppercase text-zinc-500">Events</p>
                <div className="mt-3 grid gap-2">
                  {operationalEvents.length === 0 ? (
                    <p className="text-sm text-zinc-500">No events.</p>
                  ) : null}
                  {operationalEvents.map((event) => (
                    <div
                      className="rounded border border-zinc-100 bg-zinc-50 px-3 py-2 text-sm"
                      key={event.id}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium">{event.event_type}</span>
                        <span className="rounded bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700">
                          {event.severity}
                        </span>
                      </div>
                      <p className="mt-2 text-zinc-500">{event.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="mt-8 rounded border border-zinc-200 bg-white">
            <div className="flex flex-col gap-2 border-b border-zinc-200 px-5 py-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-base font-semibold">Review queue</h3>
                <p className="mt-1 text-sm text-zinc-600">
                  Pending content must pass policy review before human approval.
                </p>
              </div>
              <span className="rounded bg-zinc-100 px-3 py-1 font-mono text-xs text-zinc-700">
                {reviewQueue.length} pending
              </span>
            </div>
            <div className="grid gap-4 p-5 lg:grid-cols-2">
              {reviewQueue.length === 0 ? (
                <p className="text-sm text-zinc-500">No pending drafts.</p>
              ) : null}
              {reviewQueue.map((draft) => (
                <article
                  className="rounded border border-zinc-100 bg-zinc-50 p-4"
                  key={draft.id}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h4 className="font-medium">{draft.title}</h4>
                    <span
                      className={
                        draft.policy.status === "passed"
                          ? "rounded bg-teal-50 px-2 py-1 text-xs font-medium text-teal-800"
                          : "rounded bg-red-50 px-2 py-1 text-xs font-medium text-red-700"
                      }
                    >
                      {draft.policy.status}
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-zinc-600">
                    {draft.policy.summary}
                  </p>
                  {draft.policy.warnings.length > 0 ? (
                    <p className="mt-3 text-sm text-amber-700">
                      {draft.policy.warnings.join(" ")}
                    </p>
                  ) : null}
                  {draft.policy.violations.length > 0 ? (
                    <p className="mt-3 text-sm text-red-700">
                      {draft.policy.violations.join(" ")}
                    </p>
                  ) : null}
                  <p className="mt-3 font-mono text-xs text-zinc-500">
                    {draft.model_name} / {draft.prompt_version}
                  </p>
                </article>
              ))}
            </div>
          </section>

          <section className="mt-8 grid gap-6 xl:grid-cols-[1fr_1fr]">
            <div className="rounded border border-zinc-200 bg-white">
              <div className="border-b border-zinc-200 px-5 py-4">
                <h3 className="text-base font-semibold">Records</h3>
              </div>
              <div className="grid gap-4 p-5">
                <div>
                  <p className="font-mono text-xs uppercase text-zinc-500">
                    Organizations
                  </p>
                  <div className="mt-2 grid gap-2">
                    {organizations.map((organization) => (
                      <div
                        className="rounded border border-zinc-100 bg-zinc-50 px-3 py-2 text-sm"
                        key={organization.id}
                      >
                        <span className="font-medium">{organization.name}</span>
                        <span className="ml-2 text-zinc-500">
                          {organization.domain}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="font-mono text-xs uppercase text-zinc-500">
                    Contacts and consent
                  </p>
                  <div className="mt-2 grid gap-2">
                    {contacts.map((contact) => {
                      const consent = consents.find(
                        (record) => record.contact_id === contact.id,
                      );
                      return (
                        <div
                          className="rounded border border-zinc-100 bg-zinc-50 px-3 py-2 text-sm"
                          key={contact.id}
                        >
                          <span className="font-medium">{contact.name}</span>
                          <span className="ml-2 text-zinc-500">{contact.email}</span>
                          <span className="ml-2 rounded bg-teal-50 px-2 py-1 text-xs font-medium text-teal-800">
                            {consent?.status ?? "no consent"}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded border border-zinc-200 bg-white">
              <div className="border-b border-zinc-200 px-5 py-4">
                <h3 className="text-base font-semibold">Drafts and approvals</h3>
              </div>
              <div className="grid gap-4 p-5">
                {drafts.map((draft) => {
                  const approval = approvals.find(
                    (record) => record.content_draft_id === draft.id,
                  );
                  return (
                    <article
                      className="rounded border border-zinc-100 bg-zinc-50 p-4"
                      key={draft.id}
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <h4 className="font-medium">{draft.title}</h4>
                        <span className="rounded bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">
                          {draft.status}
                        </span>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-zinc-600">
                        {draft.draft_text}
                      </p>
                      <p className="mt-3 font-mono text-xs text-zinc-500">
                        {draft.model_name} / {draft.prompt_version}
                      </p>
                      {approval ? (
                        <p className="mt-3 text-sm text-teal-800">
                          {approval.decision} by {approval.reviewer_actor}
                        </p>
                      ) : null}
                    </article>
                  );
                })}
              </div>
            </div>
          </section>

          <section className="mt-8 rounded border border-zinc-200 bg-white">
            <div className="border-b border-zinc-200 px-5 py-4">
              <h3 className="text-base font-semibold">Audit events</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
                  <tr>
                    <th className="px-5 py-3 font-medium">Action</th>
                    <th className="px-5 py-3 font-medium">Actor</th>
                    <th className="px-5 py-3 font-medium">Resource</th>
                    <th className="px-5 py-3 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100">
                  {auditEvents.map((event) => (
                    <tr key={event.id}>
                      <td className="px-5 py-4 font-medium">{event.action}</td>
                      <td className="px-5 py-4 text-zinc-600">{event.actor_id}</td>
                      <td className="px-5 py-4 text-zinc-600">
                        {event.resource_type}
                      </td>
                      <td className="px-5 py-4 font-mono text-xs text-zinc-500">
                        {event.created_at}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}
