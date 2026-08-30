from __future__ import annotations

import numpy as np
import pandas as pd

from research_core.objects import EvidenceEngineOutput


class TechnicalEvidenceEngine:
    version = "technical-evidence-v0"

    def evaluate(
        self, features: pd.Series, *, as_of, target: str, horizon: int
    ) -> EvidenceEngineOutput:
        states = {
            "trend": _state(features.get("sma_distance_pct_50")),
            "momentum": _state(features.get("return_20")),
            "volume": _state(features.get("volume_median_ratio_20"), neutral=1),
            "volatility": "caution" if features.get("atr_price_14", 0) > 0.04 else "neutral",
            "relative_strength": _state(features.get("relative_strength_market_20")),
            "structure": _state(
                features.get("distance_high_20") + 0.03
                if pd.notna(features.get("distance_high_20"))
                else np.nan
            ),
        }
        mapping = {"supportive": 1, "neutral": 0, "caution": -1, "contradictory": -1}
        score = 50 + 10 * sum(mapping[value] for value in states.values())
        contradictions = tuple(
            key for key, value in states.items() if value in {"caution", "contradictory"}
        )
        return EvidenceEngineOutput(
            engine_id="technical",
            engine_version=self.version,
            as_of=as_of,
            target=target,
            horizon=horizon,
            directional_score=float(np.clip(score, 0, 100)),
            confidence_quality="LOW",
            data_quality="PASS",
            evidence_count=len(states),
            explanation_payload=states,
            contradictions=contradictions,
            provenance={"mode": "ENGINEERING_FIXTURE", "feature_version": "technical-v1"},
        )


class HistoricalEvidenceEngine:
    version = "historical-evidence-v0"

    def evaluate(
        self, analogue_result, *, as_of, target: str, horizon: int
    ) -> EvidenceEngineOutput:
        agg = analogue_result.aggregate
        count = int(agg.get("sample_size", 0))
        positive = float(agg.get("positive_percentage", 0.5))
        return EvidenceEngineOutput(
            engine_id="historical",
            engine_version=self.version,
            as_of=as_of,
            target=target,
            horizon=horizon,
            directional_score=positive * 100,
            confidence_quality="LOW",
            data_quality="PASS" if count else "BLOCKED",
            evidence_count=count,
            explanation_payload={
                "analogue_count": count,
                "positive_frequency": positive,
                "median_outcome": agg.get("median_return"),
                "dispersion": [agg.get("q10"), agg.get("q90")],
                "method": analogue_result.method,
            },
            contradictions=(),
            provenance={"mode": "ENGINEERING_FIXTURE", "past_only": True},
        )


def _state(value, neutral: float = 0) -> str:
    if pd.isna(value):
        return "neutral"
    if value > neutral:
        return "supportive"
    if value < neutral:
        return "contradictory"
    return "neutral"
