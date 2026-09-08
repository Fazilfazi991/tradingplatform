"use client";

import Link from "next/link";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body>
        <main className="resilience-state resilience-state-global" role="main">
          <span className="resilience-code">APPLICATION INTERRUPTED</span>
          <h1>Verified Edge needs a clean restart.</h1>
          <p>
            No prediction or market action was taken. Restart the public experience, or return to
            the overview if the interruption continues.
          </p>
          <div className="resilience-actions">
            <button type="button" onClick={reset}>Restart Verified Edge</button>
            <Link href="/">Return to overview</Link>
          </div>
        </main>
      </body>
    </html>
  );
}
