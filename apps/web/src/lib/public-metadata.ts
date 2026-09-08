export const publicProductDescription =
  "Inspect independent market evidence, contradiction, uncertainty, provenance, and abstention in a clearly labelled research demonstration.";

export function publicWebsiteStructuredData(origin: string) {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": `${origin}/#website`,
    url: `${origin}/`,
    name: "Verified Edge",
    alternateName: "Verified Edge Market Prediction Intelligence",
    description: publicProductDescription,
    inLanguage: "en",
    publisher: {
      "@type": "Organization",
      "@id": `${origin}/#organization`,
      name: "Verified Edge",
      url: `${origin}/`,
    },
  } as const;
}

export function serializeStructuredData(value: unknown): string {
  return JSON.stringify(value).replaceAll("<", "\\u003c");
}
