"""
Talks to the Product Hunt GraphQL API v2, pulls the current top posts,
and writes one snapshot row per product into raw.product_snapshots.

Designed to be called either:
  - directly:  python extract/producthunt.py   (for local testing)
  - from Airflow: import extract_and_load and call it in a task
"""

import os
import json
import datetime as dt
from typing import Any

import requests
import psycopg2
from psycopg2.extras import execute_values

PH_API_URL = "https://api.producthunt.com/v2/api/graphql"

QUERY = """
query TopPosts($first: Int!) {
  posts(order: VOTES, first: $first) {
    edges {
      node {
        id
        name
        tagline
        description
        votesCount
        commentsCount
        featuredAt
        url
        topics(first: 5) {
          edges { node { name } }
        }
      }
    }
  }
}
"""


def fetch_posts(first: int = 20) -> list[dict[str, Any]]:
    """Call the Product Hunt API and return a list of post nodes."""
    token = os.environ["PRODUCTHUNT_API_TOKEN"]  # set via .env / Airflow connection
    resp = requests.post(
        PH_API_URL,
        json={"query": QUERY, "variables": {"first": first}},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()

    if "errors" in payload:
        raise RuntimeError(f"Product Hunt API error: {payload['errors']}")

    edges = payload["data"]["posts"]["edges"]
    return [edge["node"] for edge in edges]


def transform(node: dict[str, Any], snapshot_at: dt.datetime) -> tuple:
    """Flatten one API node into a row tuple matching raw.product_snapshots."""
    topics = ", ".join(
        t["node"]["name"] for t in node.get("topics", {}).get("edges", [])
    )
    return (
        snapshot_at,
        node["id"],
        node.get("name"),
        node.get("tagline"),
        node.get("description"),
        node.get("votesCount"),
        node.get("commentsCount"),
        topics,
        node.get("featuredAt"),
        node.get("url"),
        json.dumps(node),  # keep the full payload in the JSONB column
    )


def load(rows: list[tuple]) -> int:
    """Bulk-insert snapshot rows into Postgres/TimescaleDB."""
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "timescaledb"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "producthunt"),
        user=os.environ.get("DB_USER", "producthunt_user"),
        password=os.environ["DB_PASSWORD"],
    )
    try:
        with conn, conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO raw.product_snapshots
                    (snapshot_at, product_id, name, tagline, description,
                     votes_count, comments_count, topics, featured_at, url, raw_payload)
                VALUES %s
                ON CONFLICT (product_id, snapshot_at) DO NOTHING
                """,
                rows,
            )
        return len(rows)
    finally:
        conn.close()


def extract_and_load(first: int = 20) -> int:
    """End-to-end: fetch -> transform -> load. Returns rows loaded."""
    snapshot_at = dt.datetime.now(dt.timezone.utc)
    nodes = fetch_posts(first=first)
    rows = [transform(n, snapshot_at) for n in nodes]
    count = load(rows)
    print(f"[{snapshot_at.isoformat()}] loaded {count} product snapshots")
    return count


if __name__ == "__main__":
    # Local test entrypoint. Requires env vars set (see .env.example).
    extract_and_load()
