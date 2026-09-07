import { PageHeader, SectionHeader, Tag } from "@/components/ui";

const health = [
  ["Provider", "UPSTOX · READ ONLY", "pass"],
  ["Analytics authentication", "HEALTHY", "pass"],
  ["Current NIFTY 200 mapping", "200 / 200", "pass"],
  ["Real daily history", "200 INSTRUMENTS", "pass"],
  ["Technical intelligence", "REAL INTERNAL", "pass"],
  ["Historical analogues", "194 / 200", "pass"],
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
        <SectionHeader title="Market-data foundation" note="Upstox · Batch 13 internal activation" />
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
            <p>Backfilled through 4 Sep 2026. Nine invalid provider rows are quarantined and excluded.</p>
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
    </div>
  </>;
}
