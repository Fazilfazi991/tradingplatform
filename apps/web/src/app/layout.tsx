import type { Metadata } from "next";
import { AppShell } from "@/components/app-shell";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL;
export const metadata: Metadata = {
  ...(siteUrl ? { metadataBase: new URL(siteUrl) } : {}),
  title: { default: "Verified Edge · Evidence-led market intelligence", template: "%s · Verified Edge" },
  description: "Inspect independent market evidence, contradiction, uncertainty, provenance, and abstention in a clearly labelled research demonstration.",
  applicationName: "Verified Edge",
  openGraph: { type: "website", siteName: "Verified Edge", title: "Market intelligence that shows its work", description: "Evidence-led market research with contradictions and uncertainty intact." },
  twitter: { card: "summary", title: "Verified Edge", description: "Evidence-led market research with contradictions and uncertainty intact." },
};

export default function RootLayout({ children }: Readonly<{children:React.ReactNode}>) { return <html lang="en" data-scroll-behavior="smooth"><body><AppShell>{children}</AppShell></body></html>; }
