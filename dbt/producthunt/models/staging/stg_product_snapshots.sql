-- Staging: light cleanup of the raw landing table.
-- One row per (product, snapshot). We standardize names and drop the
-- heavy JSONB payload from downstream use.

with source as (
    select * from {{ source('raw', 'product_snapshots') }}
)

select
    product_id,
    snapshot_at,
    name                          as product_name,
    tagline,
    coalesce(votes_count, 0)      as votes_count,
    coalesce(comments_count, 0)   as comments_count,
    topics,
    featured_at,
    url
from source
