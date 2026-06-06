-- Mart: current leaderboard.
-- Takes the MOST RECENT snapshot of each product so Grafana can show
-- "top products right now" without seeing duplicate historical rows.

with ranked as (
    select
        *,
        row_number() over (
            partition by product_id
            order by snapshot_at desc
        ) as rn
    from {{ ref('stg_product_snapshots') }}
)

select
    product_id,
    product_name,
    tagline,
    votes_count,
    comments_count,
    topics,
    url,
    snapshot_at as last_seen_at
from ranked
where rn = 1
