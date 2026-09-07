export const models = [
  ["Technical Engine", "Demo", "Synthetic OHLCV fixtures", "Trend, momentum, volatility and relative strength", "0.2-demo"],
  ["Historical Analogue Engine", "Demo", "Synthetic analogue fixtures", "Find structurally similar past market states", "0.1-demo"],
  ["News / Event Engine", "Demo", "Synthetic event fixtures", "Classify material events with information-time controls", "0.1-demo"],
  ["Sentiment / Psychology Engine", "Demo", "Synthetic psychology fixtures", "Separate attention, tone, fear and euphoria", "0.1-demo"],
  ["Fundamental Engine", "Demo", "Synthetic fundamental fixtures", "Interpret earnings quality, revisions and valuation context", "0.1-demo"],
  ["Macro / Regime Engine", "Demo", "Synthetic macro fixtures", "Describe the environment conditioning every forecast", "0.1-demo"],
  ["Flow / Positioning Engine", "Unavailable", "No public-safe source", "Measure institutional, delivery and derivatives positioning", "—"],
  ["Evidence Fusion Engine", "Demo · Abstain", "Synthetic specialist fixtures", "Combine evidence without hiding disagreement", "0.1-demo"],
].map(([name, status, sources, purpose, version]) => ({ name, status, sources, purpose, version }));
