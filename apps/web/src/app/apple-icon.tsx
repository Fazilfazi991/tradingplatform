import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
  return new ImageResponse(
    <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", borderRadius: 36, background: "#07100f" }}>
      <svg width="116" height="116" viewBox="0 0 64 64" aria-hidden="true">
        <rect width="64" height="64" rx="14" fill="#0d1716" stroke="#263832" />
        <path d="M16 18 31 47 48 15M23 30h18" fill="none" stroke="#e6b35c" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>,
    size,
  );
}
