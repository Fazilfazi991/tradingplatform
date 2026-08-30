export type DataProvenance = {
  mode: "demo" | "live" | "validated";
  source: string;
  generated_at: string;
  description: string;
};

export const demoProvenance: DataProvenance = {
  mode: "demo",
  source: "Verified Edge synthetic product fixtures",
  generated_at: "2026-08-30T14:30:00+04:00",
  description: "Illustrative values for interface evaluation. Not market data or a prediction.",
};

export type Direction = "Bullish" | "Bearish" | "Neutral";
