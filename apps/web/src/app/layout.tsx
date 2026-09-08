import type { Metadata } from "next";
import { AppShell } from "@/components/app-shell";
import {
  publicProductDescription,
  publicWebsiteStructuredData,
  serializeStructuredData,
} from "@/lib/public-metadata";
import { canonicalSiteOrigin } from "@/lib/site-url";
import "./globals.css";

const siteUrl = canonicalSiteOrigin();
export const metadata: Metadata = {
  ...(siteUrl ? { metadataBase: new URL(siteUrl) } : {}),
  title: { default: "Verified Edge · Evidence-led market intelligence", template: "%s · Verified Edge" },
  description: publicProductDescription,
  applicationName: "Verified Edge",
  manifest: "/manifest.webmanifest",
  openGraph: { type: "website", siteName: "Verified Edge", title: "Market intelligence that shows its work", description: "Evidence-led market research with contradictions and uncertainty intact." },
  twitter: { card: "summary", title: "Verified Edge", description: "Evidence-led market research with contradictions and uncertainty intact." },
};

export default function RootLayout({ children }: Readonly<{children:React.ReactNode}>) {
  const structuredData = siteUrl ? publicWebsiteStructuredData(siteUrl) : undefined;
  return <html lang="en" data-scroll-behavior="smooth"><body>{structuredData ? <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: serializeStructuredData(structuredData) }} /> : null}<AppShell>{children}</AppShell></body></html>;
}
