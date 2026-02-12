from __future__ import annotations

import pandas as pd

PATTERN_COLUMNS = [
    "doji",
    "hammer",
    "inverted_hammer",
    "bullish_engulfing",
    "bearish_engulfing",
    "inside_bar",
    "breakout",
    "fake_breakout",
    "liquidity_sweep",
    "vwap_rejection",
]


def detect_patterns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    out = df.copy().sort_values("ts").reset_index(drop=True)
    body = (out["close"] - out["open"]).abs()
    candle_range = (out["high"] - out["low"]).replace(0, 1e-9)

    out["doji"] = (body / candle_range) < 0.1
    out["hammer"] = (out["lower_wick_ratio"] > 0.5) & (body / candle_range < 0.4)
    out["inverted_hammer"] = (out["upper_wick_ratio"] > 0.5) & (body / candle_range < 0.4)

    prev_open = out["open"].shift(1)
    prev_close = out["close"].shift(1)
    out["bullish_engulfing"] = (out["close"] > out["open"]) & (prev_close < prev_open) & (out["close"] > prev_open) & (out["open"] < prev_close)
    out["bearish_engulfing"] = (out["close"] < out["open"]) & (prev_close > prev_open) & (out["open"] > prev_close) & (out["close"] < prev_open)

    out["inside_bar"] = (out["high"] < out["high"].shift(1)) & (out["low"] > out["low"].shift(1))
    rolling_high = out["high"].rolling(20, min_periods=5).max().shift(1)
    rolling_low = out["low"].rolling(20, min_periods=5).min().shift(1)
    out["breakout"] = (out["close"] > rolling_high) | (out["close"] < rolling_low)
    out["fake_breakout"] = out["breakout"].shift(1).fillna(False) & (~out["breakout"])

    out["liquidity_sweep"] = ((out["high"] > out["high"].shift(1)) & (out["close"] < out["high"].shift(1))) | ((out["low"] < out["low"].shift(1)) & (out["close"] > out["low"].shift(1)))

    vwap = (out["close"] * out["volume"]).cumsum() / out["volume"].replace(0, 1).cumsum()
    out["vwap_rejection"] = ((out["low"] < vwap) & (out["close"] > vwap)) | ((out["high"] > vwap) & (out["close"] < vwap))

    return out


def pattern_probabilities(df: pd.DataFrame) -> list[dict]:
    out: list[dict] = []
    if df.empty:
        return out

    target = (df["close"].shift(-1) > df["close"]).astype(int)
    for pattern in PATTERN_COLUMNS:
        sample = df[df[pattern] == True]  # noqa: E712
        if sample.empty:
            continue
        idx = sample.index
        y = target.loc[idx].dropna()
        if y.empty:
            continue
        p_bull = float(y.mean())
        out.append(
            {
                "pattern_name": pattern,
                "p_next_bullish": p_bull,
                "p_next_bearish": 1.0 - p_bull,
                "sample_size": int(y.shape[0]),
            }
        )
    out.sort(key=lambda r: r["sample_size"], reverse=True)
    return out[:5]
