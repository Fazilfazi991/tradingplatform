import { existsSync, readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import { NextResponse } from "next/server";

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

export function GET() {
  const enabled = process.env.CODEX_RESEARCH_OPERATOR_ENABLED === "true";
  if (!enabled) return NextResponse.json({ enabled: false, candidates: [] });
  const workspace = [process.cwd(), resolve(process.cwd(), "../..")].find((path) =>
    existsSync(resolve(path, "research/codex")),
  ) ?? process.cwd();
  const statusPath = resolve(workspace, "data/local/codex-research-status.json");
  const researchRoot = resolve(workspace, "research/codex");
  let status: Record<string, unknown> = {};
  const candidates: SafeCandidate[] = [];
  try {
    status = JSON.parse(readFileSync(statusPath, "utf8"));
  } catch { /* The live ledger may not have exported a first status yet. */ }
  try {
    for (const relative of readdirSync(researchRoot, { recursive: true, encoding: "utf8" })) {
      if (!relative.endsWith("candidate.json")) continue;
      const row = JSON.parse(readFileSync(resolve(researchRoot, relative), "utf8"));
      candidates.push({
        id: row.candidate_id,
        entity: row.entity_name ?? row.scope,
        title: row.title,
        status: row.status,
        novelty: row.novelty_candidate,
        primary: row.primary_source_status,
        source: row.source_domain,
        observedAt: row.observed_at,
      });
    }
  } catch { /* An empty live candidate set is valid. */ }
  return NextResponse.json({
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
    candidates,
  });
}
