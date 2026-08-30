from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd


class CausalFeatureExtractor(ABC):
    @abstractmethod
    def transform(self, observations: pd.DataFrame, cutoff: datetime) -> pd.DataFrame:
        """Transform only observations whose available_at is no later than cutoff."""

    @staticmethod
    def eligible(observations: pd.DataFrame, cutoff: datetime) -> pd.DataFrame:
        available = pd.to_datetime(observations["available_at"], utc=True)
        stamp = pd.Timestamp(cutoff)
        if stamp.tzinfo is None:
            raise ValueError("cutoff must be timezone-aware")
        return observations.loc[available <= stamp].copy()


class NewsFeatureExtractor(CausalFeatureExtractor):
    def transform(self, observations, cutoff):
        return self.eligible(observations, cutoff)


class SentimentFeatureExtractor(CausalFeatureExtractor):
    def transform(self, observations, cutoff):
        return self.eligible(observations, cutoff)


class FundamentalFeatureExtractor(CausalFeatureExtractor):
    def transform(self, observations, cutoff):
        return self.eligible(observations, cutoff)


class MacroFeatureExtractor(CausalFeatureExtractor):
    def transform(self, observations, cutoff):
        return self.eligible(observations, cutoff)


class FlowFeatureExtractor(CausalFeatureExtractor):
    def transform(self, observations, cutoff):
        return self.eligible(observations, cutoff)


class DerivativesFeatureExtractor(CausalFeatureExtractor):
    def transform(self, observations, cutoff):
        return self.eligible(observations, cutoff)
