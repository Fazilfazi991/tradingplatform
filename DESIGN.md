---
name: Verified Edge
description: A public prediction-intelligence observatory that keeps evidence, disagreement, and demo provenance visible.
colors:
  ink: "#07100f"
  carbon: "#0d1716"
  moss: "#15221f"
  chalk: "#ecf2ed"
  sage: "#9fb0a6"
  signal-amber: "#e6b35c"
  direction-jade: "#48c78e"
  direction-coral: "#ef786f"
  context-blue: "#77a8c7"
typography:
  display:
    fontFamily: "Newsreader Variable, Georgia, serif"
    fontSize: "clamp(30px, 3.6vw, 43px)"
    fontWeight: 500
    lineHeight: 1.05
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Newsreader Variable, Georgia, serif"
    fontSize: "20px"
    fontWeight: 500
    lineHeight: 1.2
  metric:
    fontFamily: "Newsreader Variable, Georgia, serif"
    fontSize: "23px"
    fontWeight: 600
    lineHeight: 1
  body:
    fontFamily: "Manrope Variable, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: "Manrope Variable, Arial, sans-serif"
    fontSize: "9px"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.09em"
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, monospace"
    fontSize: "10px"
    fontWeight: 400
    lineHeight: 1.4
spacing:
  hairline: "4px"
  compact: "8px"
  control: "12px"
  cluster: "14px"
  panel: "20px"
  section: "30px"
  canvas-gutter: "34px"
rounded:
  data-bar: "2px"
  control: "10px"
  status: "12px"
  surface: "14px"
  pill: "999px"
components:
  navigation-item:
    backgroundColor: "transparent"
    textColor: "{colors.sage}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 11px"
    height: "39px"
  navigation-item-active:
    backgroundColor: "#16231f"
    textColor: "{colors.chalk}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 11px"
    height: "39px"
  panel:
    backgroundColor: "{colors.carbon}"
    textColor: "{colors.chalk}"
    rounded: "{rounded.surface}"
    padding: "{spacing.panel}"
  filter:
    backgroundColor: "{colors.carbon}"
    textColor: "{colors.chalk}"
    typography: "{typography.body}"
    rounded: "{rounded.pill}"
    padding: "8px 13px"
  tag-prototype:
    backgroundColor: "#2a2416"
    textColor: "{colors.signal-amber}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 9px"
    height: "25px"
  tag-supportive:
    backgroundColor: "transparent"
    textColor: "{colors.direction-jade}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 9px"
    height: "25px"
  tag-contradictory:
    backgroundColor: "transparent"
    textColor: "{colors.direction-coral}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 9px"
    height: "25px"
  consensus-node:
    backgroundColor: "#11211c"
    textColor: "{colors.chalk}"
    rounded: "{rounded.pill}"
    size: "152px"
---

# Design System: Verified Edge

## Overview

**Creative North Star: "The Evidence Lens"**

Verified Edge is an Operate-mode public prediction-intelligence observatory. Its visual world is an
editorial financial atlas rendered on near-black matte surfaces: rigorous enough to inspect quickly,
quiet enough to read at length, and candid enough to leave disagreement in view. It is not brokerage
chrome, a neon trading terminal, or a generic admin dashboard.

The system makes evidence relationships visible. Seven independent traces converge into one circular
consensus node, while the contradictory Flows trace remains coral and legibly separate. Restraint is
the governing aesthetic: amber marks attention and prototype provenance; jade and coral appear only
when direction is genuinely being communicated.

**Key Characteristics:**

- Near-black matte canvases with fine green-gray rules and shallow tonal layering.
- Editorial serif headlines paired with a compact, highly legible sans interface.
- An asymmetric desktop rail-and-canvas composition that becomes a stacked mobile evidence record.
- Explicit demo provenance at the shell, page, and data-component levels.
- Authored convergence motion with an immediate reduced-motion equivalent.

## Colors

The palette is a restrained nocturnal atlas: dark green-black neutrals carry the interface, warm amber
labels research state, and directional hues are scarce enough to retain analytical meaning.

### Primary

- **Signal Amber** (`signal-amber`): prototype labels, active filters, focus outlines, and uncertainty or
  attention states; never a general fill color.

### Secondary

- **Direction Jade** (`direction-jade`): supportive, bullish, or passing evidence only.
- **Direction Coral** (`direction-coral`): bearish, blocked, or contradictory evidence only.

### Tertiary

- **Context Blue** (`context-blue`): neutral, deferred, or contextual data that is neither supportive
  nor contradictory.

### Neutral

- **Ink** (`ink`): the primary page canvas and scrollbar track.
- **Carbon** (`carbon`): working panels, cards, metrics, filters, and chart tooltips.
- **Moss** (`moss`): secondary surface language and active navigation tonality.
- **Chalk** (`chalk`): primary text and high-emphasis numeric content.
- **Sage** (`sage`): supporting copy, captions, annotations, and low-emphasis labels.

### Named Rules

**The Direction Has Meaning Rule.** Jade and coral are reserved for real directional semantics. A
decorative accent must use the neutral or amber vocabulary instead.

**The Provenance Is Warm Rule.** Amber identifies prototype status, uncertainty, focus, and research
attention so demo context remains perceptually distinct from model direction.

## Typography

**Display Font:** Newsreader Variable (with Georgia and serif fallbacks)

**Body Font:** Manrope Variable (with Arial and sans-serif fallbacks)

**Label/Mono Font:** System UI monospace for timestamps and availability metadata

**Character:** Newsreader supplies the authority and measured cadence of an editorial financial atlas;
Manrope keeps dense evidence legible and contemporary. Monospace appears only where the content is
machine-like: timestamps, snapshots, and source availability.

### Hierarchy

- **Display** (500, fluid 30–43px, 1.05 line-height): page titles and regime statements; tightly tracked
  but never compressed beyond the established display role.
- **Title** (500, 20px, 1.2 line-height): card headlines and explanatory group names.
- **Metric** (600, 23px, 1 line-height): tabular market pulse values and compact numeric emphasis.
- **Body** (400, 12px, 1.7 line-height): explanations and evidence descriptions; extended prose remains
  near a 68-character measure.
- **Label** (700, 9px, 0.09em tracking, uppercase): status tags and compact state markers.
- **Mono** (400, 10px, 1.4 line-height): snapshot timestamps and source-status metadata.

### Named Rules

**The Editorial/Data Split Rule.** Newsreader interprets and emphasizes; Manrope operates and explains;
monospace authenticates time and source state. Do not interchange these jobs for variety.

## Layout

Desktop uses a fixed 244px navigation rail, a sticky 42px demo banner, and an asymmetric main canvas
with 34px horizontal gutters and a 1600px maximum content width. The Overview's signature consensus
field divides into a 240px regime panel, a flexible evidence field, and a 250px contradiction panel.
Four-up metrics, three-up explanatory cards, and two-up evidence groups provide compact scanning
without turning the page into a uniform dashboard grid.

At 1050px, the rail contracts to 190px, the contradiction panel drops beneath the consensus field,
metrics become two-up, and lower-priority prediction columns disappear. At 760px and below, the rail
becomes a compact sticky brand strip plus horizontally scrollable navigation; page gutters reduce to
16–18px, evidence traces stack above the circular node, and cards, news, and evidence groups become
single-column records. The consensus relationship remains intelligible even when connector lines are
removed on mobile.

The spacing rhythm is compact inside data structures and deliberately open between sections: 8–14px
for control clusters, 18–20px for cells and cards, and 30px between major sections.

## Elevation & Depth

The system is flat by default and uses tonal layering plus fine low-contrast borders to establish
depth. Panels sit on Ink as Carbon surfaces; selected regions shift slightly toward Moss. Shadows are
not a general card treatment. The circular consensus node alone receives a soft ambient shadow so the
convergence destination reads as a focal object rather than another cell.

### Shadow Vocabulary

- **Consensus Ambient** (`0 16px 34px rgba(0,0,0,.24)`): reserved for the circular consensus node.
- **Banner Blur** (`backdrop-filter: blur(12px)`): used only on the sticky provenance banner to preserve
  separation while content scrolls beneath it.

### Named Rules

**The Border-First Rule.** Establish ordinary hierarchy with surface tone and one-pixel rules; do not
add card shadows. The consensus node is the intentional exception.

## Shapes

Working surfaces use gently rounded 14px corners, compact navigation and chart tooltips use 10px, and
research-status containers use 12px. Pills are reserved for filters, tags, sector markers, and true
state capsules. Data bars remain almost square at 2px, while the consensus node is a true circle whose
geometry visually resolves the incoming evidence traces.

Fine one-pixel borders carry most separation. Dense metric and status groups share outer clipping so
their internal rules read as one atlas plate rather than a collection of floating cards.

## Components

### Navigation

- **Style:** a fixed dark rail with 39px quiet rows, compact icons, and low-emphasis labels.
- **Active / Hover:** a Moss-toned inset field with Chalk text; the active icon alone receives amber.
- **Mobile:** the rail becomes a sticky brand strip followed by horizontally scrollable pill links.

### Filters and Action Cards

- **Shape:** filters are compact pills; model-selection cards retain the 14px surface radius.
- **Default:** Carbon surface, low-contrast green-gray border, and Chalk text.
- **Hover / Active:** amber border and text for filters; cards remain restrained and reveal detail in
  place rather than opening a decorative modal.
- **Focus:** the global 2px amber outline with 3px offset remains visible for keyboard operation.

### Tags

- **Style:** 25px-high uppercase capsules with 9px text, bold weight, and generous tracking.
- **Prototype:** amber text and border on a warm translucent-dark field.
- **Supportive / Passing:** jade text and border with no decorative fill.
- **Bearish / Blocked:** coral text and border with no decorative fill.
- **Neutral / Deferred:** blue text and border.

### Cards / Containers

- **Corner Style:** gently rounded working surfaces (14px).
- **Background:** Carbon over Ink, with rarer Moss-toned state shifts.
- **Shadow Strategy:** flat and border-defined; see the Border-First Rule.
- **Border:** one-pixel low-contrast green-gray rule.
- **Internal Padding:** usually 20px; evidence panels expand to 22px and focal regions to 26px.

### Data Rows and Metrics

- **Structure:** compact cells use shared outer clipping and internal dividers; tabular numerals prevent
  score and market-value jitter.
- **State:** row hover uses a subtle tonal shift, while directional change is carried by jade or coral
  text rather than a filled cell.
- **Responsive:** secondary prediction columns are progressively removed before the row becomes a
  two-column mobile record.

### Evidence Convergence

Seven independent evidence rows terminate visually at a 152px circular consensus node on desktop.
Each supportive trace uses jade; the contradictory Flows trace and connector remain coral. Trace bars
settle over 800ms with an exponential ease-out curve and 60ms per-row staggering. On mobile, connector
lines disappear, the traces remain individually readable, and the node centers beneath them. Reduced
motion users receive the complete state immediately.

### Demo Provenance

The sticky research banner, page snapshot stamp, research-mode rail card, and inline synthetic-data
note form a deliberate provenance system. Labels state what is synthetic and what is not live; blocked
states explain both the absent source and what would unlock it.

## Do's and Don'ts

### Do:

- **Do** keep synthetic/demo provenance visible at shell, page, and data-component levels.
- **Do** preserve all seven independent evidence traces and the circular consensus node as one
  readable convergence story.
- **Do** keep contradictory Flows coral even when the overall consensus is bullish.
- **Do** use borders and tonal layering for ordinary depth, reserving the ambient shadow for the node.
- **Do** preserve keyboard focus, semantic headings, chart summaries, tabular numerals, and the
  reduced-motion final state.
- **Do** convert desktop density into stacked mobile evidence records without hiding contradiction.

### Don't:

- **Don't** use jade or coral as decorative brand color or as an unqualified status flourish.
- **Don't** imply live data, validated probabilities, performance, execution, or financial advice.
- **Don't** replace the evidence model with a single hero score or decorative gauge.
- **Don't** turn the interface into neon sci-fi trading chrome, glassmorphism, or a generic admin grid.
- **Don't** add shadows to ordinary cards or round every container into a pill.
- **Don't** convey direction, contradiction, or blocked state through color alone.
