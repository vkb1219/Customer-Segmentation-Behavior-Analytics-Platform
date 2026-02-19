import os
import numpy as np
import pandas as pd
from python.db import fetch_df, execute_sql

OUT_DIR = "data/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

SEGMENT_RULES = [
    ("Champions", lambda r,f,m: r>=4 and f>=4 and m>=4),
    ("Loyal",     lambda r,f,m: r>=4 and f>=3 and m>=3),
    ("Big Spenders", lambda r,f,m: r>=3 and m>=4),
    ("New",       lambda r,f,m: r>=4 and f<=2),
    ("At Risk",   lambda r,f,m: r<=2 and (f>=3 or m>=3)),
    ("Hibernating", lambda r,f,m: r<=2 and f<=2 and m<=2),
]

def score_quintiles(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    # quintile bins (1..5). For recency, lower days is better (higher score).
    q = pd.qcut(series.rank(method="first"), 5, labels=[1,2,3,4,5])
    q = q.astype(int)
    return q if higher_is_better else (6 - q)

def build_scored_table():
    # Pull base RFM from SQL mart
    df = fetch_df("SELECT customer_id, recency_days, frequency_orders, monetary_value FROM retail.mart_rfm_base;")
    if df.empty:
        raise RuntimeError("mart_rfm_base is empty. Run SQL builds first.")

    df["r_score"] = score_quintiles(df["recency_days"], higher_is_better=False)  # lower recency_days => higher score
    df["f_score"] = score_quintiles(df["frequency_orders"], higher_is_better=True)
    df["m_score"] = score_quintiles(df["monetary_value"], higher_is_better=True)
    df["rfm_score"] = df["r_score"]*100 + df["f_score"]*10 + df["m_score"]

    # assign segment by simple rules
    def assign(row):
        for name, rule in SEGMENT_RULES:
            if rule(row.r_score, row.f_score, row.m_score):
                return name
        return "Needs Attention"

    df["segment"] = df.apply(assign, axis=1)

    # write to csv output
    df.to_csv(os.path.join(OUT_DIR, "rfm_segments.csv"), index=False)

    # upsert into SQL mart_rfm_scored
    execute_sql("TRUNCATE TABLE retail.mart_rfm_scored;")
    # Use fast copy via to_sql
    from python.db import get_engine
    eng = get_engine()
    df[["customer_id","r_score","f_score","m_score","rfm_score","segment"]].to_sql(
        "mart_rfm_scored", eng, schema="retail", if_exists="append", index=False, method="multi", chunksize=5000
    )
    print("Wrote RFM segments to SQL + CSV.")

if __name__ == "__main__":
    build_scored_table()
