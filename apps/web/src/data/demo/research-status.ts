export const researchStatus = [
  ["Provider-neutral abstraction", "PASS"], ["Deterministic datasets", "PASS"],
  ["Current NIFTY 200 mapping", "PASS"], ["Upstox internal market history", "ACTIVE"],
  ["PostgreSQL runtime", "ACTIVE"], ["Point-in-time historical universe", "BLOCKED"],
  ["Corporate actions", "BLOCKED"], ["Second source", "DEFERRED"],
  ["Specialist engines", "7 / 7 ENGINEERING READY"], ["Evidence Fusion", "V0 ACTIVE"],
  ["Prediction Engine V1", "WALK-FORWARD"], ["Public predictions", "BLOCKED"],
].map(([label, status]) => ({ label, status }));
