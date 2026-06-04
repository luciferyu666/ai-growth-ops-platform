"use client";

import Link from "next/link";
import { useState } from "react";

export type WorkspaceMetrics = {
  organizations: number;
  contacts: number;
  consent_records: number;
  content_drafts: number;
  approved_drafts: number;
  audit_events: number;
};

type Locale = "en" | "zh-Hant";

type MetricCardConfig = {
  label: string;
  value: number;
  detail: string;
  accent: string;
};

type HomeCopy = {
  statusBadge: string;
  language: string;
  navOperations: string;
  navProposalDemo: string;
  navWorkspace: string;
  navLeads: string;
  navApprovals: string;
  navSignals: string;
  navAudit: string;
  workspaceStatus: string;
  title: string;
  workspaceButton: string;
  proposalButton: string;
  serviceMap: string;
  service: string;
  stack: string;
  state: string;
  route: string;
  workflowBaseline: string;
  metricLabels: {
    organizations: string;
    contacts: string;
    contentDrafts: string;
    auditEvents: string;
  };
  metricDetails: {
    organizations: string;
    contacts: string;
    contentDrafts: (approvedDrafts: number) => string;
    auditEvents: string;
  };
  serviceRows: string[][];
  workflowRows: string[][];
};

const homeCopy: Record<Locale, HomeCopy> = {
  en: {
    statusBadge: "Foundation",
    language: "Language",
    navOperations: "Operations",
    navProposalDemo: "Proposal Demo",
    navWorkspace: "Workspace",
    navLeads: "Leads",
    navApprovals: "Approvals",
    navSignals: "Signals",
    navAudit: "Audit",
    workspaceStatus: "Workspace status",
    title: "Engineering foundation",
    workspaceButton: "Workspace",
    proposalButton: "Proposal",
    serviceMap: "Service map",
    service: "Service",
    stack: "Stack",
    state: "State",
    route: "Route",
    workflowBaseline: "Workflow baseline",
    metricLabels: {
      organizations: "Organizations",
      contacts: "Contacts",
      contentDrafts: "Content drafts",
      auditEvents: "Audit events",
    },
    metricDetails: {
      organizations: "CRM account records",
      contacts: "Authorized contact records",
      contentDrafts: (approvedDrafts) => `${approvedDrafts} approved`,
      auditEvents: "Mutation trail",
    },
    serviceRows: [
      ["Web", "Next.js", "Scaffolded", "localhost:3000"],
      ["API", "FastAPI", "Health route", "localhost:8000/health"],
      ["Database", "PostgreSQL", "Compose service", "localhost:5433"],
      ["Queue", "Redis + Celery", "Compose service", "localhost:6379"],
    ],
    workflowRows: [
      ["CRM account", "Organization and contact APIs", "Available"],
      ["Consent gate", "Channel-level consent record", "Available"],
      ["Content draft", "Mock AI draft generation", "Available"],
      ["Approval gate", "Approve and audit workflow", "Available"],
    ],
  },
  "zh-Hant": {
    statusBadge: "工程底座",
    language: "語系",
    navOperations: "營運總覽",
    navProposalDemo: "提案展示",
    navWorkspace: "工作區",
    navLeads: "名單",
    navApprovals: "審核",
    navSignals: "訊號",
    navAudit: "稽核",
    workspaceStatus: "工作區狀態",
    title: "工程基礎",
    workspaceButton: "工作區",
    proposalButton: "提案",
    serviceMap: "服務地圖",
    service: "服務",
    stack: "技術棧",
    state: "狀態",
    route: "路由",
    workflowBaseline: "工作流基準",
    metricLabels: {
      organizations: "組織",
      contacts: "聯絡人",
      contentDrafts: "內容草稿",
      auditEvents: "稽核事件",
    },
    metricDetails: {
      organizations: "CRM 帳戶資料",
      contacts: "授權聯絡人資料",
      contentDrafts: (approvedDrafts) => `${approvedDrafts} 已核准`,
      auditEvents: "異動紀錄",
    },
    serviceRows: [
      ["Web", "Next.js", "已建立骨架", "localhost:3000"],
      ["API", "FastAPI", "健康檢查路由", "localhost:8000/health"],
      ["Database", "PostgreSQL", "Compose 服務", "localhost:5433"],
      ["Queue", "Redis + Celery", "Compose 服務", "localhost:6379"],
    ],
    workflowRows: [
      ["CRM 帳戶", "Organization 與 contact APIs", "可用"],
      ["同意閘門", "通道層級 consent record", "可用"],
      ["內容草稿", "Mock AI draft generation", "可用"],
      ["審核閘門", "Approve 與 audit workflow", "可用"],
    ],
  },
};

function LanguageSwitch({
  locale,
  onLocaleChange,
}: Readonly<{
  locale: Locale;
  onLocaleChange: (locale: Locale) => void;
}>) {
  return (
    <div className="mt-5">
      <p className="font-mono text-xs uppercase text-zinc-500">
        {homeCopy[locale].language}
      </p>
      <div className="mt-2 grid grid-cols-2 rounded border border-zinc-200 bg-zinc-50 p-1">
        {[
          { locale: "en" as const, label: "EN" },
          { locale: "zh-Hant" as const, label: "繁中" },
        ].map((option) => (
          <button
            aria-pressed={locale === option.locale}
            className={
              locale === option.locale
                ? "min-h-9 rounded bg-zinc-950 px-3 py-2 text-sm font-medium text-white"
                : "min-h-9 rounded px-3 py-2 text-sm font-medium text-zinc-600 hover:text-zinc-950"
            }
            key={option.locale}
            onClick={() => onLocaleChange(option.locale)}
            type="button"
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export function HomeClient({
  metrics,
}: Readonly<{
  metrics: WorkspaceMetrics;
}>) {
  const [locale, setLocale] = useState<Locale>("en");
  const copy = homeCopy[locale];
  const metricCards: MetricCardConfig[] = [
    {
      label: copy.metricLabels.organizations,
      value: metrics.organizations,
      detail: copy.metricDetails.organizations,
      accent: "border-teal-500",
    },
    {
      label: copy.metricLabels.contacts,
      value: metrics.contacts,
      detail: copy.metricDetails.contacts,
      accent: "border-amber-500",
    },
    {
      label: copy.metricLabels.contentDrafts,
      value: metrics.content_drafts,
      detail: copy.metricDetails.contentDrafts(metrics.approved_drafts),
      accent: "border-indigo-500",
    },
    {
      label: copy.metricLabels.auditEvents,
      value: metrics.audit_events,
      detail: copy.metricDetails.auditEvents,
      accent: "border-rose-500",
    },
  ];

  return (
    <main className="min-h-screen bg-[#f6f7f4] text-zinc-950" lang={locale}>
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col lg:flex-row">
        <aside className="border-b border-zinc-200 bg-white px-6 py-5 lg:w-64 lg:border-b-0 lg:border-r">
          <div className="flex items-center justify-between gap-4 lg:block">
            <div>
              <p className="font-mono text-xs uppercase text-teal-700">
                growth-ops
              </p>
              <h1 className="mt-2 text-xl font-semibold">AI Growth Ops</h1>
            </div>
            <div className="rounded border border-teal-200 bg-teal-50 px-3 py-1 text-sm font-medium text-teal-800">
              {copy.statusBadge}
            </div>
          </div>

          <LanguageSwitch locale={locale} onLocaleChange={setLocale} />

          <nav className="mt-8 grid gap-2 text-sm text-zinc-600">
            <span className="rounded bg-zinc-950 px-3 py-2 font-medium text-white">
              {copy.navOperations}
            </span>
            <Link className="px-3 py-2" href="/proposal">
              {copy.navProposalDemo}
            </Link>
            <Link className="px-3 py-2" href="/workspace">
              {copy.navWorkspace}
            </Link>
            <span className="px-3 py-2">{copy.navLeads}</span>
            <span className="px-3 py-2">{copy.navApprovals}</span>
            <span className="px-3 py-2">{copy.navSignals}</span>
            <span className="px-3 py-2">{copy.navAudit}</span>
          </nav>
        </aside>

        <section className="flex-1 px-5 py-6 sm:px-8 lg:px-10">
          <header className="flex flex-col gap-4 border-b border-zinc-200 pb-6 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="font-mono text-xs uppercase text-zinc-500">
                {copy.workspaceStatus}
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-normal">
                {copy.title}
              </h2>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
              <Link
                className="rounded border border-zinc-200 bg-white px-3 py-2 text-center transition-colors hover:border-teal-500"
                href="/workspace"
              >
                {copy.workspaceButton}
              </Link>
              <Link
                className="rounded border border-zinc-200 bg-white px-3 py-2 text-center transition-colors hover:border-teal-500"
                href="/proposal"
              >
                {copy.proposalButton}
              </Link>
              <span className="rounded border border-zinc-200 bg-white px-3 py-2 text-center">
                Next.js
              </span>
              <span className="rounded border border-zinc-200 bg-white px-3 py-2 text-center">
                FastAPI
              </span>
              <span className="rounded border border-zinc-200 bg-white px-3 py-2 text-center">
                PostgreSQL
              </span>
            </div>
          </header>

          <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {metricCards.map((metric) => (
              <article
                className={`min-h-36 rounded border bg-white p-5 shadow-sm ${metric.accent}`}
                key={metric.label}
              >
                <p className="text-sm text-zinc-500">{metric.label}</p>
                <p className="mt-5 font-mono text-4xl font-semibold">
                  {metric.value}
                </p>
                <p className="mt-4 text-sm text-zinc-600">{metric.detail}</p>
              </article>
            ))}
          </section>

          <section className="mt-8 grid gap-6 xl:grid-cols-[1fr_1.2fr]">
            <div className="rounded border border-zinc-200 bg-white">
              <div className="border-b border-zinc-200 px-5 py-4">
                <h3 className="text-base font-semibold">{copy.serviceMap}</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[520px] text-left text-sm">
                  <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
                    <tr>
                      <th className="px-5 py-3 font-medium">{copy.service}</th>
                      <th className="px-5 py-3 font-medium">{copy.stack}</th>
                      <th className="px-5 py-3 font-medium">{copy.state}</th>
                      <th className="px-5 py-3 font-medium">{copy.route}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100">
                    {copy.serviceRows.map(([service, stack, state, route]) => (
                      <tr key={service}>
                        <td className="px-5 py-4 font-medium">{service}</td>
                        <td className="px-5 py-4 text-zinc-600">{stack}</td>
                        <td className="px-5 py-4">
                          <span className="rounded bg-teal-50 px-2 py-1 text-xs font-medium text-teal-800">
                            {state}
                          </span>
                        </td>
                        <td className="px-5 py-4 font-mono text-xs text-zinc-500">
                          {route}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="rounded border border-zinc-200 bg-white">
              <div className="border-b border-zinc-200 px-5 py-4">
                <h3 className="text-base font-semibold">
                  {copy.workflowBaseline}
                </h3>
              </div>
              <div className="divide-y divide-zinc-100">
                {copy.workflowRows.map(([name, next, state]) => (
                  <article
                    className="grid gap-3 px-5 py-4 sm:grid-cols-[1fr_1.4fr_auto] sm:items-center"
                    key={name}
                  >
                    <p className="font-medium">{name}</p>
                    <p className="text-sm text-zinc-600">{next}</p>
                    <span className="w-fit rounded bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">
                      {state}
                    </span>
                  </article>
                ))}
              </div>
            </div>
          </section>
        </section>
      </div>
    </main>
  );
}
