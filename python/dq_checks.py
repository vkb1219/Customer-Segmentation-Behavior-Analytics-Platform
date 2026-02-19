import pandas as pd
from python.db import fetch_df

def run_dq_checks():
    """
    Lightweight data quality checks you can mention in interviews.
    """
    checks = []

    # 1) No negative revenue for completed orders
    q1 = """
    SELECT COUNT(*) AS bad_rows
    FROM retail.fact_orders
    WHERE status='completed' AND order_total < 0;
    """
    bad1 = int(fetch_df(q1).iloc[0]["bad_rows"])
    checks.append(("no_negative_revenue_completed", bad1 == 0, bad1))

    # 2) Order items should have positive quantity
    q2 = """
    SELECT COUNT(*) AS bad_rows
    FROM retail.fact_order_items
    WHERE quantity <= 0;
    """
    bad2 = int(fetch_df(q2).iloc[0]["bad_rows"])
    checks.append(("positive_quantity_items", bad2 == 0, bad2))

    # 3) Orphan order items
    q3 = """
    SELECT COUNT(*) AS bad_rows
    FROM retail.fact_order_items oi
    LEFT JOIN retail.fact_orders o ON o.order_id = oi.order_id
    WHERE o.order_id IS NULL;
    """
    bad3 = int(fetch_df(q3).iloc[0]["bad_rows"])
    checks.append(("no_orphan_order_items", bad3 == 0, bad3))

    return pd.DataFrame(checks, columns=["check", "passed", "bad_rows"])

if __name__ == "__main__":
    df = run_dq_checks()
    print(df.to_string(index=False))
