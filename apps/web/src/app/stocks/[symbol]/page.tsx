import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { StockDemo } from "@/components/stock-demo";

const demoSymbols = new Set(["RELIANCE"]);

export async function generateMetadata(
  { params }: { params: Promise<{ symbol: string }> },
): Promise<Metadata> {
  const { symbol } = await params;
  return {
    title: `${symbol.toUpperCase()} Synthetic Research Demo`,
    description: "A synthetic stock-intelligence demonstration. No live prediction or recommendation is provided.",
    robots: { index: false, follow: false },
  };
}

export default async function StockPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const normalized = symbol.toUpperCase();
  if (!demoSymbols.has(normalized)) notFound();
  return <StockDemo symbol={normalized}/>;
}
