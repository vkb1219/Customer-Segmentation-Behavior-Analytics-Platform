from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

# Example DAG (reference only). To run it, install Airflow and place this file in your dags/ folder.

with DAG(
    dag_id="customer_segmentation_daily",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={"retries": 1},
) as dag:

    generate = BashOperator(
        task_id="generate_synthetic_data",
        bash_command="python /path/to/repo/python/generate_data.py --out /path/to/repo/data/raw --days 365 --customers 5000 --seed 7"
    )

    load = BashOperator(
        task_id="load_to_postgres",
        bash_command="python /path/to/repo/python/load_to_postgres.py --data-dir /path/to/repo/data/raw --truncate"
    )

    sql_build = BashOperator(
        task_id="run_sql_transforms",
        bash_command="python /path/to/repo/python/run_sql.py --dir /path/to/repo/sql"
    )

    rfm = BashOperator(
        task_id="rfm_scoring",
        bash_command="python /path/to/repo/python/rfm_scoring.py"
    )

    cluster = BashOperator(
        task_id="kmeans_clustering",
        bash_command="python /path/to/repo/python/clustering_kmeans.py"
    )

    cohorts = BashOperator(
        task_id="cohort_retention",
        bash_command="python /path/to/repo/python/cohorts.py"
    )

    viz = BashOperator(
        task_id="viz_report",
        bash_command="python /path/to/repo/python/viz_report.py --out /path/to/repo/bi/dashboard_screenshots"
    )

    generate >> load >> sql_build >> [rfm, cluster, cohorts] >> viz
