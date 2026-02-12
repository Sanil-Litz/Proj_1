# Deployment & Reliability Architecture

## Runtime topology

1. **TimescaleDB (PostgreSQL 16)**
   - Stores normalized OHLCV and precomputed feature tables.
   - Hypertables + symbol/timeframe indexes for low-latency historical reads.
2. **FastAPI inference service**
   - Exposes `/predict`, `/validate_prediction`, `/history/{symbol}`.
   - Serves Indian market inference with contextual confidence adjustments.
3. **Scheduler/ingestion worker**
   - Runs periodic backfills during and around Indian market sessions.
   - Can be deployed as a separate process using `app.services.scheduler`.
4. **TradingView bridge**
   - Pine indicator consumes confidence + direction from webhook integration.

## Failure recovery

- Ingestion endpoints are idempotent using upserts on `(symbol,timeframe,ts)`.
- API can restart without data loss; state persists in TimescaleDB volumes.
- Model can retrain on-demand from stored features; no hidden in-memory-only dependency.

## Logging

- Structured JSON logs via `python-json-logger`.
- Container-native stdout logs compatible with ELK/CloudWatch/Loki.

## API endpoint summary

- `POST /predict`
- `POST /validate_prediction`
- `GET /history/{symbol}`
- `POST /ingest/backfill`
- `POST /ingest/live_tick`

## Indian-market conventions implemented

- Instruments limited to Indian indices/equities/MCX gold/BTCINR.
- Expiry day tagging (weekly/monthly Thursday logic).
- Candlestick and regime features include expiry-context flags.
- Hooks prepared for budget-day, RBI-day, and spillover event marking.
