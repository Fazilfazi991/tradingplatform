export function LoadingEvidenceView() {
  return (
    <main className="loading-state" role="status" aria-live="polite" aria-busy="true">
      <div className="loading-heading">
        <span>ASSEMBLING EVIDENCE VIEW</span>
        <div className="loading-title" />
        <div className="loading-copy" />
      </div>
      <div className="loading-ledger" aria-hidden="true">
        <div /><div /><div />
      </div>
      <span className="sr-only">Loading the Verified Edge evidence view.</span>
    </main>
  );
}
