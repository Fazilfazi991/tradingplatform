import Link from "next/link";
import { serializeStructuredData } from "@/lib/public-metadata";
import { canonicalSiteOrigin } from "@/lib/site-url";

export function PublicBreadcrumbs({ current, path }: { current: string; path: `/${string}` }) {
  const origin = canonicalSiteOrigin();
  const structuredData = origin ? {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: `${origin}/` },
      { "@type": "ListItem", position: 2, name: current, item: `${origin}${path}` },
    ],
  } as const : undefined;

  return <>
    {structuredData ? <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: serializeStructuredData(structuredData) }} /> : null}
    <nav className="public-breadcrumbs" aria-label="Breadcrumb">
      <ol>
        <li><Link href="/">Home</Link></li>
        <li aria-current="page">{current}</li>
      </ol>
    </nav>
  </>;
}
