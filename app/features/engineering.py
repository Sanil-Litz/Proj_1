from __future__ import annotations

import numpy as np
import pandas as pd


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    out = df.copy().sort_values("ts").reset_index(drop=True)
    rng = (out["high"] - out["low"]).replace(0, np.nan)
    body = (out["close"] - out["open"]).abs()

    out["body_size"] = body
    out["upper_wick_ratio"] = (out["high"] - out[["open", "close"]].max(axis=1)) / rng
    out["lower_wick_ratio"] = (out[["open", "close"]].min(axis=1) - out["low"]) / rng
    out["volume_change"] = out["volume"].pct_change().fillna(0.0)
    out["gap_pct"] = (out["open"] - out["close"].shift(1)).div(out["close"].shift(1)).fillna(0.0)

    ret = out["close"].pct_change().fillna(0.0)
    rolling_vol = ret.rolling(20, min_periods=5).std().fillna(0.0)
    q1, q2 = rolling_vol.quantile([0.33, 0.66]).tolist()

    out["volatility_regime"] = np.select(
        [rolling_vol <= q1, rolling_vol <= q2],
        ["low", "medium"],
        default="high",
    )

    out["pre_expiry_flag"] = out.get("is_expiry_day", False).shift(-1).fillna(False)
    out["post_expiry_flag"] = out.get("is_expiry_day", False).shift(1).fillna(False)
    return out.fillna(0.0)
