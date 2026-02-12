CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS instrument_catalog (
    symbol TEXT PRIMARY KEY,
    exchange TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS market_events (
    event_date DATE NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    severity SMALLINT NOT NULL DEFAULT 1,
    PRIMARY KEY (event_date, event_type)
);

CREATE TABLE IF NOT EXISTS ohlcv (
    symbol TEXT NOT NULL REFERENCES instrument_catalog(symbol),
    timeframe TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    corporate_action_factor DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    is_expiry_day BOOLEAN NOT NULL DEFAULT FALSE,
    is_weekly_expiry BOOLEAN NOT NULL DEFAULT FALSE,
    is_monthly_expiry BOOLEAN NOT NULL DEFAULT FALSE,
    is_budget_day BOOLEAN NOT NULL DEFAULT FALSE,
    is_rbi_policy_day BOOLEAN NOT NULL DEFAULT FALSE,
    is_global_spillover_day BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (symbol, timeframe, ts)
);

SELECT create_hypertable('ohlcv', by_range('ts'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_tf_ts ON ohlcv (symbol, timeframe, ts DESC);

CREATE TABLE IF NOT EXISTS ohlcv_features (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    body_size DOUBLE PRECISION NOT NULL,
    upper_wick_ratio DOUBLE PRECISION NOT NULL,
    lower_wick_ratio DOUBLE PRECISION NOT NULL,
    volume_change DOUBLE PRECISION NOT NULL,
    gap_pct DOUBLE PRECISION NOT NULL,
    volatility_regime TEXT NOT NULL,
    pre_expiry_flag BOOLEAN NOT NULL DEFAULT FALSE,
    post_expiry_flag BOOLEAN NOT NULL DEFAULT FALSE,
    pattern_vector JSONB NOT NULL,
    PRIMARY KEY (symbol, timeframe, ts)
);

CREATE INDEX IF NOT EXISTS idx_features_symbol_tf_ts ON ohlcv_features (symbol, timeframe, ts DESC);
