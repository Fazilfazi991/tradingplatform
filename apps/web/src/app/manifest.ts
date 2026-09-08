import type { MetadataRoute } from "next";

import { publicProductDescription } from "@/lib/public-metadata";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "Verified Edge — Market Prediction Intelligence",
    short_name: "Verified Edge",
    description: publicProductDescription,
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#07100f",
    theme_color: "#07100f",
    categories: ["finance", "education"],
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml" }],
  };
}
