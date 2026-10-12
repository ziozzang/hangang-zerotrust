-- Design example only. Configure database roles, encryption, TTL and queries
-- before deployment. ReplacingMergeTree merges are not an exactly-once guarantee.
CREATE TABLE zerotrust_events
(
    event_id UUID,
    occurred_at DateTime64(3, 'UTC'),
    observed_at DateTime64(3, 'UTC'),
    schema_version LowCardinality(String),
    component LowCardinality(String),
    instance_id String,
    event_type LowCardinality(String),
    outcome LowCardinality(String),
    reason_code LowCardinality(String),
    resource_id String,
    action LowCardinality(String),
    request_id String,
    authority_epoch String,
    catalog_revision UInt64,
    policy_revision UInt64,
    latency_us UInt64
)
ENGINE = ReplacingMergeTree(observed_at)
PARTITION BY toYYYYMM(occurred_at)
ORDER BY (component, occurred_at, event_id)
TTL occurred_at + INTERVAL 30 DAY;

-- Select/deduplicate on stable event identity when using retry-derived records.
-- Do not infer exact authorization/audit totals from an undeduplicated view.
