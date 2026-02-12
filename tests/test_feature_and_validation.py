from datetime import datetime, timedelta, timezone

import pandas as pd

from app.features.engineering import compute_features
from app.features.pattern_engine import detect_patterns, pattern_probabilities
from app.models.schemas import CandleDirection, PredictionResponse
from app.validation.validator_service import ValidatorService


def sample_df(n: int = 120) -> pd.DataFrame:
    ts0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = []
    px = 100.0
    for i in range(n):
        o = px
        c = px + (0.3 if i % 2 == 0 else -0.2)
        h = max(o, c) + 0.2
        l = min(o, c) - 0.2
        rows.append(
            {
                "ts": ts0 + timedelta(minutes=i),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": 1000 + i,
                "is_expiry_day": False,
            }
        )
        px = c
    return pd.DataFrame(rows)


def test_feature_generation_and_pattern_probs() -> None:
    df = compute_features(sample_df())
    pat_df = detect_patterns(df)
    probs = pattern_probabilities(pat_df)
    assert "body_size" in df.columns
    assert "volatility_regime" in df.columns
    assert isinstance(probs, list)


def test_validator_adjusts_confidence() -> None:
    validator = ValidatorService()
    pred = PredictionResponse(
        symbol="NSE:NIFTY50",
        timeframe="5m",
        as_of=datetime.now(timezone.utc),
        direction=CandleDirection.bullish,
        confidence_pct=30,
        expected_volatility=0.04,
        expected_candle_size_low=5,
        expected_candle_size_high=20,
        top_patterns=[],
        analog_case_ids=[],
    )
    out = validator.validate(pred)
    assert out.adjusted_confidence_pct < pred.confidence_pct
    assert out.reasons
