import os
import pandas as pd
from python.db import fetch_df, get_engine

OUT_DIR = "data/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

def main():
    # cohort = month of first completed purchase
    q = """
    WITH first_purchase AS (
      SELECT customer_id, DATE_TRUNC('month', MIN(order_date))::date AS cohort_month
      FROM retail.fact_orders
      WHERE status='completed'
      GROUP BY 1
    ),
    activity AS (
      SELECT o.customer_id,
             DATE_TRUNC('month', o.order_date)::date AS active_month
      FROM retail.fact_orders o
      WHERE o.status='completed'
      GROUP BY 1,2
    ),
    joined AS (
      SELECT fp.cohort_month, a.active_month, a.customer_id
      FROM first_purchase fp
      JOIN activity a ON a.customer_id = fp.customer_id
    ),
    cohort_size AS (
      SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
      FROM first_purchase
      GROUP BY 1
    )
    SELECT
      j.cohort_month,
      j.active_month,
      cs.cohort_size,
      COUNT(DISTINCT j.customer_id) AS active_users,
      (COUNT(DISTINCT j.customer_id)::numeric / NULLIF(cs.cohort_size,0))::numeric(10,4) AS retention_rate
    FROM joined j
    JOIN cohort_size cs ON cs.cohort_month = j.cohort_month
    GROUP BY 1,2,3
    ORDER BY 1,2;
    """
    df = fetch_df(q)
    df.to_csv(os.path.join(OUT_DIR, "cohort_retention.csv"), index=False)

    # persist to DB mart
    eng = get_engine()
    with eng.begin() as conn:
        conn.exec_driver_sql("TRUNCATE TABLE retail.mart_cohort_retention;")
    df.to_sql("mart_cohort_retention", eng, schema="retail", if_exists="append", index=False, method="multi", chunksize=5000)

    print("Cohort retention exported to SQL + CSV.")

if __name__ == "__main__":
    main()
