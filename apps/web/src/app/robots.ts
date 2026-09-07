import type { MetadataRoute } from "next";
export default function robots(): MetadataRoute.Robots {
  const origin = process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "");
  return { rules: { userAgent: "*", allow: "/", disallow: ["/research", "/research-desk", "/data-health", "/settings", "/api/"] }, ...(origin ? { sitemap: `${origin}/sitemap.xml`, host: origin } : {}) };
}
