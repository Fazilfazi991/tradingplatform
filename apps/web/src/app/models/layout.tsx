import type { Metadata } from "next";
import { PublicBreadcrumbs } from "@/components/public-breadcrumbs";

export const metadata: Metadata = {
  title: "Evidence Engines",
  description: "How Verified Edge separates technical, historical, event, macro, fundamental, psychology, and positioning evidence.",
  alternates: { canonical: "/models" },
};

export default function ModelsLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <><PublicBreadcrumbs current="Seven evidence engines" path="/models" />{children}</>;
}
