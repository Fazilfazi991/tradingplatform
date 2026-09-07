import type { MetadataRoute } from "next";
import { canonicalSiteOrigin } from "@/lib/site-url";

export default function robots(): MetadataRoute.Robots {
  const origin = canonicalSiteOrigin();
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: [
        "/research",
        "/research-desk",
        "/data-health",
        "/settings",
        "/api/",
        "/predictions",
        "/stocks/",
        "/fusion",
        "/historical",
        "/intelligence",
        "/sectors",
      ],
    },
    ...(origin ? { sitemap: `${origin}/sitemap.xml`, host: origin } : {}),
  };
}
