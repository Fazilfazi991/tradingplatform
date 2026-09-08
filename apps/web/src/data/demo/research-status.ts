import { releaseStatus } from "@/lib/release-status";

export const researchStatus = [
  ["Provider-neutral abstraction", "PASS"], ["Deterministic datasets", "PASS"],
  ["Current NIFTY 200 mapping snapshot", "PASS"], ["Upstox market history", "REAL BACKFILL · 4 SEP 2026"],
  ["PostgreSQL runtime", releaseStatus.unavailable], ["Point-in-time historical universe", "BLOCKED"],
  ["Corporate actions", "BLOCKED"], ["Second source", "DEFERRED"],
  ["Specialist engines", "ENGINEERING CONTRACTS · SOURCE LIMITED"], ["Evidence Fusion", `${releaseStatus.partialLiveAbstain} · RUNTIME STOPPED`],
  ["Prediction Engine V1", releaseStatus.holdoutForwardRequired], ["Public predictions", "BLOCKED"],
].map(([label, status]) => ({ label, status }));
