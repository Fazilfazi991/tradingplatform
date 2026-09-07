import type { MetadataRoute } from "next";
const routes=["", "/methodology", "/data-sources", "/validation", "/about", "/faq", "/fusion", "/models"] as const;
export default function sitemap(): MetadataRoute.Sitemap {
  const origin = process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "");
  if (!origin) return [];
  return routes.map((route) => ({ url: `${origin}${route}`, changeFrequency: "monthly" as const, priority: route ? 0.7 : 1 }));
}
