import type { MetadataRoute } from "next";
import { canonicalSiteOrigin } from "@/lib/site-url";

const routes = [
  "",
  "/methodology",
  "/data-sources",
  "/validation",
  "/models",
  "/about",
  "/faq",
] as const;

export default function sitemap(): MetadataRoute.Sitemap {
  const origin = canonicalSiteOrigin();
  if (!origin) return [];
  return routes.map((route) => ({
    url: `${origin}${route}`,
    changeFrequency: "monthly" as const,
    priority: route ? 0.7 : 1,
  }));
}
