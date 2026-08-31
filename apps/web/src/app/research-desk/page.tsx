"use client";

import { useState } from "react";
import { AlertTriangle, ArrowUpRight, CheckCircle2, Clock3, FileCheck2, SearchCheck, ShieldAlert } from "lucide-react";
import { PageHeader, Tag } from "@/components/ui";
import { researchDesk } from "@/data/demo/research-desk";

const filters = ["ALL", "NEW", "VERIFYING", "RIGHTS REVIEW", "CONTRADICTION"] as const;

export default function ResearchDeskPage() {
  const [filter, setFilter] = useState<(typeof filters)[number]>("ALL");
  const candidates = researchDesk.candidates.filter((item) => filter === "ALL" || item.status === filter);

  return <>
    <PageHeader title="Research Desk" stamp="31 Aug 2026 · 18:05 IST">
      Exploratory discovery, primary-source verification, and operational research. Candidates remain outside prediction evidence until the standard pipeline approves them.
    </PageHeader>
    <div className="content research-desk">
      <section className="research-command panel" aria-labelledby="research-queue-title">
        <div className="research-command-copy">
          <div className="research-lock"><ShieldAlert size={16}/><b>INTERNAL RESEARCH</b><span>NOT PREDICTION INPUT UNTIL VERIFIED</span></div>
          <h2 id="research-queue-title">What changed, what is credible, and what still needs proof.</h2>
          <p>Codex begins with platform gaps, searches differentially, and hands findings back as untrusted candidates. It cannot alter Fusion, promote evidence, or activate sources.</p>
        </div>
        <dl className="research-run-state">
          <div><dt>Last run</dt><dd>{researchDesk.lastRun}</dd></div>
          <div><dt>Next expected</dt><dd>{researchDesk.nextRun}</dd></div>
          <div><dt>Operator</dt><dd><span className="status-dot"/>Prepared · disabled by default</dd></div>
        </dl>
      </section>

      <section className="research-metrics" aria-label="Research desk status">
        {researchDesk.metrics.map(([label,value])=><div key={label}><span>{label}</span><strong>{value}</strong></div>)}
      </section>

      <section className="research-layout">
        <div className="research-queue">
          <div className="research-toolbar">
            <div><h2>Research queue</h2><p>Newest and materially changed candidates only</p><span className="research-fixture-label">Synthetic research candidates · engineering fixture</span></div>
            <div className="filters" aria-label="Filter research candidates">{filters.map(value=><button type="button" key={value} className={`filter ${filter===value?"active":""}`} aria-pressed={filter===value} onClick={()=>setFilter(value)}>{value}</button>)}</div>
          </div>
          <div className="candidate-ledger panel" aria-live="polite">
            {candidates.length ? candidates.map((item)=><article className="candidate-record" key={item.id}>
              <div className="candidate-rail"><span>{item.id}</span><time>{item.firstSeen}</time><i/></div>
              <div className="candidate-main">
                <div className="candidate-head"><div><small>{item.entity}</small><h3>{item.title}</h3></div><Tag tone={item.status==="CONTRADICTION"?"bearish":item.primary==="FOUND"?"pass":item.status==="RIGHTS REVIEW"?"demo":"neutral"}>{item.status}</Tag></div>
                <div className="candidate-facts">
                  <div><span>Source</span><b>{item.source}</b><small>{item.sourceType}</small></div>
                  <div><span>Primary</span><b>{item.primary}</b><small>{item.verification}</small></div>
                  <div><span>Novelty</span><b>{item.novelty}</b><small>{item.existing}</small></div>
                  <div><span>Materiality candidate</span><b>{item.materiality}</b><small>Non-authoritative</small></div>
                </div>
                <p className="candidate-note">{item.notes}</p>
                <footer><span><FileCheck2 size={13}/>{item.provenance}</span><button type="button" disabled aria-label={`Review ${item.id}`}>Review unavailable in prototype <ArrowUpRight size={13}/></button></footer>
              </div>
            </article>) : <div className="research-empty"><SearchCheck size={24}/><h3>No candidates in this state</h3><p>The differential queue is clear. Collection and specialist engines continue independently.</p></div>}
          </div>
        </div>

        <aside className="research-side" aria-label="Research operations">
          <section className="panel research-side-section"><div className="research-side-title"><AlertTriangle size={15}/><h2>Operational issues</h2></div>{researchDesk.issues.map(([type,title,note])=><div className="research-side-row" key={title}><span>{type}</span><b>{title}</b><p>{note}</p></div>)}</section>
          <section className="panel research-side-section"><div className="research-side-title"><Clock3 size={15}/><h2>Recent Codex runs</h2></div>{researchDesk.runs.map(([name,time,result])=><div className="research-run" key={`${name}-${time}`}><CheckCircle2 size={14}/><div><b>{name}</b><span>{time} IST · {result}</span></div></div>)}</section>
        </aside>
      </section>
    </div>
  </>;
}
