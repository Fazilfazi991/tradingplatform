export function timingSafeTextEqual(left: string, right: string): boolean {
  const length = Math.max(left.length, right.length);
  let mismatch = left.length ^ right.length;
  for (let index = 0; index < length; index += 1) {
    mismatch |= (left.charCodeAt(index) || 0) ^ (right.charCodeAt(index) || 0);
  }
  return mismatch === 0;
}

export function validBasicAuthorization(
  header: string | null,
  expectedUser: string | undefined,
  expectedPassword: string | undefined,
): boolean {
  if (!expectedUser || !expectedPassword || !header?.startsWith("Basic ")) return false;
  try {
    const decoded = atob(header.slice(6));
    const separator = decoded.indexOf(":");
    if (separator < 0) return false;
    return timingSafeTextEqual(decoded.slice(0, separator), expectedUser)
      && timingSafeTextEqual(decoded.slice(separator + 1), expectedPassword);
  } catch {
    return false;
  }
}

export function internalAccessAudit(
  method: string,
  path: string,
  outcome: "AUTHORIZED" | "DENIED",
  occurredAt: Date = new Date(),
) {
  return {
    event: "INTERNAL_ROUTE_ACCESS" as const,
    outcome,
    method,
    path,
    occurred_at: occurredAt.toISOString(),
    sensitive_values_logged: false as const,
  };
}
