import { demoProvenance, type Direction } from "./types";

export type Prediction = {
  symbol: string; company: string; price: string; direction: Direction; score: number;
  range: string; downside: string; agreement: string; certainty: string; quality: string;
};

export const predictionProvenance = demoProvenance;
export const predictions: Prediction[] = [
  ["RELIANCE", "Reliance Industries", "₹1,482.40", "Bullish", 72, "+1.1% → +4.0%", "−2.2%", "5 / 7", "Medium", "Fixture complete"],
  ["HDFCBANK", "HDFC Bank", "₹1,976.25", "Bullish", 69, "+0.8% → +3.1%", "−1.9%", "5 / 7", "Medium", "Fixture complete"],
  ["ICICIBANK", "ICICI Bank", "₹1,418.10", "Bullish", 66, "+0.5% → +2.8%", "−2.1%", "4 / 7", "Medium", "Fixture complete"],
  ["INFY", "Infosys", "₹1,612.80", "Neutral", 52, "−1.2% → +1.6%", "−2.7%", "3 / 7", "Low", "Fixture complete"],
  ["TCS", "Tata Consultancy Services", "₹3,142.65", "Neutral", 49, "−1.4% → +1.3%", "−2.5%", "3 / 7", "Low", "Fixture complete"],
  ["SBIN", "State Bank of India", "₹928.35", "Bullish", 64, "+0.4% → +3.0%", "−2.4%", "4 / 7", "Medium", "Fixture complete"],
  ["LT", "Larsen & Toubro", "₹3,826.70", "Bullish", 61, "+0.3% → +2.7%", "−2.3%", "4 / 7", "Medium", "Fixture complete"],
  ["BHARTIARTL", "Bharti Airtel", "₹1,934.55", "Bearish", 38, "−2.9% → +0.4%", "−3.2%", "2 / 7", "Low", "Fixture complete"],
].map(([symbol, company, price, direction, score, range, downside, agreement, certainty, quality]) => ({
  symbol, company, price, direction, score, range, downside, agreement, certainty, quality,
} as Prediction));
