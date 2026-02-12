from __future__ import annotations

import numpy as np
import pandas as pd


def build_context(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "trend": "unknown",
            "volatility_cluster": "unknown",
            "volume_environment": "unknown",
            "phase": "unknown",
            "momentum": 0.0,
        }

    d = df.sort_values("ts").tail(120).copy()
    close = d["close"]
    ema_fast = close.ewm(span=20, adjust=False).mean().iloc[-1]
    ema_slow = close.ewm(span=60, adjust=False).mean().iloc[-1]

    trend = "up" if ema_fast > ema_slow else "down"
    returns = close.pct_change().dropna()
    vol = returns.std() if not returns.empty else 0.0
    volatility_cluster = "high" if vol > returns.rolling(30).std().median() else "normal"

    vol_ratio = d["volume"].tail(20).mean() / max(d["volume"].tail(100).mean(), 1e-9)
    volume_environment = "institutional" if vol_ratio > 1.2 else "retail"

    hi = d["high"].tail(20).max()
    lo = d["low"].tail(20).min()
    phase = "consolidation" if (hi - lo) / max(close.iloc[-1], 1e-9) < 0.015 else "expansion"

    momentum = float(np.polyfit(np.arange(len(close.tail(30))), close.tail(30).to_numpy(), 1)[0])

    expiry_driven = bool(d.get("is_expiry_day", pd.Series([False])).tail(5).any())
    budget = bool(d.get("is_budget_day", pd.Series([False])).tail(3).any())
    rbi = bool(d.get("is_rbi_policy_day", pd.Series([False])).tail(3).any())

    return {
        "trend": trend,
        "volatility_cluster": volatility_cluster,
        "volume_environment": volume_environment,
        "phase": "expiry_driven" if expiry_driven else phase,
        "momentum": momentum,
        "budget_context": budget,
        "rbi_context": rbi,
    }
