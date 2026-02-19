import argparse
import os
from python.db import execute_sql

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="sql", help="SQL directory")
    ap.add_argument("--only", default=None, help="Run only a specific SQL file name (e.g., 00_schema.sql)")
    args = ap.parse_args()

    sql_dir = args.dir
    files = sorted([f for f in os.listdir(sql_dir) if f.endswith(".sql")])

    if args.only:
        files = [args.only]

    for f in files:
        path = os.path.join(sql_dir, f)
        sql = read_file(path)
        print(f"Running {path} ...")
        execute_sql(sql)

    print("SQL run complete.")

if __name__ == "__main__":
    main()
