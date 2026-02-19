import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt
from python.db import fetch_df

def savefig(path: str):
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bi/dashboard_screenshots", help="Output folder for PNGs")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    # 1) Revenue by segment
    seg = fetch_df("""
      SELECT segment, COUNT(*) AS customers, SUM(m.monetary_value) AS revenue_365d
      FROM retail.mart_rfm_scored s
      JOIN retail.mart_rfm_base m USING(customer_id)
      GROUP BY 1
      ORDER BY revenue_365d DESC;
    """)
    seg.plot(kind="bar", x="segment", y="revenue_365d", legend=False)
    plt.title("Revenue (Last 365 Days) by RFM Segment")
    plt.xlabel("Segment")
    plt.ylabel("Revenue")
    savefig(os.path.join(args.out, "01_revenue_by_segment.png"))

    # 2) Customer count by segment
    seg.plot(kind="bar", x="segment", y="customers", legend=False)
    plt.title("Customer Count by RFM Segment")
    plt.xlabel("Segment")
    plt.ylabel("Customers")
    savefig(os.path.join(args.out, "02_customers_by_segment.png"))

    # 3) Cohort retention curve (aggregate)
    coh = fetch_df("SELECT cohort_month, active_month, retention_rate FROM retail.mart_cohort_retention;")
    if not coh.empty:
        # compute months since cohort
        coh["cohort_month"] = pd.to_datetime(coh["cohort_month"])
        coh["active_month"] = pd.to_datetime(coh["active_month"])
        coh["month_index"] = ((coh["active_month"].dt.year - coh["cohort_month"].dt.year) * 12 +
                              (coh["active_month"].dt.month - coh["cohort_month"].dt.month))
        avg_curve = coh.groupby("month_index")["retention_rate"].mean().reset_index()
        plt.plot(avg_curve["month_index"], avg_curve["retention_rate"])
        plt.title("Average Cohort Retention Curve")
        plt.xlabel("Months Since First Purchase")
        plt.ylabel("Retention Rate")
        savefig(os.path.join(args.out, "03_avg_cohort_retention_curve.png"))

    # 4) Cluster profile table (as simple bar chart of total_revenue mean)
    cl = fetch_df("""
      SELECT cluster_id, AVG(total_revenue) AS avg_revenue, AVG(total_orders) AS avg_orders
      FROM retail.mart_customer_clusters
      GROUP BY 1
      ORDER BY 1;
    """)
    if not cl.empty:
        cl.plot(kind="bar", x="cluster_id", y="avg_revenue", legend=False)
        plt.title("Avg Revenue by Behavioral Cluster")
        plt.xlabel("Cluster")
        plt.ylabel("Avg Revenue")
        savefig(os.path.join(args.out, "04_avg_revenue_by_cluster.png"))

        cl.plot(kind="bar", x="cluster_id", y="avg_orders", legend=False)
        plt.title("Avg Orders by Behavioral Cluster")
        plt.xlabel("Cluster")
        plt.ylabel("Avg Orders")
        savefig(os.path.join(args.out, "05_avg_orders_by_cluster.png"))

    print(f"Saved dashboard screenshots to: {args.out}")

if __name__ == "__main__":
    main()
