export const INTERNAL_ROUTE_PREFIXES = [
  "/research",
  "/research-desk",
  "/data-health",
  "/settings",
  "/api/research-desk",
] as const;

export type SurfaceClass = "PUBLIC" | "DEMO" | "INTERNAL_RESEARCH" | "INTERNAL_ADMIN";

export function isInternalPath(pathname: string): boolean {
  return INTERNAL_ROUTE_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function classifySurface(pathname: string): SurfaceClass {
  if (pathname === "/research" || pathname.startsWith("/research/")) {
    return "INTERNAL_RESEARCH";
  }
  if (isInternalPath(pathname)) return "INTERNAL_ADMIN";
  if (
    pathname === "/predictions" ||
    pathname.startsWith("/stocks/") ||
    pathname === "/sectors" ||
    pathname === "/intelligence" ||
    pathname === "/historical"
  ) return "DEMO";
  return "PUBLIC";
}
