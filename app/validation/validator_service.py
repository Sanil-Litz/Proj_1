from __future__ import annotations

from app.core.config import get_settings
from app.models.schemas import CandleDirection, PredictionResponse, ValidationResponse

settings = get_settings()


class ValidatorService:
    def validate(self, prediction: PredictionResponse) -> ValidationResponse:
        reasons: list[str] = []
        adjusted = prediction.confidence_pct

        if not prediction.top_patterns:
            reasons.append("No statistically matched Indian pattern samples available")
            adjusted -= 15

        small_sample = [p for p in prediction.top_patterns if p.sample_size < 30]
        if small_sample:
            reasons.append("Pattern sample size too low for robust Indian-market inference")
            adjusted -= 10

        if prediction.expected_volatility > 0.03:
            reasons.append("Abnormal volatility regime detected")
            adjusted -= 8

        if prediction.direction == CandleDirection.neutral:
            reasons.append("Direction unresolved")
            adjusted -= 20

        if prediction.confidence_pct < settings.confidence_floor * 100:
            reasons.append("Initial confidence below configured floor")
            adjusted -= 10

        disagreement = abs(prediction.confidence_pct - adjusted) / 100
        if disagreement > settings.validator_disagreement_threshold:
            reasons.append("Validator disagreement threshold exceeded")

        adjusted = max(1.0, min(99.0, adjusted))
        approved = disagreement <= settings.validator_disagreement_threshold
        return ValidationResponse(
            approved=approved,
            adjusted_confidence_pct=round(adjusted, 2),
            reasons=reasons,
        )
