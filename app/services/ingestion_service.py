from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.features.engineering import compute_features
from app.ingestion.calendar_utils import is_monthly_expiry, is_weekly_expiry
from app.ingestion.providers import BaseIndianMarketProvider, ProviderRequest


class IngestionService:
    def __init__(self, provider: BaseIndianMarketProvider):
        self.provider = provider

    def backfill(self, db: Session, symbol: str, timeframe: str, years: int) -> int:
        end = datetime.utcnow()
        start = end - timedelta(days=365 * years)
        req = ProviderRequest(symbol=symbol, timeframe=timeframe, start=start, end=end)
        raw = self.provider.fetch_ohlcv(req)
        if raw.empty:
            return 0

        cooked = compute_features(self._attach_market_context(raw))
        self._upsert_ohlcv(db, symbol, timeframe, cooked)
        self._upsert_features(db, symbol, timeframe, cooked)
        db.commit()
        return int(cooked.shape[0])

    def ingest_live_tick(self, db: Session, payload: dict) -> None:
        row = pd.DataFrame([payload])
        row["ts"] = pd.to_datetime(row["ts"], utc=True)
        symbol = payload["symbol"]
        timeframe = payload["timeframe"]

        cooked = compute_features(self._attach_market_context(row))
        self._upsert_ohlcv(db, symbol, timeframe, cooked)
        self._upsert_features(db, symbol, timeframe, cooked)
        db.commit()

    def _attach_market_context(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["d"] = pd.to_datetime(out["ts"], utc=True).dt.date
        out["is_weekly_expiry"] = out["d"].apply(is_weekly_expiry)
        out["is_monthly_expiry"] = out["d"].apply(is_monthly_expiry)
        out["is_expiry_day"] = out["is_weekly_expiry"] | out["is_monthly_expiry"]
        out["is_budget_day"] = False
        out["is_rbi_policy_day"] = False
        out["is_global_spillover_day"] = False
        out.drop(columns=["d"], inplace=True)
        return out

    def _upsert_ohlcv(self, db: Session, symbol: str, timeframe: str, df: pd.DataFrame) -> None:
        stmt = text(
            """
            INSERT INTO ohlcv(symbol,timeframe,ts,open,high,low,close,volume,is_expiry_day,is_weekly_expiry,is_monthly_expiry,is_budget_day,is_rbi_policy_day,is_global_spillover_day)
            VALUES (:symbol,:timeframe,:ts,:open,:high,:low,:close,:volume,:is_expiry_day,:is_weekly_expiry,:is_monthly_expiry,:is_budget_day,:is_rbi_policy_day,:is_global_spillover_day)
            ON CONFLICT(symbol,timeframe,ts) DO UPDATE SET
              open=EXCLUDED.open,high=EXCLUDED.high,low=EXCLUDED.low,close=EXCLUDED.close,volume=EXCLUDED.volume,
              is_expiry_day=EXCLUDED.is_expiry_day,is_weekly_expiry=EXCLUDED.is_weekly_expiry,is_monthly_expiry=EXCLUDED.is_monthly_expiry,
              is_budget_day=EXCLUDED.is_budget_day,is_rbi_policy_day=EXCLUDED.is_rbi_policy_day,is_global_spillover_day=EXCLUDED.is_global_spillover_day
            """
        )
        for _, r in df.iterrows():
            db.execute(stmt, {**r.to_dict(), "symbol": symbol, "timeframe": timeframe})

    def _upsert_features(self, db: Session, symbol: str, timeframe: str, df: pd.DataFrame) -> None:
        stmt = text(
            """
            INSERT INTO ohlcv_features(symbol,timeframe,ts,body_size,upper_wick_ratio,lower_wick_ratio,volume_change,gap_pct,volatility_regime,pre_expiry_flag,post_expiry_flag,pattern_vector)
            VALUES (:symbol,:timeframe,:ts,:body_size,:upper_wick_ratio,:lower_wick_ratio,:volume_change,:gap_pct,:volatility_regime,:pre_expiry_flag,:post_expiry_flag,'{}'::jsonb)
            ON CONFLICT(symbol,timeframe,ts) DO UPDATE SET
              body_size=EXCLUDED.body_size,upper_wick_ratio=EXCLUDED.upper_wick_ratio,lower_wick_ratio=EXCLUDED.lower_wick_ratio,
              volume_change=EXCLUDED.volume_change,gap_pct=EXCLUDED.gap_pct,volatility_regime=EXCLUDED.volatility_regime,
              pre_expiry_flag=EXCLUDED.pre_expiry_flag,post_expiry_flag=EXCLUDED.post_expiry_flag
            """
        )
        for _, r in df.iterrows():
            db.execute(stmt, {**r.to_dict(), "symbol": symbol, "timeframe": timeframe})
