import { AlertTriangle, Ban, Database, LockKeyhole, Sigma } from "lucide-react";
import { PageHeader } from "@/components/ui";
import { predictionV1 as study } from "@/data/research/prediction-v1";

const metric = (value: number) => value.toFixed(4);

export default function PredictionResearchV1() {
  return <>
    <PageHeader title="Prediction Engine V1" label="REAL-DATASET STUDY" stamp="08 Sep 2026 · 01:39 GST">
      A sealed, real-market experiment asking whether reproducible predictive structure exists.
    </PageHeader>
    <div className="content prediction-research">
      <section className="prediction-lock" aria-labelledby="research-boundary">
        <div>
          <LockKeyhole size={17} aria-hidden="true" />
          <h2 id="research-boundary">Internal research. Not for customer use. Not for trading.</h2>
        </div>
        <p>Probabilities estimate preregistered target classes. They are not confidence scores, profit chances, advice, or an execution signal.</p>
      </section>

      <section className="prediction-study panel" aria-labelledby="study-status">
        <div className="prediction-study-copy">
          <h2 id="study-status">{study.researchStatus}</h2>
          <p>The holdout remains a locked measurement surface. Candidate choice, calibration, abstention, and pass criteria must be committed before access.</p>
          <dl className="prediction-identifiers">
            <div><dt>Registration</dt><dd>{study.registrationHash.slice(0, 16)}…</dd></div>
            <div><dt>Dataset</dt><dd>{study.datasetHash.slice(0, 16)}…</dd></div>
          </dl>
        </div>
        <div className="prediction-seal" aria-label={`Holdout state: ${study.holdoutState}`}>
          <LockKeyhole size={20} aria-hidden="true" />
          <span>Sealed holdout</span>
          <strong>{study.holdoutState}</strong>
          <small>{study.holdout}</small>
        </div>
      </section>

      <section className="prediction-facts" aria-label="Dataset facts">
        <div><Database size={14}/><span>Canonical rows</span><strong>{study.rows.toLocaleString()}</strong></div>
        <div><Sigma size={14}/><span>Eligible universe</span><strong>{study.symbols} symbols</strong></div>
        <div><span>Chronology</span><strong>{study.range}</strong></div>
        <div><span>Experiment count</span><strong>{study.experimentCount}</strong></div>
      </section>

      <section className="section" aria-labelledby="walk-forward">
        <div className="prediction-section-heading">
          <div><h2 id="walk-forward">Walk-forward evidence</h2><p>Three expanding annual folds · sigmoid calibration · 10-session maximum purge</p></div>
          <span>Lower Brier is better</span>
        </div>
        <div className="prediction-ledger panel">
          <div className="prediction-row prediction-row-head" aria-hidden="true">
            <span>Horizon</span><span>Selected model</span><span>Brier</span><span>Baseline</span><span>ECE</span><span>Coverage</span>
          </div>
          {study.horizons.map(row => <div className="prediction-row" key={row.horizon}>
            <strong>{row.horizon}</strong><span className="prediction-model">{row.model}<small>{row.folds} positive folds</small></span><span data-label="Brier">{metric(row.brier)}</span><span data-label="Baseline">{metric(row.baseline)}</span><span data-label="ECE">{metric(row.ece)}</span><span data-label="Coverage">{row.coverage}</span>
          </div>)}
        </div>
      </section>

      <section className="prediction-null panel" aria-labelledby="null-controls">
        <div><h2 id="null-controls">Null controls remained significant after correction</h2><p>Temporal structure was preserved; individual panel rows were never shuffled.</p></div>
        <dl><div><dt>Selected hypotheses</dt><dd>{study.nullControls.significant}</dd></div><div><dt>Method</dt><dd>{study.nullControls.method}</dd></div><div><dt>Correction</dt><dd>{study.nullControls.correction}</dd></div><div><dt>Adjusted p</dt><dd>{study.nullControls.adjustedP}</dd></div></dl>
      </section>

      <section className="prediction-method-grid">
        <div><h2>Calibration before conviction</h2><p>Class probabilities are calibrated on historical validation slices only. The sealed interval never fits a scaler, model, method, or threshold.</p></div>
        <div><h2>Abstention is an output</h2><p>Low separation, strong out-of-distribution state, model disagreement, insufficient history, and unresolved data quality can all withhold a forecast.</p></div>
        <div><h2>Nulls stay visible</h2><p>Date-block permutations and simple baselines contextualize every candidate. Failed experiments remain in the immutable research record.</p></div>
      </section>

      <section className="prediction-warning panel" aria-labelledby="limitations">
        <AlertTriangle size={18} aria-hidden="true" />
        <div><h2 id="limitations">This cannot establish a verified NIFTY 200 edge</h2><p>Historical membership is unavailable, so panel evidence is labelled survivorship-biased. Corporate-action adjustment semantics remain unverified.</p></div>
        <ul>{study.warnings.map(warning => <li key={warning.code}><span>{warning.label}</span><code>{warning.code}</code></li>)}</ul>
      </section>

      <footer className="prediction-footer"><Ban size={14}/><span>No public forecast route · no BUY/SELL · no position sizing · no broker execution · no forward paper run started</span></footer>
    </div>
  </>;
}
