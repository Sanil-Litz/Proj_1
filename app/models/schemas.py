from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CandleDirection(str, Enum):
    bullish = "bullish"
    bearish = "bearish"
    neutral = "neutral"


class PredictionRequest(BaseModel):
    symbol: str = Field(description="Indian symbol, e.g. NSE:NIFTY50")
    timeframe: str = Field(description="1m, 5m, 15m, 1h, 1d")
    as_of: datetime


class PatternProbability(BaseModel):
    pattern_name: str
    p_next_bullish: float
    p_next_bearish: float
    sample_size: int


class PredictionResponse(BaseModel):
    symbol: str
    timeframe: str
    as_of: datetime
    direction: CandleDirection
    confidence_pct: float
    expected_volatility: float
    expected_candle_size_low: float
    expected_candle_size_high: float
    top_patterns: list[PatternProbability]
    analog_case_ids: list[str]


class ValidationRequest(BaseModel):
    prediction: PredictionResponse


class ValidationResponse(BaseModel):
    approved: bool
    adjusted_confidence_pct: float
    reasons: list[str]


class BackfillRequest(BaseModel):
    symbol: str
    timeframe: str
    years: int = Field(default=20, ge=15, le=30)


class HistoryResponseRow(BaseModel):
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    body_size: float
    upper_wick_ratio: float
    lower_wick_ratio: float
    gap_pct: float
    volatility_regime: str
