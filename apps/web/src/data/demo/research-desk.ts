export type ResearchCandidate = {
  id: string;
  entity: string;
  title: string;
  firstSeen: string;
  source: string;
  sourceType: string;
  primary: "FOUND" | "NOT FOUND" | "CHECKING";
  novelty: "NEW" | "UPDATE" | "DUPLICATE" | "RELATED";
  materiality: "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";
  verification: string;
  status: "NEW" | "VERIFYING" | "RIGHTS REVIEW" | "CONTRADICTION";
  existing: string;
  notes: string;
  provenance: string;
};

export const researchDesk = {
  lastRun: "31 Aug 2026 · 18:00 IST",
  nextRun: "01 Sep 2026 · 07:45 IST",
  metrics: [
    ["Candidates today", "7"], ["Primary sources", "3"],
    ["Duplicates avoided", "18"], ["Pending review", "5"],
  ],
  candidates: [
    {
      id: "RC-0261", entity: "Reserve Bank of India",
      title: "Liquidity operation requires policy-context verification",
      firstSeen: "17:44 IST", source: "rbi.org.in", sourceType: "PRIMARY_REGULATOR",
      primary: "FOUND", novelty: "NEW", materiality: "MEDIUM",
      verification: "Primary page located; evidence eligibility not assessed",
      status: "VERIFYING", existing: "RBI event cluster · 2 related observations",
      notes: "Confirm whether this changes the current liquidity state or is an operational continuation.",
      provenance: "Codex run · operations-audit · official RSS lead",
    },
    {
      id: "RC-0260", entity: "Debock Industries",
      title: "Secondary summary conflicts with final regulatory order wording",
      firstSeen: "17:18 IST", source: "sebi.gov.in", sourceType: "PRIMARY_REGULATOR",
      primary: "FOUND", novelty: "UPDATE", materiality: "HIGH",
      verification: "Primary order found; contradiction preserved",
      status: "CONTRADICTION", existing: "SEBI event · EVT-8F2C",
      notes: "Do not resolve from the headline. Route the official order through the standard collector after rights review.",
      provenance: "Codex run · hourly-1700 · platform UNKNOWN follow-up",
    },
    {
      id: "RC-0259", entity: "Indian industrials",
      title: "Syndicated contract story resolves to an already-known filing",
      firstSeen: "16:31 IST", source: "multiple secondary domains", sourceType: "SECONDARY_REPUTABLE",
      primary: "FOUND", novelty: "DUPLICATE", materiality: "LOW",
      verification: "Existing exchange filing matched",
      status: "NEW", existing: "Canonical event · EVT-74A1",
      notes: "Suppress 11 syndicated copies. No new candidate should enter evidence review.",
      provenance: "Codex run · eod · differential search",
    },
    {
      id: "RC-0258", entity: "USD/INR",
      title: "Narrative shift lacks a permitted primary statistical source",
      firstSeen: "15:08 IST", source: "market commentary", sourceType: "SECONDARY_OTHER",
      primary: "NOT FOUND", novelty: "RELATED", materiality: "UNKNOWN",
      verification: "Source rights and primary evidence unresolved",
      status: "RIGHTS REVIEW", existing: "No matching canonical event",
      notes: "Retain as exploratory context only. Do not infer currency direction or activate a new source.",
      provenance: "Codex run · hourly-1500 · macro gap",
    },
  ] satisfies ResearchCandidate[],
  issues: [
    ["Collector issue", "RBI naive timestamps", "Fix prepared on isolated branch; soak runtime remains untouched"],
    ["Browser research", "Available", "Not used in the latest run; direct official sources were sufficient"],
    ["Source candidate", "Government statistics feed", "REVIEW_REQUIRED · no activation"],
  ],
  runs: [
    ["Operations audit", "18:00", "5 gaps · 1 collector issue"],
    ["EOD review", "16:45", "3 candidates · 11 duplicates"],
    ["Hourly differential", "16:00", "1 update · 0 contradictions"],
  ],
};
