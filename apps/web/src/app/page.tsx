import { HomeClient, type WorkspaceMetrics } from "./home-client";

export const dynamic = "force-dynamic";

async function getWorkspaceMetrics(): Promise<WorkspaceMetrics> {
  const apiBaseUrl =
    process.env.API_INTERNAL_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000";

  try {
    const response = await fetch(`${apiBaseUrl}/workspace/metrics`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Metrics API returned ${response.status}`);
    }

    return (await response.json()) as WorkspaceMetrics;
  } catch {
    return {
      organizations: 0,
      contacts: 0,
      consent_records: 0,
      content_drafts: 0,
      approved_drafts: 0,
      audit_events: 0,
    };
  }
}

export default async function Home() {
  const metrics = await getWorkspaceMetrics();

  return <HomeClient metrics={metrics} />;
}
