export class FixedWindowLimiter {
  private hits: number[] = [];
  private readonly maximum: number;
  private readonly windowMs: number;

  constructor(maximum: number, windowMs: number) {
    if (maximum <= 0 || windowMs <= 0) throw new Error("rate-limit bounds must be positive");
    this.maximum = maximum;
    this.windowMs = windowMs;
  }

  allow(now = Date.now()): boolean {
    const cutoff = now - this.windowMs;
    this.hits = this.hits.filter((timestamp) => timestamp > cutoff);
    if (this.hits.length >= this.maximum) return false;
    this.hits.push(now);
    return true;
  }
}

export class MemoryTtlCache<T> {
  private entry: { expiresAt: number; value: T } | undefined;
  private readonly ttlMs: number;

  constructor(ttlMs: number) {
    if (ttlMs <= 0) throw new Error("cache TTL must be positive");
    this.ttlMs = ttlMs;
  }

  get(now = Date.now()): T | undefined {
    if (!this.entry || this.entry.expiresAt <= now) return undefined;
    return this.entry.value;
  }

  set(value: T, now = Date.now()): void {
    this.entry = { value, expiresAt: now + this.ttlMs };
  }
}
