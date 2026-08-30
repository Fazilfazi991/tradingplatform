import { demoProvenance } from "./types";

export const market = {
  provenance: demoProvenance,
  timestamp: "30 Aug 2026 · 14:30 GST",
  pulse: [
    { label: "NIFTY 50", value: "24,842.10", change: "+0.58%", tone: "up" },
    { label: "BANK NIFTY", value: "53,106.40", change: "+0.31%", tone: "up" },
    { label: "INDIA VIX", value: "13.24", change: "−2.18%", tone: "down" },
    { label: "MARKET BREADTH", value: "1.65", change: "1,342 / 812", tone: "neutral" },
  ],
  engines: [
    { name: "Technical", stance: "Bullish", score: 78, rationale: "Trend and momentum remain constructive." },
    { name: "Historical", stance: "Bullish", score: 70, rationale: "Comparable regimes skew positive." },
    { name: "News", stance: "Neutral", score: 54, rationale: "Event tone is balanced." },
    { name: "Sentiment", stance: "Bullish", score: 68, rationale: "Attention is positive, not euphoric." },
    { name: "Macro", stance: "Neutral", score: 58, rationale: "Growth steady; global risk mixed." },
    { name: "Flows", stance: "Bearish", score: 32, rationale: "Foreign flows diverge from price strength." },
    { name: "Fundamental", stance: "Bullish", score: 71, rationale: "Earnings quality is supportive." },
  ],
};
