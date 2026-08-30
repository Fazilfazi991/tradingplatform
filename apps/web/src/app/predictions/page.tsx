"use client";
import { useMemo, useState } from "react";
import Link from "next/link";
import { predictions } from "@/data/demo/predictions";
import { PageHeader, SectionHeader } from "@/components/ui";

export default function Predictions() {
  const [horizon,setHorizon]=useState("5D"); const [query,setQuery]=useState("");
  const rows=useMemo(()=>predictions.filter(p=>(p.symbol+p.company).toLowerCase().includes(query.toLowerCase())),[query]);
  return <><PageHeader title="Market predictions">Probabilistic outlooks based on multiple evidence engines. Every value on this page is synthetic.</PageHeader><div className="content">
    <section className="section"><div className="filters" aria-label="Prediction filters">{["1D","3D","5D","10D"].map(x=><button key={x} className={`filter ${horizon===x?"active":""}`} onClick={()=>setHorizon(x)}>{x}</button>)}{["NIFTY 50","NIFTY 100","NIFTY 200","Sector","All statuses"].map((x,i)=><button key={x} className={`filter ${i===2?"active":""}`}>{x}</button>)}<input aria-label="Search stocks" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search symbol…" className="filter" style={{marginLeft:"auto",color:"var(--chalk)"}}/></div></section>
    <section className="section"><SectionHeader title={`${horizon} synthetic outlooks`} note={`${rows.length} demo securities · MODEL PROTOTYPE`}/><div className="panel prediction-list">{rows.map(p=><Link href={`/stocks/${p.symbol}`} className="prediction-row" key={p.symbol}><div><strong>{p.symbol}</strong><small>{p.company}</small><small className="mobile-range">{p.range} · {p.agreement}</small></div><div><span className={`tag ${p.direction.toLowerCase()}`}>{p.direction}</span></div><div><span className="prediction-score">{p.score}</span><small className="tooltip" title="Directional conviction after evidence fusion—not probability of profit.">Prediction score</small></div><div><strong>{p.range}</strong><small>Expected range · downside {p.downside}</small></div><div><strong>{p.agreement}</strong><small className="tooltip" title="How many independent evidence engines support the direction.">Evidence agreement</small></div><div><strong>{p.certainty}</strong><small className="tooltip" title="Stability and calibration quality of the prototype model.">Model certainty</small></div></Link>)}</div></section>
    <section className="section"><div className="cards"><div className="card"><h3>Prediction score</h3><p>Directional strength after evidence fusion. It is not a probability of profit.</p></div><div className="card"><h3>Evidence agreement</h3><p>How many specialist engines independently support the outlook.</p></div><div className="card"><h3>Data quality</h3><p>Completeness and provenance of inputs, independent of model certainty.</p></div></div></section>
  </div></>;
}
