import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { NextResponse } from "next/server";
import { FixedWindowLimiter, MemoryTtlCache } from "@/lib/bounded-runtime";

type SafeCandidate = {
  id: string;
  entity: string;
  title: string;
  status: string;
  novelty: string;
  primary: string;
  source: string;
  observedAt: string;
};

export const dynamic = "force-dynamic";
const MAX_ARTIFACT_BYTES = 256 * 1024;
const MAX_ENTRIES_SCANNED = 500;
const MAX_CANDIDATES = 100;
const limiter = new FixedWindowLimiter(30, 60_000);
const cache = new MemoryTtlCache<ResearchDeskPayload>(15_000);
const privateHeaders = { "Cache-Control": "private, no-store" };

type ResearchDeskPayload = {
  enabled: boolean;
  status?: Record<string, unknown>;
  candidates: SafeCandidate[];
};

function readJson(path: string): Record<string, unknown> | null {
  try {
    if (statSync(path).size > MAX_ARTIFACT_BYTES) return null;
    const value: unknown = JSON.parse(readFileSync(path, "utf8"));
    return value !== null && typeof value === "object" && !Array.isArray(value)
      ? value as Record<string, unknown>
      : null;
  } catch {
    return null;
  }
}

function candidateFiles(root: string): string[] {
  const pending = [root];
  const result: string[] = [];
  let scanned = 0;
  while (pending.length && scanned < MAX_ENTRIES_SCANNED && result.length < MAX_CANDIDATES) {
    const directory = pending.pop();
    if (!directory) break;
    let entries;
    try {
      entries = readdirSync(directory, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      scanned += 1;
      if (scanned > MAX_ENTRIES_SCANNED) break;
      if (entry.isSymbolicLink()) continue;
      const path = resolve(directory, entry.name);
      if (entry.isDirectory()) pending.push(path);
      else if (entry.isFile() && entry.name === "candidate.json") result.push(path);
      if (result.length >= MAX_CANDIDATES) break;
    }
  }
  return result;
}

export function GET() {
  const enabled = process.env.CODEX_RESEARCH_OPERATOR_ENABLED === "true";
  if (!enabled) {
    return NextResponse.json(
      { enabled: false, candidates: [] },
      { headers: privateHeaders },
    );
  }
  if (!limiter.allow()) {
    return NextResponse.json(
      { error: "RATE_LIMITED" },
      { status: 429, headers: { ...privateHeaders, "Retry-After": "60" } },
    );
  }
  const cached = cache.get();
  if (cached) return NextResponse.json(cached, { headers: privateHeaders });
  const workspace = [process.cwd(), resolve(process.cwd(), "../..")].find((path) =>
    existsSync(resolve(path, "research/codex")),
  ) ?? process.cwd();
  const statusPath = resolve(workspace, "data/local/codex-research-status.json");
  const researchRoot = resolve(workspace, "research/codex");
  let status: Record<string, unknown> = {};
  const candidates: SafeCandidate[] = [];
  status = readJson(statusPath) ?? {};
  if (existsSync(researchRoot)) {
    for (const path of candidateFiles(researchRoot)) {
      const row = readJson(path);
      if (!row) continue;
      candidates.push({
        id: String(row.candidate_id ?? "UNKNOWN"),
        entity: String(row.entity_name ?? row.scope ?? "Unknown entity"),
        title: String(row.title ?? "Untitled candidate"),
        status: String(row.status ?? "UNKNOWN"),
        novelty: String(row.novelty_candidate ?? "UNKNOWN"),
        primary: String(row.primary_source_status ?? "UNKNOWN"),
        source: String(row.source_domain ?? "UNKNOWN"),
        observedAt: String(row.observed_at ?? ""),
      });
    }
  }
  const payload: ResearchDeskPayload = {
    enabled: true,
    status: {
      lastRun: status.last_run ?? null,
      runsToday: status.runs_today ?? 0,
      candidatesToday: status.candidates_today ?? 0,
      new: status.new ?? 0,
      updates: status.updates ?? 0,
      duplicates: status.duplicates ?? 0,
      duplicatesSuppressed: status.duplicates_suppressed ?? 0,
      primarySourcesVerified: status.primary_sources_verified ?? 0,
      pendingReview: status.pending_review ?? 0,
      rightsReview: status.rights_review ?? 0,
      contradictions: status.contradictions ?? 0,
      researchIncidents: status.research_incidents ?? 0,
    },
    candidates: candidates.sort((left, right) => right.observedAt.localeCompare(left.observedAt)),
  };
  cache.set(payload);
  return NextResponse.json(payload, { headers: privateHeaders });
}
