import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Check, CircleSlash2, Fingerprint, Scale, ShieldCheck } from "lucide-react";

export const metadata: Metadata = { alternates: { canonical: "/" } };

const engines = [
  ["Technical", "Price structure"], ["Historical", "Comparable regimes"],
  ["News & events", "Material developments"], ["Macro", "Policy and liquidity"],
  ["Fundamentals", "Business evidence"], ["Psychology", "Attention and narrative"],
  ["Flows", "Positioning evidence"],
] as const;

export default function Overview() {
  return <div className="public-home">
    <section className="home-hero" aria-labelledby="home-title">
      <div className="home-message">
        <h1 id="home-title">Market intelligence that shows its work.</h1>
        <p>Verified Edge brings independent evidence together without hiding disagreement. See what supports a view, what contradicts it, where the data came from, and when the honest answer is to abstain.</p>
        <div className="home-actions"><Link className="home-primary" href="/stocks/RELIANCE">Explore the research demo <ArrowRight aria-hidden="true" size={16}/></Link><Link className="home-secondary" href="/methodology">Read the methodology</Link></div>
        <ul className="home-trust" aria-label="Research principles"><li><ShieldCheck aria-hidden="true"/>Independent engines</li><li><Scale aria-hidden="true"/>Contradictions stay visible</li><li><Fingerprint aria-hidden="true"/>Provenance by design</li><li><CircleSlash2 aria-hidden="true"/>Abstention is valid</li></ul>
      </div>
      <div className="home-evidence" aria-label="Seven evidence engines converge into a synthesis that may abstain">
        <div className="home-engine-list">{engines.map(([name, detail], index) => <div className="home-engine" style={{"--engine-index": index} as React.CSSProperties} key={name}><span>{String(index + 1).padStart(2, "0")}</span><div><b>{name}</b><small>{detail}</small></div><i aria-hidden="true"/></div>)}<div className="home-contradiction"><span>Contradictory evidence</span><i aria-hidden="true"/></div></div>
        <div className="home-synthesis"><small>Evidence</small><strong>Synthesis</strong><span>Not a trading signal</span></div><p className="home-abstain"><CircleSlash2 aria-hidden="true" size={14}/> Abstain when evidence is insufficient.</p>
      </div>
    </section>
    <section className="home-principles" aria-label="How Verified Edge works">
      <article><Check aria-hidden="true"/><div><h2>Independent evidence</h2><p>Seven specialists examine different information classes. A shared conclusion is earned through agreement, not assumed from one model.</p><Link href="/models">Explore the evidence architecture <ArrowRight aria-hidden="true" size={14}/></Link></div></article>
      <article><Scale aria-hidden="true"/><div><h2>Contradictions stay visible</h2><p>Conflicting evidence is kept in context, so uncertainty remains inspectable instead of being averaged into false confidence.</p><Link href="/fusion">See evidence fusion <ArrowRight aria-hidden="true" size={14}/></Link></div></article>
      <article><ShieldCheck aria-hidden="true"/><div><h2>Validation before claims</h2><p>The predictive research passed a sealed holdout, but prospective validation is still required. Public predictions remain unavailable.</p><Link href="/validation">Read the validation status <ArrowRight aria-hidden="true" size={14}/></Link></div></article>
    </section>
    <section className="home-boundary"><div><h2>Research, not recommendation.</h2><p>The public experience uses synthetic demonstration data. Verified Edge does not provide investment advice, BUY/SELL calls, target prices, order execution, or verified performance claims.</p></div><Link href="/risk">Read the risk disclosure <ArrowRight aria-hidden="true" size={14}/></Link></section>
  </div>;
}
