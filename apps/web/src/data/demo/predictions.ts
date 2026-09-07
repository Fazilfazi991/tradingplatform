import { demoProvenance, type Direction } from "./types";

export type Prediction = {
  symbol: string; company: string; price: string; direction: Direction; score: number;
  range: string; downside: string; agreement: string; certainty: string; quality: string;
};

export const predictionProvenance = demoProvenance;
export const predictions: Prediction[] = [
  ["RELIANCE", "Reliance Industries", "₹1,482.40", "Bullish", 72, "+1.1% → +4.0%", "−2.2%", "5 / 7", "Medium", "Fixture complete"],
].map(([symbol, company, price, direction, score, range, downside, agreement, certainty, quality]) => ({
  symbol, company, price, direction, score, range, downside, agreement, certainty, quality,
} as Prediction));
