"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, BrainCircuit, Database, FlaskConical, Gauge, History, Newspaper, Search, Settings, Shapes, Sparkles } from "lucide-react";

const nav = [
  ["Overview", "/", Gauge], ["Predictions", "/predictions", Sparkles],
  ["Stocks", "/stocks/RELIANCE", Search], ["Sectors", "/sectors", Shapes],
  ["News & Sentiment", "/intelligence", Newspaper], ["Historical Intelligence", "/historical", History],
  ["Models", "/models", BrainCircuit], ["Research Lab", "/research", FlaskConical],
  ["Data Health", "/data-health", Database], ["Settings", "/settings", Settings],
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return <div className="app">
    <aside className="sidebar">
      <Link href="/" className="brand">VERIFIED EDGE<small>Market Prediction Intelligence</small></Link>
      <nav className="nav" aria-label="Primary navigation">{nav.map(([label,href,Icon]) => <Link key={label} href={href} className={path===href?"active":""}><Icon size={15}/>{label}</Link>)}</nav>
      <div className="research-mode"><b>DEMO / RESEARCH MODE</b><br/>Synthetic fixtures only<br/>No live prediction</div>
    </aside>
    <main className="main">
      <div className="demo-banner"><b>RESEARCH PROTOTYPE</b><span>Market and prediction values shown here are synthetic demo data unless explicitly marked otherwise.</span></div>
      <div className="mobile-nav"><Link href="/" className="brand">VERIFIED EDGE</Link><BarChart3 size={18}/></div>
      <nav className="mobile-links" aria-label="Mobile navigation">{nav.slice(0,10).map(([label,href])=><Link key={label} href={href}>{label}</Link>)}</nav>
      {children}
    </main>
  </div>;
}
