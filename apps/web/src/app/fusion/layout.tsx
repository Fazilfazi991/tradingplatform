import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Synthetic Evidence Fusion Demo",
  description: "A synthetic demonstration of evidence synthesis, contradiction handling, and abstention.",
  robots: { index: false, follow: false },
};

export default function FusionLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
