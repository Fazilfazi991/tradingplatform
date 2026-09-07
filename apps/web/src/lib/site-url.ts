export function canonicalSiteOrigin(
  environment: Readonly<Record<string, string | undefined>> = process.env,
): string | undefined {
  const configured = environment.NEXT_PUBLIC_SITE_URL
    ?? environment.VERCEL_PROJECT_PRODUCTION_URL
    ?? environment.VERCEL_URL;
  if (!configured?.trim()) return undefined;
  try {
    const candidate = new URL(
      /^https?:\/\//i.test(configured) ? configured : `https://${configured}`,
    );
    const local = candidate.hostname === "localhost" || candidate.hostname === "127.0.0.1";
    if (candidate.protocol !== "https:" && !local) return undefined;
    return candidate.origin;
  } catch {
    return undefined;
  }
}
