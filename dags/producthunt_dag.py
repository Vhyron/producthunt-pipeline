"""
Runs every 30 minutes:
  1. extract_load  -> pull top posts from Product Hunt into raw.product_snapshots
  2. dbt_run       -> build staging + marts models on top of the raw data
  3. dbt_test      -> run dbt's data-quality tests
"""

import sys
import datetime as dt

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Make our /opt/airflow/extract module importable inside the container.
sys.path.append("/opt/airflow")
from extract.producthunt import extract_and_load  # noqa: E402

default_args = {
    "owner": "cognito",
    "retries": 2,
    "retry_delay": dt.timedelta(minutes=2),
}

with DAG(
    dag_id="producthunt_pipeline",
    description="Extract Product Hunt metrics -> TimescaleDB -> dbt models",
    start_date=dt.datetime(2024, 1, 1),
    schedule="*/30 * * * *",   # every 30 minutes (cron syntax)
    catchup=False,             # don't backfill old runs on first deploy
    max_active_runs=1,         # never overlap runs
    default_args=default_args,
    tags=["producthunt", "elt"],
) as dag:

    extract_load = PythonOperator(
        task_id="extract_load",
        python_callable=extract_and_load,
        op_kwargs={"first": 20},
    )

    # dbt runs as a shell command. The dbt project is mounted at /opt/airflow/dbt.
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "cd /opt/airflow/dbt/producthunt && "
            "dbt run --profiles-dir . --target prod"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "cd /opt/airflow/dbt/producthunt && "
            "dbt test --profiles-dir . --target prod"
        ),
    )

    # Define order: extract -> transform -> test
    extract_load >> dbt_run >> dbt_test
