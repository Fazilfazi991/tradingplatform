import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Synthetic Historical Intelligence Demo",
  robots: { index: false, follow: false },
};

export default function HistoricalLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
