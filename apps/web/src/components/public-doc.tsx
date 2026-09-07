import type { ReactNode } from "react";
import { PageHeader } from "@/components/ui";

export function PublicDoc({ title, summary, children, draft = false }: { title: string; summary: string; children: ReactNode; draft?: boolean }) {
  return <><PageHeader title={title} label={draft ? "DRAFT — REVIEW REQUIRED" : "PUBLIC INFORMATION"} stamp="PRE-RELEASE">{summary}</PageHeader><article className="public-doc">{draft && <p className="doc-draft">This pre-release document requires owner and legal review before production.</p>}{children}</article></>;
}
