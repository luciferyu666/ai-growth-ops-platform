"use client";

import { useMemo, useState } from "react";

export type ReadinessItem = {
  label: string;
  score: number;
  status: string;
  evidence: string;
};

export type CapabilityItem = {
  area: string;
  proof: string;
  state: string;
};

export type ArchitectureItem = {
  service: string;
  stack: string;
  demo_value: string;
};

export type RoadmapItem = {
  phase: string;
  name: string;
  timeline: string;
  outcome: string;
  deliverables: string[];
};

export type ProposalDemo = {
  title: string;
  subtitle: string;
  positioning: {
    primary: string;
    not_claiming: string[];
    recommended_talk_track: string;
  };
  readiness: ReadinessItem[];
  capabilities: CapabilityItem[];
  architecture: ArchitectureItem[];
  roadmap: RoadmapItem[];
  demo_script: string[];
  compliance_boundary: {
    allowed: string[];
    excluded: string[];
  };
};

type ProposalSource = "api" | "fallback";
type Locale = "en" | "zh-Hant";

type UiCopy = {
  sourceApi: string;
  sourceFallback: string;
  technicalDemo: string;
  navSummary: string;
  navCapabilities: string;
  navArchitecture: string;
  navRoadmap: string;
  navDemoScript: string;
  language: string;
  eyebrow: string;
  positioning: string;
  notClaiming: string;
  capabilityProof: string;
  complianceBoundary: string;
  allowed: string;
  excluded: string;
  architectureMap: string;
  service: string;
  stack: string;
  demoValue: string;
  roadmapEyebrow: string;
  roadmapTitle: string;
  proposalPath: string;
  suggestedDemoScript: string;
};

const uiCopy: Record<Locale, UiCopy> = {
  en: {
    sourceApi: "Live API",
    sourceFallback: "Fallback data",
    technicalDemo: "Technical demo",
    navSummary: "Summary",
    navCapabilities: "Capabilities",
    navArchitecture: "Architecture",
    navRoadmap: "Roadmap",
    navDemoScript: "Demo Script",
    language: "Language",
    eyebrow: "Technical proposal demo",
    positioning: "Positioning",
    notClaiming: "Not claiming",
    capabilityProof: "Capability proof",
    complianceBoundary: "Compliance boundary",
    allowed: "Allowed",
    excluded: "Excluded",
    architectureMap: "Architecture map",
    service: "Service",
    stack: "Stack",
    demoValue: "Demo value",
    roadmapEyebrow: "Productization roadmap",
    roadmapTitle: "From technical proof to compliant SaaS product",
    proposalPath: "Proposal path",
    suggestedDemoScript: "Suggested demo script",
  },
  "zh-Hant": {
    sourceApi: "即時 API",
    sourceFallback: "備援資料",
    technicalDemo: "技術展示",
    navSummary: "摘要",
    navCapabilities: "能力證明",
    navArchitecture: "架構",
    navRoadmap: "路線圖",
    navDemoScript: "展示腳本",
    language: "語系",
    eyebrow: "技術提案展示版",
    positioning: "展示定位",
    notClaiming: "不宣稱事項",
    capabilityProof: "技術能力證明",
    complianceBoundary: "合規邊界",
    allowed: "允許範圍",
    excluded: "排除範圍",
    architectureMap: "架構地圖",
    service: "服務",
    stack: "技術棧",
    demoValue: "展示價值",
    roadmapEyebrow: "產品化路線",
    roadmapTitle: "從技術驗證走向合規 SaaS 產品",
    proposalPath: "提案路徑",
    suggestedDemoScript: "建議展示腳本",
  },
};

const zhFallback: ProposalDemo = {
  title: "技術提案展示版",
  subtitle: "合規 AI Growth Ops SaaS 工程基礎",
  positioning: {
    primary: "技術能力與交付能力展示",
    not_claiming: [
      "完整正式產品已完成",
      "CRM 工作流已完整商用",
      "AI 內容工作流已完整商用",
      "平台規避、假評論或帳號自動化",
    ],
    recommended_talk_track:
      "此展示用來證明團隊能設計並交付可維護的合規 AI 成長營運 SaaS 基礎。展示重點是架構、稽核優先的資料模型、可執行服務與產品化路線，而不是宣稱所有商業功能已完成。",
  },
  readiness: [
    {
      label: "工程基礎",
      score: 65,
      status: "可技術展示",
      evidence: "Web、API、DB、Redis、worker、Docker Compose、測試",
    },
    {
      label: "合規一致性",
      score: 70,
      status: "可提案展示",
      evidence: "明確允許/排除邊界與 audit schema",
    },
    {
      label: "商業 MVP",
      score: 10,
      status: "尚未啟動",
      evidence: "已有領域資料表；完整使用者流程仍待產品化",
    },
    {
      label: "展示信心",
      score: 55,
      status: "技術展示版",
      evidence: "適合架構審查與交付能力評估",
    },
  ],
  capabilities: [
    {
      area: "系統架構能力",
      proof: "ADR 驅動的 monorepo，清楚分離 web、API、infra 與 docs",
      state: "已展示",
    },
    {
      area: "SaaS 應用基礎",
      proof: "Next.js dashboard、FastAPI service、PostgreSQL、Redis、Celery",
      state: "已展示",
    },
    {
      area: "資料治理",
      proof: "同意紀錄、審核紀錄與 append-oriented audit events",
      state: "底座完成",
    },
    {
      area: "AI 工作流準備度",
      proof: "內容草稿 schema 已保留 prompt version 與 model metadata",
      state: "已設計尚未接正式模型",
    },
    {
      area: "交付與維運",
      proof: "Docker Compose runtime、tests、lint、migrations、health checks",
      state: "已展示",
    },
  ],
  architecture: [
    {
      service: "Web",
      stack: "Next.js 16 + TypeScript + Tailwind CSS",
      demo_value: "操作 dashboard 與提案展示介面",
    },
    {
      service: "API",
      stack: "FastAPI + Python 3.12",
      demo_value: "結構化提案資料、health checks 與後續 domain APIs",
    },
    {
      service: "Database",
      stack: "PostgreSQL + SQLAlchemy + Alembic",
      demo_value: "CRM、同意、審核、草稿與稽核紀錄的持久化基礎",
    },
    {
      service: "Automation",
      stack: "Redis + Celery",
      demo_value: "排程匯入、AI jobs 與報表工作流基礎",
    },
  ],
  roadmap: [
    {
      phase: "第一階段",
      name: "Demo vertical slice",
      timeline: "1-2 週",
      outcome: "CRM 到內容審核再到 audit event 的端到端流程",
      deliverables: [
        "Organization 與 contact CRUD",
        "Consent record workflow",
        "Mock AI provider 內容草稿流程",
        "Approve / reject workflow",
        "Dashboard metrics 讀取真實 API 資料",
      ],
    },
    {
      phase: "第二階段",
      name: "AI workflow productization",
      timeline: "2-4 週",
      outcome: "Prompt templates、provider abstraction 與審核控制",
      deliverables: [
        "LLM provider adapter",
        "Prompt versioning",
        "Generated content audit trail",
        "Human approval policy",
        "品質與合規檢查",
      ],
    },
    {
      phase: "第三階段",
      name: "SaaS readiness",
      timeline: "4-6 週",
      outcome: "多使用者、權限化、可部署的平台",
      deliverables: [
        "Authentication and RBAC",
        "Tenant / workspace model",
        "Production deployment pipeline",
        "Observability and error monitoring",
        "Backup and data retention plan",
      ],
    },
    {
      phase: "第四階段",
      name: "Growth integrations",
      timeline: "6 週以上",
      outcome: "合規 API 整合與報表工作流",
      deliverables: [
        "Official API integrations",
        "Authorized data import flows",
        "Review invitation management",
        "Brand signal monitoring",
        "Executive reporting",
      ],
    },
  ],
  demo_script: [
    "開啟技術提案展示版頁面。",
    "展示 API-backed 提案資料與 readiness scores。",
    "說明系統架構圖與 health checks。",
    "說明合規邊界，以及產品刻意排除的行為。",
    "走過產品化路線與下一個 vertical slice。",
    "最後明確定位：這是交付能力展示，不是完整產品完工宣稱。",
  ],
  compliance_boundary: {
    allowed: [
      "官方 API 整合",
      "授權資料匯入",
      "基於同意的工作流",
      "人工審核的 AI 內容草稿",
      "真實客戶評論邀請流程",
      "Audit logs 與資料治理",
    ],
    excluded: [
      "假評論",
      "未授權爬取",
      "帳號養號或帳號農場",
      "平台風控規避",
      "CAPTCHA、OTP 或活體檢測繞過",
      "未經同意的大量訊息發送",
    ],
  },
};

function localizeProposal(data: ProposalDemo, locale: Locale): ProposalDemo {
  if (locale === "en") {
    return data;
  }

  return {
    ...zhFallback,
    readiness: zhFallback.readiness.map((item, index) => ({
      ...item,
      score: data.readiness[index]?.score ?? item.score,
    })),
  };
}

function StatusBadge({
  children,
  tone = "neutral",
}: Readonly<{
  children: React.ReactNode;
  tone?: "neutral" | "good" | "warning";
}>) {
  const toneClass = {
    neutral: "border-zinc-200 bg-white text-zinc-700",
    good: "border-teal-200 bg-teal-50 text-teal-800",
    warning: "border-amber-200 bg-amber-50 text-amber-800",
  }[tone];

  return (
    <span className={`rounded border px-2 py-1 text-xs font-medium ${toneClass}`}>
      {children}
    </span>
  );
}

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
        {uiCopy[locale].language}
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

export function ProposalClient({
  data,
  source,
}: Readonly<{
  data: ProposalDemo;
  source: ProposalSource;
}>) {
  const [locale, setLocale] = useState<Locale>("en");
  const copy = uiCopy[locale];
  const localizedData = useMemo(
    () => localizeProposal(data, locale),
    [data, locale],
  );

  return (
    <main className="min-h-screen bg-[#f6f7f4] text-zinc-950" lang={locale}>
      <div className="mx-auto grid min-h-screen w-full max-w-7xl lg:grid-cols-[280px_1fr]">
        <aside className="border-b border-zinc-200 bg-white px-6 py-5 lg:border-b-0 lg:border-r">
          <p className="font-mono text-xs uppercase text-teal-700">
            proposal-demo
          </p>
          <h1 className="mt-2 text-xl font-semibold">AI Growth Ops</h1>
          <div className="mt-4 flex flex-wrap gap-2">
            <StatusBadge tone={source === "api" ? "good" : "warning"}>
              {source === "api" ? copy.sourceApi : copy.sourceFallback}
            </StatusBadge>
            <StatusBadge>{copy.technicalDemo}</StatusBadge>
          </div>

          <LanguageSwitch locale={locale} onLocaleChange={setLocale} />

          <nav className="mt-8 grid gap-2 text-sm text-zinc-600">
            <a
              className="rounded bg-zinc-950 px-3 py-2 font-medium text-white"
              href="#summary"
            >
              {copy.navSummary}
            </a>
            <a className="px-3 py-2" href="#capabilities">
              {copy.navCapabilities}
            </a>
            <a className="px-3 py-2" href="#architecture">
              {copy.navArchitecture}
            </a>
            <a className="px-3 py-2" href="#roadmap">
              {copy.navRoadmap}
            </a>
            <a className="px-3 py-2" href="#demo-script">
              {copy.navDemoScript}
            </a>
          </nav>
        </aside>

        <section className="px-5 py-6 sm:px-8 lg:px-10">
          <section
            id="summary"
            className="grid gap-6 border-b border-zinc-200 pb-8 xl:grid-cols-[1.2fr_0.8fr]"
          >
            <div>
              <p className="font-mono text-xs uppercase text-zinc-500">
                {copy.eyebrow}
              </p>
              <h2 className="mt-3 max-w-3xl text-3xl font-semibold tracking-normal">
                {localizedData.title}
              </h2>
              <p className="mt-3 max-w-3xl text-base leading-7 text-zinc-600">
                {localizedData.subtitle}
              </p>
              <p className="mt-6 max-w-3xl border-l-4 border-teal-500 pl-4 text-sm leading-6 text-zinc-700">
                {localizedData.positioning.recommended_talk_track}
              </p>
            </div>

            <div className="rounded border border-zinc-200 bg-white p-5">
              <h3 className="text-base font-semibold">{copy.positioning}</h3>
              <p className="mt-3 text-sm text-zinc-600">
                {localizedData.positioning.primary}
              </p>
              <div className="mt-5">
                <p className="font-mono text-xs uppercase text-zinc-500">
                  {copy.notClaiming}
                </p>
                <ul className="mt-3 grid gap-2 text-sm text-zinc-700">
                  {localizedData.positioning.not_claiming.map((item) => (
                    <li key={item} className="rounded bg-zinc-50 px-3 py-2">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>

          <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {localizedData.readiness.map((item) => (
              <article
                className="rounded border border-zinc-200 bg-white p-5"
                key={item.label}
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium text-zinc-600">
                    {item.label}
                  </p>
                  <StatusBadge tone={item.score >= 55 ? "good" : "warning"}>
                    {item.status}
                  </StatusBadge>
                </div>
                <p className="mt-5 font-mono text-4xl font-semibold">
                  {item.score}%
                </p>
                <div className="mt-4 h-2 rounded bg-zinc-100">
                  <div
                    className="h-2 rounded bg-teal-600"
                    style={{ width: `${Math.min(item.score, 100)}%` }}
                  />
                </div>
                <p className="mt-4 text-sm leading-6 text-zinc-600">
                  {item.evidence}
                </p>
              </article>
            ))}
          </section>

          <section id="capabilities" className="mt-8 grid gap-6 xl:grid-cols-2">
            <div className="rounded border border-zinc-200 bg-white">
              <div className="border-b border-zinc-200 px-5 py-4">
                <h3 className="text-base font-semibold">{copy.capabilityProof}</h3>
              </div>
              <div className="divide-y divide-zinc-100">
                {localizedData.capabilities.map((item) => (
                  <article
                    className="grid gap-3 px-5 py-4 sm:grid-cols-[0.8fr_1.4fr_auto] sm:items-center"
                    key={item.area}
                  >
                    <p className="font-medium">{item.area}</p>
                    <p className="text-sm leading-6 text-zinc-600">
                      {item.proof}
                    </p>
                    <StatusBadge>{item.state}</StatusBadge>
                  </article>
                ))}
              </div>
            </div>

            <div className="rounded border border-zinc-200 bg-white">
              <div className="border-b border-zinc-200 px-5 py-4">
                <h3 className="text-base font-semibold">
                  {copy.complianceBoundary}
                </h3>
              </div>
              <div className="grid gap-4 p-5 md:grid-cols-2">
                <div>
                  <p className="font-mono text-xs uppercase text-teal-700">
                    {copy.allowed}
                  </p>
                  <ul className="mt-3 grid gap-2 text-sm text-zinc-700">
                    {localizedData.compliance_boundary.allowed.map((item) => (
                      <li key={item} className="rounded bg-teal-50 px-3 py-2">
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="font-mono text-xs uppercase text-rose-700">
                    {copy.excluded}
                  </p>
                  <ul className="mt-3 grid gap-2 text-sm text-zinc-700">
                    {localizedData.compliance_boundary.excluded.map((item) => (
                      <li key={item} className="rounded bg-rose-50 px-3 py-2">
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </section>

          <section
            className="mt-8 rounded border border-zinc-200 bg-white"
            id="architecture"
          >
            <div className="border-b border-zinc-200 px-5 py-4">
              <h3 className="text-base font-semibold">{copy.architectureMap}</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
                  <tr>
                    <th className="px-5 py-3 font-medium">{copy.service}</th>
                    <th className="px-5 py-3 font-medium">{copy.stack}</th>
                    <th className="px-5 py-3 font-medium">{copy.demoValue}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100">
                  {localizedData.architecture.map((item) => (
                    <tr key={item.service}>
                      <td className="px-5 py-4 font-medium">{item.service}</td>
                      <td className="px-5 py-4 font-mono text-xs text-zinc-600">
                        {item.stack}
                      </td>
                      <td className="px-5 py-4 text-zinc-600">
                        {item.demo_value}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="mt-8" id="roadmap">
            <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="font-mono text-xs uppercase text-zinc-500">
                  {copy.roadmapEyebrow}
                </p>
                <h3 className="mt-2 text-xl font-semibold">
                  {copy.roadmapTitle}
                </h3>
              </div>
              <StatusBadge tone="good">{copy.proposalPath}</StatusBadge>
            </div>
            <div className="grid gap-4 xl:grid-cols-4">
              {localizedData.roadmap.map((item) => (
                <article
                  className="rounded border border-zinc-200 bg-white p-5"
                  key={`${item.phase}-${item.name}`}
                >
                  <p className="font-mono text-xs uppercase text-teal-700">
                    {item.phase}
                  </p>
                  <h4 className="mt-3 text-base font-semibold">{item.name}</h4>
                  <p className="mt-2 text-sm font-medium text-zinc-500">
                    {item.timeline}
                  </p>
                  <p className="mt-4 text-sm leading-6 text-zinc-600">
                    {item.outcome}
                  </p>
                  <ul className="mt-4 grid gap-2 text-sm text-zinc-700">
                    {item.deliverables.map((deliverable) => (
                      <li
                        className="border-l-2 border-zinc-200 pl-3"
                        key={deliverable}
                      >
                        {deliverable}
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </section>

          <section
            className="mt-8 rounded border border-zinc-200 bg-white"
            id="demo-script"
          >
            <div className="border-b border-zinc-200 px-5 py-4">
              <h3 className="text-base font-semibold">
                {copy.suggestedDemoScript}
              </h3>
            </div>
            <ol className="grid gap-3 p-5 text-sm text-zinc-700 md:grid-cols-2">
              {localizedData.demo_script.map((item, index) => (
                <li className="grid grid-cols-[32px_1fr] gap-3" key={item}>
                  <span className="flex h-8 w-8 items-center justify-center rounded bg-zinc-950 font-mono text-xs text-white">
                    {index + 1}
                  </span>
                  <span className="pt-1.5 leading-6">{item}</span>
                </li>
              ))}
            </ol>
          </section>
        </section>
      </div>
    </main>
  );
}
