from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass(slots=True)
class ProviderRequest:
    symbol: str
    timeframe: str
    start: datetime
    end: datetime


class BaseIndianMarketProvider:
    name = "base"

    def fetch_ohlcv(self, req: ProviderRequest) -> pd.DataFrame:
        raise NotImplementedError


class EmptyProvider(BaseIndianMarketProvider):
    """Safe fallback used when provider keys are missing.

    Returns an empty DataFrame with required columns so ingestion pipelines remain deterministic.
    """

    name = "empty"

    def fetch_ohlcv(self, req: ProviderRequest) -> pd.DataFrame:
        return pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume"])
