#!/usr/bin/env bash
set -euo pipefail

# Run the full pipeline locally
# Usage: bash scripts/run_all.sh

python3 python/generate_data.py --out data/raw --days 365 --customers 5000 --seed 7
python3 python/run_sql.py --dir sql --only 00_schema.sql
python3 python/load_to_postgres.py --data-dir data/raw --truncate
python3 python/run_sql.py --dir sql
python3 python/dq_checks.py
python3 python/rfm_scoring.py
python3 python/clustering_kmeans.py
python3 python/cohorts.py
python3 python/viz_report.py --out bi/dashboard_screenshots

echo "Done. Check data/outputs and bi/dashboard_screenshots."
