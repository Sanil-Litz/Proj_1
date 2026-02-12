from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from xgboost import XGBClassifier

from app.features.context_engine import build_context
from app.features.pattern_engine import detect_patterns, pattern_probabilities
from app.models.schemas import CandleDirection, PredictionResponse


@dataclass
class ModelArtifacts:
    clf: XGBClassifier
    nbrs: NearestNeighbors
    feature_matrix: np.ndarray
    ids: list[str]


class PredictionService:
    def __init__(self) -> None:
        self.artifacts: ModelArtifacts | None = None

    def train(self, df: pd.DataFrame) -> None:
        if df.shape[0] < 300:
            self.artifacts = None
            return

        feat_cols = ["body_size", "upper_wick_ratio", "lower_wick_ratio", "volume_change", "gap_pct"]
        train_df = df.dropna(subset=feat_cols + ["close"]).copy()
        x = train_df[feat_cols].to_numpy()
        y = (train_df["close"].shift(-1) > train_df["close"]).astype(int).fillna(0).to_numpy()

        clf = XGBClassifier(
            n_estimators=150,
            max_depth=4,
            learning_rate=0.06,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
        )
        clf.fit(x, y)

        nbrs = NearestNeighbors(n_neighbors=10, metric="euclidean")
        nbrs.fit(x)

        ids = [f"case_{i}" for i in range(train_df.shape[0])]
        self.artifacts = ModelArtifacts(clf=clf, nbrs=nbrs, feature_matrix=x, ids=ids)

    def predict(self, symbol: str, timeframe: str, as_of, df: pd.DataFrame) -> PredictionResponse:
        if self.artifacts is None:
            self.train(df)

        d = detect_patterns(df)
        probs = pattern_probabilities(d)
        ctx = build_context(d)

        latest = d.iloc[-1]
        x_latest = np.array(
            [[latest["body_size"], latest["upper_wick_ratio"], latest["lower_wick_ratio"], latest["volume_change"], latest["gap_pct"]]]
        )

        if self.artifacts is None:
            bull_prob = 0.5
            analog_ids = []
        else:
            bull_prob = float(self.artifacts.clf.predict_proba(x_latest)[0][1])
            _, idx = self.artifacts.nbrs.kneighbors(x_latest)
            analog_ids = [self.artifacts.ids[i] for i in idx[0].tolist()]

        context_adjust = 0.0
        if ctx.get("phase") == "expiry_driven":
            context_adjust -= 0.05
        if ctx.get("budget_context") or ctx.get("rbi_context"):
            context_adjust -= 0.08
        if ctx.get("volatility_cluster") == "high":
            context_adjust -= 0.04

        adjusted_bull = min(max(bull_prob + context_adjust, 0.01), 0.99)
        direction = CandleDirection.bullish if adjusted_bull >= 0.5 else CandleDirection.bearish
        confidence = abs(adjusted_bull - 0.5) * 200

        returns = d["close"].pct_change().dropna().tail(50)
        expected_vol = float(returns.std()) if not returns.empty else 0.0
        body_dist = d["body_size"].tail(100)
        low, high = float(body_dist.quantile(0.25)), float(body_dist.quantile(0.75))

        return PredictionResponse(
            symbol=symbol,
            timeframe=timeframe,
            as_of=as_of,
            direction=direction,
            confidence_pct=round(confidence, 2),
            expected_volatility=round(expected_vol, 6),
            expected_candle_size_low=round(low, 6),
            expected_candle_size_high=round(high, 6),
            top_patterns=probs,
            analog_case_ids=analog_ids,
        )
