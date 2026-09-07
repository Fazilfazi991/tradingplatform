import { notFound } from "next/navigation";
import { StockDemo } from "@/components/stock-demo";

const demoSymbols = new Set(["RELIANCE"]);

export default async function StockPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const normalized = symbol.toUpperCase();
  if (!demoSymbols.has(normalized)) notFound();
  return <StockDemo symbol={normalized}/>;
}
