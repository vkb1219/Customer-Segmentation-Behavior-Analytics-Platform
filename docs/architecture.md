# Architecture (Local Reference)

**Bronze**
- Raw CSVs generated via `python/generate_data.py`
- Loaded into Postgres: `raw_customers`, `raw_products`, `raw_orders`, `raw_order_items`

**Silver**
- Cleaned tables: cast types, handle returns/cancellations, dedupe

**Gold**
- `mart_customer_metrics`: customer 360 KPIs
- `mart_rfm_base`: recency/frequency/monetary base measures
- `mart_rfm_scored`: quintile scoring + segment labels
- `mart_cohort_retention`: monthly cohort retention

**Python Analytics**
- RFM scoring verification + export
- KMeans clustering on behavioral features
- Cohort retention export
- Visualization report PNGs

**Orchestration**
- `pipelines/airflow_dag_customer_segmentation.py` shows a daily job pattern
