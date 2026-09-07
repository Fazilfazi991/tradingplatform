"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, BrainCircuit, CircleHelp, Database, Gauge, GitMerge, Search, ShieldCheck, Sparkles } from "lucide-react";

const nav = [
  ["Overview", "/", Gauge], ["Research demo", "/predictions", Sparkles],
  ["Stock explorer", "/stocks/RELIANCE", Search], ["Evidence Fusion", "/fusion", GitMerge],
  ["Methodology", "/methodology", BookOpen], ["Evidence engines", "/models", BrainCircuit],
  ["Data sources", "/data-sources", Database], ["Validation", "/validation", ShieldCheck],
  ["FAQ", "/faq", CircleHelp],
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return <div className="app">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className="sidebar">
      <Link href="/" className="brand">VERIFIED EDGE<small>Market Prediction Intelligence</small></Link>
      <nav className="nav" aria-label="Primary navigation">{nav.map(([label,href,Icon]) => <Link key={label} href={href} aria-current={path===href?"page":undefined} className={path===href?"active":""}><Icon aria-hidden="true" size={15}/>{label}</Link>)}</nav>
      <div className="research-mode"><b>DEMO — SYNTHETIC DATA</b><br/>Research interface only<br/>No public predictions</div>
    </aside>
    <main className="main">
      <div className="demo-banner"><b>RESEARCH PROTOTYPE</b><span>Market and prediction values shown here are synthetic demo data unless explicitly marked otherwise.</span></div>
      <div className="mobile-nav"><Link href="/" className="brand">VERIFIED EDGE</Link><BrainCircuit aria-hidden="true" size={18}/></div>
      <nav className="mobile-links" aria-label="Mobile navigation">{nav.map(([label,href])=><Link key={label} href={href} aria-current={path===href?"page":undefined}>{label}</Link>)}</nav>
      <div id="main-content" tabIndex={-1}>{children}</div>
      <footer className="site-footer"><div><b>VERIFIED EDGE</b><span>Evidence-led market research with uncertainty intact.</span></div><nav aria-label="Legal and company"><Link href="/about">About</Link><Link href="/contact">Contact</Link><Link href="/risk">Risk</Link><Link href="/privacy">Privacy</Link><Link href="/terms">Terms</Link></nav></footer>
    </main>
  </div>;
}
