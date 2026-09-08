import type { ReactNode } from "react";
import { PublicBreadcrumbs } from "@/components/public-breadcrumbs";
import { PageHeader } from "@/components/ui";

export function PublicDoc({ title, summary, path, children, draft = false }: { title: string; summary: string; path?: `/${string}`; children: ReactNode; draft?: boolean }) {
  return <>{path ? <PublicBreadcrumbs current={title} path={path} /> : null}<PageHeader title={title} label={draft ? "DRAFT — REVIEW REQUIRED" : "PUBLIC INFORMATION"} stamp="PRE-RELEASE">{summary}</PageHeader><article className="public-doc">{draft && <p className="doc-draft">This pre-release document requires owner and legal review before production.</p>}{children}</article></>;
}
