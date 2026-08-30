export const models = [
  ["Technical Engine", "Prototype", "OHLCV fixtures", "Trend, momentum, volatility and relative strength", "0.2-demo"],
  ["Historical Analogue Engine", "Planned", "Not connected", "Find structurally similar past market states", "—"],
  ["News / Event Engine", "Planned", "Not connected", "Classify material events with information-time controls", "—"],
  ["Sentiment / Psychology Engine", "Planned", "Not connected", "Separate attention, tone, fear and euphoria", "—"],
  ["Fundamental Engine", "Planned", "Not connected", "Interpret earnings quality, revisions and valuation context", "—"],
  ["Macro / Regime Engine", "Prototype", "Synthetic fixtures", "Describe the environment conditioning every forecast", "0.1-demo"],
  ["Flow / Positioning Engine", "Blocked", "Source not connected", "Measure institutional, delivery and derivatives positioning", "—"],
  ["Prediction Fusion Engine", "Not started", "Depends on validated engines", "Combine evidence without hiding disagreement", "—"],
].map(([name, status, sources, purpose, version]) => ({ name, status, sources, purpose, version }));
