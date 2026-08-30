"use client";
import Link from "next/link";
import { useState } from "react";
import { useParams } from "next/navigation";
import { market } from "@/data/demo/market";
import { DataNote, EmptyDataState, PageHeader, SectionHeader, Tag } from "@/components/ui";
import { PriceChart } from "@/components/price-chart";
import { ArrowRight } from "lucide-react";

const evidence=[
  ["Technical",78,["Price above EMA20 and EMA50","20-day momentum positive","Volume expanding","Outperforming sector"]],
  ["Historical analogues",61,["184 similar fixture states","61% positive · 17% neutral · 22% negative","Median 5-day return +1.8%","Synthetic prototype statistics"]],
  ["News intelligence",54,["Recent company tone: positive","Sector tone: neutral","Material-event score: 58","No live news connected"]],
  ["Market psychology",64,["Sentiment 64/100 positive","Attention rising","Fear/euphoria subdued","News tone mixed-positive"]],
  ["Fundamental context",71,["Revenue trend constructive","Profitability stable","Valuation above fixture history","Revisions direction positive"]],
  ["Macro / cross-market",58,["NIFTY regime constructive","India VIX contained","USD/INR mixed","Crude and global risk neutral"]],
];
export default function StockPage(){const {symbol}=useParams<{symbol:string}>();const [expanded,setExpanded]=useState<string|null>("Technical");return <><PageHeader title={`${symbol} intelligence`}>A transparent evidence stack for a synthetic five-session outlook. Not investment advice.</PageHeader><div className="content">
  <section className="section"><div className="panel" style={{padding:26,display:"flex",justifyContent:"space-between",gap:24,flexWrap:"wrap"}}><div><Tag>Demo model output</Tag><h2 style={{font:"500 38px 'Newsreader Variable'",margin:"18px 0 6px"}}>Moderately bullish</h2><p className="micro">5 trading sessions · demo price ₹1,482.40</p></div><div><div className="score">72<span> / 100</span></div><small className="micro">PREDICTION SCORE</small></div></div></section>
  <section className="section"><SectionHeader title="Price context and prediction range" note="Synthetic price path · illustrative forecast window"/><PriceChart/></section>
  <section className="section"><SectionHeader title="Evidence stack" note="Select an engine to expand its reasoning"/><div className="evidence-grid">{evidence.map(([name,score,items])=><button className="panel evidence" style={{textAlign:"left"}} key={name as string} onClick={()=>setExpanded(expanded===name?null:name as string)} aria-expanded={expanded===name}><div className="evidence-head"><h3>{name as string}</h3><strong>{score as number}</strong></div><div className="bar"><i style={{width:`${score}%`}}/></div>{expanded===name&&<ul>{(items as string[]).map(x=><li key={x}>{x}</li>)}</ul>}</button>)}</div></section>
  <section className="section"><SectionHeader title="Where the models disagree"/><div className="panel consensus" style={{minHeight:0,gridTemplateColumns:"1fr 1fr"}}><div className="regime"><h3 style={{color:"var(--chalk)"}}>The view is not unanimous.</h3><p className="micro">Technical and fundamental evidence are supportive. News is neutral. Foreign-flow weakness is the primary contradictory signal.</p></div><div className="contradiction">{market.engines.slice(0,4).map(e=><div className="status-row" key={e.name}><span>{e.name}</span><Tag tone={e.stance.toLowerCase()}>{e.stance}</Tag></div>)}</div></div></section>
  <section className="section"><div className="fusion-entry"><div><Tag>Demo fusion V0</Tag><h2>Seven engines. One conflicted evidence state.</h2><p>Inspect agreement, uncertainty, missing positioning, and why the system abstains.</p></div><Link href="/fusion">Open evidence fusion <ArrowRight size={15}/></Link></div></section>
  <section className="section"><SectionHeader title="Invalidation / view-change conditions" note="Prediction-state reasoning, not a stop-loss"/><div className="card"><p>The outlook would weaken if the broad regime turns risk-off, the stock closes below its medium-term trend, volume confirmation disappears, or material negative information becomes available.</p></div></section>
  <section className="section"><EmptyDataState title="Flow / positioning source unavailable">FII/DII context, delivery trend, derivatives positioning, and sector-flow datasets are not connected in this prototype.</EmptyDataState></section><DataNote/>
</div></>}
