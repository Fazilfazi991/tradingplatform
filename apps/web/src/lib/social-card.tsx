import { ImageResponse } from "next/og";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

const newsreader = readFile(
  join(process.cwd(), "public", "fonts", "newsreader-500.ttf"),
).then((data) => Uint8Array.from(data).buffer);
const manrope = readFile(
  join(process.cwd(), "public", "fonts", "manrope-400.ttf"),
).then((data) => Uint8Array.from(data).buffer);

const traces = [74, 61, 82, 48, 68, 57, 39];

export async function socialCardImage() {
  const [newsreaderData, manropeData] = await Promise.all([newsreader, manrope]);
  return new ImageResponse(
    <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", background: "#07100f", color: "#ecf2ed", padding: "58px 64px 42px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 15 }}>
          <svg width="40" height="40" viewBox="0 0 64 64" aria-hidden="true">
            <rect width="64" height="64" rx="14" fill="#0d1716" stroke="#263832" />
            <path d="M16 18 31 47 48 15M23 30h18" fill="none" stroke="#e6b35c" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <div style={{ display: "flex", fontFamily: "Newsreader Variable", fontSize: 28, letterSpacing: "-0.02em" }}>Verified Edge</div>
        </div>
        <div style={{ display: "flex", color: "#9fb0a6", fontFamily: "Manrope Variable", fontSize: 14 }}>Market Prediction Intelligence</div>
      </div>
      <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 70 }}>
        <div style={{ width: 670, display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", fontFamily: "Newsreader Variable", fontSize: 76, lineHeight: 0.98, letterSpacing: "-0.035em" }}>Market intelligence that shows its work.</div>
          <div style={{ display: "flex", maxWidth: 610, marginTop: 28, color: "#9fb0a6", fontFamily: "Manrope Variable", fontSize: 20, lineHeight: 1.5 }}>Independent evidence, contradiction, provenance, and uncertainty remain visible.</div>
        </div>
        <div style={{ width: 330, display: "flex", alignItems: "center" }}>
          <div style={{ width: 190, display: "flex", flexDirection: "column", gap: 13 }}>
            {traces.map((value, index) => <div key={value} style={{ height: 7, display: "flex", alignItems: "center", background: "#15221f" }}><div style={{ width: `${value}%`, height: 2, display: "flex", background: index === 6 ? "#e6b35c" : "#9fb0a6" }} /></div>)}
          </div>
          <div style={{ width: 122, height: 122, marginLeft: 18, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", border: "1px solid #e6b35c", borderRadius: 999, background: "#0d1716", color: "#ecf2ed", fontFamily: "Newsreader Variable", fontSize: 18, lineHeight: 1.15, textAlign: "center" }}>
            <div style={{ display: "flex" }}>Evidence</div>
            <div style={{ display: "flex" }}>synthesis</div>
          </div>
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: 22, borderTop: "1px solid #263832", color: "#9fb0a6", fontFamily: "Manrope Variable", fontSize: 13, letterSpacing: "0.06em", textTransform: "uppercase" }}>
        <div style={{ display: "flex" }}>Evidence · Contradiction · Provenance · Abstention</div>
        <div style={{ display: "flex", color: "#e6b35c" }}>Research platform · No trading signals</div>
      </div>
    </div>,
    {
      width: 1200,
      height: 630,
      fonts: [
        { name: "Newsreader Variable", data: newsreaderData, weight: 500 },
        { name: "Manrope Variable", data: manropeData, weight: 400 },
      ],
    },
  );
}
