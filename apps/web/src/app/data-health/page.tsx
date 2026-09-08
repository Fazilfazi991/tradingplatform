import { PageHeader, SectionHeader, Tag } from "@/components/ui";

const health = [
  ["Provider contract", "UPSTOX · READ ONLY", "pass"],
  ["Last bounded authentication check", "PASSED · 7 SEP 2026", "pass"],
  ["Current authentication health", "NOT CHECKED BY THIS PAGE", "deferred"],
  ["Platform worker", "NOT STARTED", "deferred"],
  ["Scheduled EOD collection", "DISABLED", "deferred"],
  ["Latest canonical market session", "4 SEP 2026 · NOT CURRENT", "blocked"],
  ["Current NIFTY 200 mapping snapshot", "200 / 200", "pass"],
  ["Historical analogue eligibility", "194 / 200", "pass"],
  ["Point-in-time universe", "BLOCKED", "blocked"],
  ["Independent second source", "NOT CONFIGURED", "deferred"],
  ["Public redistribution", "NOT APPROVED", "blocked"],
];

export default function DataHealth() {
  return <>
    <PageHeader title="Data health">
      Internal evidence for market-data coverage, research eligibility, and unresolved rights gates.
    </PageHeader>
    <div className="content">
      <section className="section">
        <SectionHeader title="Market-data foundation" note="Historical activation evidence · not a live health probe" />
        <div className="panel status-list">
          {health.map(([label, value, tone]) => <div className="status-row" key={label}>
            <span>{label}</span><Tag tone={tone}>{value}</Tag>
          </div>)}
        </div>
      </section>
      <section className="section">
        <div className="cards">
          <div className="card">
            <h3>Current mapping</h3>
            <div className="score">200<span> / 200 exact</span></div>
            <p>Resolved through ISIN or exact NSE symbol matching. Fuzzy matching remains disabled.</p>
          </div>
          <div className="card">
            <h3>Real market history</h3>
            <div className="score">442,837<span> daily bars</span></div>
            <p>Backfilled through 4 Sep 2026. This fixed research dataset is not current market state. Nine invalid provider rows are quarantined and excluded.</p>
          </div>
          <div className="card">
            <h3>Research boundary</h3>
            <Tag tone="deferred">Not predictively validated</Tag>
            <p style={{ marginTop: 16 }}>
              Current-membership research is survivorship-biased. Public data display and predictions remain gated.
            </p>
          </div>
        </div>
      </section>
      <section className="section">
        <div className="card">
          <h3>Operational interpretation</h3>
          <p>This page records bounded activation evidence. It does not call Upstox, inspect credentials, or infer current provider availability. Current health requires the protected worker heartbeat, EOD ledger, source freshness, and provider canaries on the production host.</p>
        </div>
      </section>
    </div>
  </>;
}
