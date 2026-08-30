import { Info, TriangleAlert } from "lucide-react";

export function PageHeader({ title, children, stamp="30 Aug 2026 · 14:30 GST" }: { title:string; children:string; stamp?:string }) {
  return <header className="topbar"><div><h1>{title}</h1><p>{children}</p></div><div className="stamp">DEMO SNAPSHOT · {stamp}</div></header>;
}
export function SectionHeader({ title, note }: { title:string; note?:string }) { return <div className="section-title"><h2>{title}</h2>{note&&<p>{note}</p>}</div>; }
export function Tag({ children, tone="demo" }: { children:React.ReactNode; tone?:string }) { return <span className={`tag ${tone}`}>{children}</span>; }
export function DataNote() { return <p className="micro"><Info size={12} style={{verticalAlign:"-2px",marginRight:6}}/>Synthetic prototype statistics. Not a live prediction.</p>; }
export function EmptyDataState({ title, children }: { title:string; children:React.ReactNode }) { return <div className="card"><TriangleAlert size={18} color="var(--amber)"/><h3 style={{marginTop:18}}>{title}</h3><p>{children}</p><div style={{marginTop:18}}><Tag tone="blocked">Data source not connected</Tag></div></div>; }
