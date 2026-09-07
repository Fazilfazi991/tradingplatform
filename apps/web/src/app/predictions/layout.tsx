import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Synthetic Forecast Research Demo",
  description: "A clearly labelled synthetic demonstration of the Verified Edge forecast-research interface.",
  robots: { index: false, follow: false },
};

export default function PredictionsLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
