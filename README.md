# Indian Market Next-Candle Prediction Platform

Production-oriented, Indian-market-only trend prediction stack for NSE/BSE/MCX instruments.

## Core capabilities

- Historical + live ingestion for Indian market symbols across 1m/5m/15m/1h/1d.
- TimescaleDB-backed OHLCV store with precomputed candle, regime, expiry-context, and event-context features.
- Statistical pattern engine that estimates `P(next bullish)` and `P(next bearish)` from historical Indian occurrences.
- Context engine combining higher timeframe trend, volatility regime, volume state, consolidation/expansion, and Indian event-day flags.
- Prediction engine with direction, confidence, expected volatility, and expected candle-size range.
- Self-checking validator API (`/validate_prediction`) that downgrades confidence on conflicts/regime mismatches.
- TradingView Pine Script integration with arrows, confidence meter, labels, and optional alerts.
- Dockerized deployment, scheduler, structured logging, and recovery-safe ingestion checkpoints.

## Repository layout

- `app/` – FastAPI service, feature/prediction engines, ingestion, DB layer.
- `sql/` – schema and indexes.
- `tradingview/` – Pine Script indicator template for Indian symbols.
- `infra/` – Docker Compose and production env template.
- `tests/` – unit and API tests.

## Quick start

1. Copy env file and configure secrets/data-provider keys:
   ```bash
   cp infra/.env.example .env
   ```
2. Launch database + API + scheduler:
   ```bash
   docker compose -f infra/docker-compose.yml up --build
   ```
3. Run migrations:
   ```bash
   docker compose -f infra/docker-compose.yml exec api python -m app.db.migrate
   ```
4. Validate health:
   ```bash
   curl http://localhost:8000/health
   ```

## API

- `POST /predict` – next-candle prediction.
- `POST /validate_prediction` – independent confidence verification.
- `GET /history/{symbol}` – historical OHLCV + computed features.
- `POST /ingest/backfill` – backfill historical data.
- `POST /ingest/live_tick` – live tick ingestion path.

## Important operational notes

- Trading calendar aligns to Indian exchanges and excludes exchange holidays.
- Expiry metadata supports weekly/monthly derivatives expiries.
- Corporate actions are adjusted via provider metadata in the normalization layer.
- Budget day, RBI policy day, and global spillover events are modeled as contextual flags.
