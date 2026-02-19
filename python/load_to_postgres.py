import argparse
import os
import pandas as pd
from sqlalchemy import text
from python.db import get_engine

RAW_TABLES = {
    "customers.csv": "retail.raw_customers",
    "products.csv": "retail.raw_products",
    "orders.csv": "retail.raw_orders",
    "order_items.csv": "retail.raw_order_items",
}

def ensure_schema(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS retail;"))

def truncate_raw(engine):
    with engine.begin() as conn:
        for tbl in RAW_TABLES.values():
            conn.execute(text(f"TRUNCATE TABLE {tbl};"))

def load_csv(engine, csv_path: str, table: str):
    df = pd.read_csv(csv_path)
    # ensure date parsing
    for col in ["signup_date", "order_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.date
    df.to_sql(table.split(".")[1], engine, schema=table.split(".")[0], if_exists="append", index=False, method="multi", chunksize=5000)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data/raw", help="Folder containing raw CSVs")
    ap.add_argument("--truncate", action="store_true", help="Truncate raw tables before loading")
    args = ap.parse_args()

    engine = get_engine()
    ensure_schema(engine)

    # Ensure tables exist (schema SQL will also create them, but we do it defensively)
    # If tables are missing, run: python python/run_sql.py --dir sql --only 00_schema.sql
    if args.truncate:
        truncate_raw(engine)

    for fname, table in RAW_TABLES.items():
        path = os.path.join(args.data_dir, fname)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing {path}. Run generate_data.py first.")
        print(f"Loading {path} -> {table}")
        load_csv(engine, path, table)

    print("Load complete.")

if __name__ == "__main__":
    main()
