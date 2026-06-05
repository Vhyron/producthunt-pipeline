CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE IF NOT EXISTS raw.product_snapshots (
    snapshot_at    TIMESTAMPTZ NOT NULL,
    product_id     TEXT        NOT NULL,
    name           TEXT,
    tagline        TEXT,
    description    TEXT,
    votes_count    INTEGER,
    comments_count INTEGER,
    topics         TEXT,
    featured_at    TIMESTAMPTZ,
    url            TEXT,
    raw_payload    JSONB,
    PRIMARY KEY (product_id, snapshot_at)
);

-- TimescaleDB hypertable, partitioned by time.
-- Makes time-bucketed queries (per-hour, per-day) fast and efficient.
SELECT create_hypertable(
    'raw.product_snapshots',
    'snapshot_at',
    if_not_exists => TRUE
);

-- Helpful index for "show me this product's history" lookups.
CREATE INDEX IF NOT EXISTS idx_product_snapshots_product
    ON raw.product_snapshots (product_id, snapshot_at DESC);
