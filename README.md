# Product Hunt Data Pipeline

A pipeline that extracts metrics from
Product Hunt, loads them into TimescaleDB, transforms them with dbt, and
visualizes them live in Grafana — orchestrated by Airflow.

```
Product Hunt API
   │  (GraphQL)
   ▼
[ Airflow ]  ── extract_load ──►  raw.product_snapshots   (TimescaleDB)
   │
   ├── dbt run ──►  staging (views)  ──►  marts (tables)
   │                                        ├─ mart_current_leaderboard
   │                                        └─ mart_vote_velocity
   ▼
[ Grafana ]  ── live dashboard (30s refresh)
```

## Stack
| Layer        | Tool                         |
|--------------|------------------------------|
| Extract      | Python + Product Hunt GraphQL |
| Orchestrate  | Apache Airflow (LocalExecutor) |
| Storage      | TimescaleDB (Postgres + time-series) |
| Transform    | dbt (staging → marts)        |
| Visualize    | Grafana                      |
| Runtime      | Docker Compose (OrbStack on Mac) |

## Prerequisites
- OrbStack (or Docker Desktop) running
- A Product Hunt API developer token

## Quick start
```bash
# 1. Configure secrets
cp .env.example .env
#    then edit .env with your PH token + a DB password

# 2. Build & launch the whole stack
docker compose up -d --build

# 3. Open the UIs
#    Airflow : http://localhost:8080   (admin / admin)
#    Grafana : http://localhost:3000   (admin / admin)

# 4. In Airflow, unpause the `producthunt_pipeline` DAG (toggle top-left).
#    It runs every 30 min; click ▶ to trigger a first run immediately.

# 5. Watch data land in Grafana → "Product Hunt Live Monitor" dashboard.
```

## Useful commands
```bash
docker compose up -d                       # start everything
docker compose logs -f airflow-scheduler   # watch the scheduler
docker compose logs -f                     # all services
docker compose down                        # stop (data persists)
docker compose down -v                     # stop + wipe all data
```

## Test the extractor alone (optional)
```bash
docker compose exec airflow-scheduler \
  python /opt/airflow/extract/producthunt.py
```
