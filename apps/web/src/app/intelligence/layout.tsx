import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Synthetic Market Intelligence Demo",
  robots: { index: false, follow: false },
};

export default function IntelligenceLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
