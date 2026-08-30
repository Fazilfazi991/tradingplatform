import { market } from "@/data/demo/market";
import { DataNote, PageHeader, SectionHeader, Tag } from "@/components/ui";

export default function Overview() { return <>
  <PageHeader title="Market intelligence, with its doubts intact.">Seven specialist engines interpret the market independently before their evidence is fused into a probabilistic view.</PageHeader>
  <div className="content">
    <section className="section"><SectionHeader title="Market pulse" note="Demo market snapshot"/><div className="metric-grid">{market.pulse.map(x=><div className="metric" key={x.label}><label>{x.label}</label><strong>{x.value}</strong><small className={x.tone}>{x.change}</small></div>)}</div></section>
    <section className="section"><SectionHeader title="Evidence convergence" note="Illustrative demo output · 5 of 7 engines supportive"/>
      <div className="panel consensus">
        <div className="regime"><Tag>Current market regime</Tag><h3>Moderate<br/>bullish</h3><div className="score">72<span> / 100</span></div><p className="micro">Trend and breadth are constructive, while mixed foreign flows and valuation restrain conviction.</p><div style={{marginTop:28}}><Tag tone="neutral">1–4 week regime</Tag></div></div>
        <div className="engine-field"><DataNote/><div className="trace-list">{market.engines.map((e,i)=><div className={`engine-row ${e.stance==="Bearish"?"negative":""}`} key={e.name} title={e.rationale}><b>{e.name}</b><div className="track"><i style={{width:`${e.score}%`,animationDelay:`${i*60}ms`}}/></div><span className={e.stance==="Bearish"?"down":"up"}>{e.score}</span></div>)}</div><div className="consensus-node"><small className="micro">SYNTHETIC<br/>CONSENSUS</small><div className="score">72</div><strong>Moderately<br/>bullish</strong></div></div>
        <aside className="contradiction"><Tag tone="bearish">Primary contradiction</Tag><div className="contradiction-box"><h3 className="down">Flows · 32/100</h3><p className="micro">Foreign-flow weakness diverges from broader price strength. The prediction is not unanimous.</p></div><div style={{marginTop:52}}><small className="micro">WHAT WOULD CHANGE THE VIEW?</small><p className="micro">A risk-off market regime, loss of medium-term trend, fading volume confirmation, or material negative news.</p></div></aside>
      </div>
    </section>
    <section className="section"><SectionHeader title="Why the system leans bullish" note="Explanation, not recommendation"/><div className="cards"><div className="card"><h3>Supporting evidence</h3><p>Trend structure, historical regime similarity, sector breadth, and measured positive psychology.</p></div><div className="card"><h3>Contradictions</h3><p>Foreign institutional flows remain weak and selected large-cap valuations are elevated.</p></div><div className="card"><h3>Uncertainty</h3><p>Medium. Two engines are neutral and one is materially opposed to the current consensus.</p></div></div></section>
  </div>
  </>; }
