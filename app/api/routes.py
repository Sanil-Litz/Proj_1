from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.ingestion.providers import EmptyProvider
from app.models.schemas import (
    BackfillRequest,
    PredictionRequest,
    PredictionResponse,
    ValidationRequest,
    ValidationResponse,
)
from app.services.ingestion_service import IngestionService
from app.services.prediction_service import PredictionService
from app.validation.validator_service import ValidatorService

router = APIRouter()
prediction_service = PredictionService()
validator_service = ValidatorService()
ingestion_service = IngestionService(provider=EmptyProvider())


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/ingest/backfill")
def backfill(req: BackfillRequest, db: Session = Depends(get_db)) -> dict:
    rows = ingestion_service.backfill(db, req.symbol, req.timeframe, req.years)
    return {"ingested_rows": rows}


@router.post("/ingest/live_tick")
def live_tick(payload: dict, db: Session = Depends(get_db)) -> dict:
    ingestion_service.ingest_live_tick(db, payload)
    return {"ok": True}


@router.get("/history/{symbol}")
def history(symbol: str, timeframe: str, limit: int = 200, db: Session = Depends(get_db)) -> list[dict]:
    stmt = text(
        """
        SELECT o.ts,o.open,o.high,o.low,o.close,o.volume,f.body_size,f.upper_wick_ratio,f.lower_wick_ratio,f.gap_pct,f.volatility_regime
        FROM ohlcv o JOIN ohlcv_features f
        ON o.symbol=f.symbol AND o.timeframe=f.timeframe AND o.ts=f.ts
        WHERE o.symbol=:symbol AND o.timeframe=:timeframe
        ORDER BY o.ts DESC LIMIT :limit
        """
    )
    rows = db.execute(stmt, {"symbol": symbol, "timeframe": timeframe, "limit": limit}).mappings().all()
    return [dict(r) for r in rows]


@router.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest, db: Session = Depends(get_db)) -> PredictionResponse:
    stmt = text(
        """
        SELECT o.ts,o.open,o.high,o.low,o.close,o.volume,o.is_expiry_day,o.is_budget_day,o.is_rbi_policy_day,
               f.body_size,f.upper_wick_ratio,f.lower_wick_ratio,f.volume_change,f.gap_pct
        FROM ohlcv o JOIN ohlcv_features f
        ON o.symbol=f.symbol AND o.timeframe=f.timeframe AND o.ts=f.ts
        WHERE o.symbol=:symbol AND o.timeframe=:timeframe AND o.ts<=:as_of
        ORDER BY o.ts DESC LIMIT 1000
        """
    )
    rows = db.execute(
        stmt,
        {"symbol": req.symbol, "timeframe": req.timeframe, "as_of": req.as_of},
    ).mappings().all()
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("ts")
    return prediction_service.predict(req.symbol, req.timeframe, req.as_of, df)


@router.post("/validate_prediction", response_model=ValidationResponse)
def validate_prediction(req: ValidationRequest) -> ValidationResponse:
    return validator_service.validate(req.prediction)
