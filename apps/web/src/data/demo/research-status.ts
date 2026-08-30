export const researchStatus = [
  ["Provider-neutral abstraction", "PASS"], ["Deterministic datasets", "PASS"],
  ["Current NIFTY 200 mapping", "PASS"], ["Upstox live validation", "BLOCKED"],
  ["PostgreSQL runtime", "NOT CONFIGURED"], ["Historical universe", "BLOCKED"],
  ["Corporate actions", "BLOCKED"], ["Second source", "DEFERRED"],
  ["Prediction models", "NOT STARTED"], ["News intelligence", "NOT STARTED"],
  ["Sentiment intelligence", "NOT STARTED"],
].map(([label, status]) => ({ label, status }));
