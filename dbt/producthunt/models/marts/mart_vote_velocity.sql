-- Mart: vote velocity.
-- For each product, compute how many votes it gained between consecutive
-- snapshots, and the rate per hour. This powers the "trending / momentum"
-- time-series charts in Grafana.

with snapshots as (
    select
        product_id,
        product_name,
        snapshot_at,
        votes_count
    from {{ ref('stg_product_snapshots') }}
),

with_lag as (
    select
        *,
        lag(votes_count) over (
            partition by product_id order by snapshot_at
        ) as prev_votes,
        lag(snapshot_at) over (
            partition by product_id order by snapshot_at
        ) as prev_snapshot_at
    from snapshots
)

select
    product_id,
    product_name,
    snapshot_at,
    votes_count,
    votes_count - prev_votes as votes_gained,
    -- votes gained per hour between the two snapshots
    case
        when prev_snapshot_at is not null
             and snapshot_at > prev_snapshot_at
        then (votes_count - prev_votes)::numeric
             / (extract(epoch from (snapshot_at - prev_snapshot_at)) / 3600.0)
        else null
    end as votes_per_hour
from with_lag
where prev_votes is not null
