#!/usr/bin/env bash
set -euo pipefail

# Run the full pipeline locally
# Usage: bash scripts/run_all.sh

python python/generate_data.py --out data/raw --days 365 --customers 5000 --seed 7
python python/run_sql.py --dir sql --only 00_schema.sql
python python/load_to_postgres.py --data-dir data/raw --truncate
python python/run_sql.py --dir sql
python python/dq_checks.py
python python/rfm_scoring.py
python python/clustering_kmeans.py
python python/cohorts.py
python python/viz_report.py --out bi/dashboard_screenshots

echo "Done. Check data/outputs and bi/dashboard_screenshots."
