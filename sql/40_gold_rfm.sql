-- 40_gold_rfm.sql
-- Builds mart_rfm_base using last 365 days of COMPLETED orders.

WITH completed AS (
  SELECT *
  FROM retail.v_orders_completed
  WHERE order_date >= (CURRENT_DATE - INTERVAL '365 days')
),
agg AS (
  SELECT
    customer_id,
    (CURRENT_DATE - MAX(order_date))::int AS recency_days,
    COUNT(DISTINCT order_id)::int AS frequency_orders,
    SUM(order_total)::numeric(14,2) AS monetary_value
  FROM completed
  GROUP BY 1
)
INSERT INTO retail.mart_rfm_base (customer_id, recency_days, frequency_orders, monetary_value)
SELECT customer_id, recency_days, frequency_orders, monetary_value
FROM agg
ON CONFLICT (customer_id) DO UPDATE
SET recency_days=EXCLUDED.recency_days,
    frequency_orders=EXCLUDED.frequency_orders,
    monetary_value=EXCLUDED.monetary_value;
