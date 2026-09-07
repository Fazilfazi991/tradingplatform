import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Synthetic Sector Intelligence Demo",
  robots: { index: false, follow: false },
};

export default function SectorsLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return children;
}
