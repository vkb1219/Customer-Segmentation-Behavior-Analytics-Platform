import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from python.db import fetch_df, get_engine

OUT_DIR = "data/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

def load_features():
    q = """
    SELECT
      customer_id,
      COALESCE(total_orders,0) AS total_orders,
      COALESCE(total_revenue,0) AS total_revenue,
      COALESCE(avg_order_value,0) AS avg_order_value,
      COALESCE(avg_basket_size,0) AS avg_basket_size,
      COALESCE(purchase_frequency_per_mo,0) AS purchase_frequency_per_mo,
      COALESCE(days_since_last_purchase,9999) AS days_since_last_purchase,
      COALESCE(returns_rate,0) AS returns_rate
    FROM retail.mart_customer_metrics;
    """
    df = fetch_df(q)
    if df.empty:
        raise RuntimeError("mart_customer_metrics is empty. Run SQL builds first.")
    return df

def choose_k(X, k_min=3, k_max=8):
    best = None
    for k in range(k_min, k_max+1):
        km = KMeans(n_clusters=k, random_state=42, n_init="auto")
        labels = km.fit_predict(X)
        s = silhouette_score(X, labels)
        if best is None or s > best[0]:
            best = (s, k)
    return best[1], best[0]

def main():
    df = load_features()
    features = ["total_orders","total_revenue","avg_order_value","avg_basket_size",
                "purchase_frequency_per_mo","days_since_last_purchase","returns_rate"]
    X = df[features].to_numpy()

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    k, sil = choose_k(Xs)
    km = KMeans(n_clusters=k, random_state=42, n_init="auto")
    df["cluster_id"] = km.fit_predict(Xs).astype(int)
    df.to_csv(os.path.join(OUT_DIR, "customer_clusters.csv"), index=False)

    # persist to DB
    eng = get_engine()
    with eng.begin() as conn:
        conn.exec_driver_sql("DROP TABLE IF EXISTS retail.mart_customer_clusters;")
        conn.exec_driver_sql("""
            CREATE TABLE retail.mart_customer_clusters (
              customer_id INT PRIMARY KEY,
              cluster_id INT,
              total_orders INT,
              total_revenue NUMERIC(14,2),
              avg_order_value NUMERIC(14,2),
              avg_basket_size NUMERIC(14,2),
              purchase_frequency_per_mo NUMERIC(14,4),
              days_since_last_purchase INT,
              returns_rate NUMERIC(10,4)
            );
        """)
    df.rename(columns={"total_orders":"total_orders"}, inplace=True)
    df.to_sql("mart_customer_clusters", eng, schema="retail", if_exists="append", index=False, method="multi", chunksize=5000)

    # cluster profile summary
    prof = df.groupby("cluster_id")[features].mean().round(2).reset_index()
    prof.to_csv(os.path.join(OUT_DIR, "cluster_profiles.csv"), index=False)

    print(f"Clustering complete. k={k}, silhouette={sil:.3f}")
    print(prof)

if __name__ == "__main__":
    main()
