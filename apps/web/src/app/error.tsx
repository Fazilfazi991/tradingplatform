"use client";

import Link from "next/link";

export default function ErrorBoundary({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="resilience-state" role="main">
      <span className="resilience-code">VIEW INTERRUPTED</span>
      <h1>We could not complete this evidence view.</h1>
      <p>
        The research demonstration remains unchanged. Try loading this view again, or return to the
        overview while the interruption clears.
      </p>
      <div className="resilience-actions">
        <button type="button" onClick={reset}>Try this view again</button>
        <Link href="/">Return to overview</Link>
      </div>
    </main>
  );
}
