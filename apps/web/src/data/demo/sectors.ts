import { demoProvenance } from "./types";

export const sectors = {
  provenance: demoProvenance,
  items: [
    ["Financials", 78, 72, "Positive", "Bullish"], ["IT", 64, 58, "Neutral", "Neutral"],
    ["Energy", 71, 66, "Positive", "Bullish"], ["Auto", 59, 61, "Neutral", "Neutral"],
    ["FMCG", 43, 48, "Neutral", "Neutral"], ["Pharma", 67, 69, "Positive", "Bullish"],
    ["Metals", 38, 42, "Negative", "Bearish"], ["Realty", 54, 51, "Neutral", "Neutral"],
    ["Consumer", 57, 56, "Positive", "Neutral"], ["Industrials", 74, 70, "Positive", "Bullish"],
  ].map(([name, strength, breadth, sentiment, outlook]) => ({ name, strength, breadth, sentiment, outlook })),
};
