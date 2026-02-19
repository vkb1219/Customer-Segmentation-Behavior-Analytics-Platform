-- 30_gold_customer_360.sql
-- Builds mart_customer_metrics

WITH orders_non_cancel AS (
  SELECT * FROM retail.v_orders_non_cancelled
),
orders_completed AS (
  SELECT * FROM retail.v_orders_completed
),
order_item_rollup AS (
  SELECT
    o.customer_id,
    AVG(items_per_order)::numeric(14,2) AS avg_basket_size
  FROM (
    SELECT
      oi.order_id,
      o.customer_id,
      SUM(oi.quantity) AS items_per_order
    FROM retail.v_order_items_clean oi
    JOIN orders_non_cancel o ON o.order_id = oi.order_id
    GROUP BY 1,2
  ) t
  GROUP BY 1
),
dominant_category AS (
  SELECT customer_id, category
  FROM (
    SELECT
      o.customer_id,
      p.category,
      SUM(oi.line_total) AS cat_revenue,
      ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY SUM(oi.line_total) DESC) AS rn
    FROM retail.v_order_items_clean oi
    JOIN orders_non_cancel o ON o.order_id = oi.order_id
    JOIN retail.dim_products p ON p.product_id = oi.product_id
    GROUP BY 1,2
  ) x
  WHERE rn = 1
),
returns AS (
  SELECT
    customer_id,
    SUM(CASE WHEN status='returned' THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*),0) AS returns_rate
  FROM orders_non_cancel
  GROUP BY 1
),
base AS (
  SELECT
    c.customer_id,
    MIN(o.order_date) AS first_purchase_date,
    MAX(o.order_date) AS last_purchase_date,
    COUNT(DISTINCT o.order_id)::int AS total_orders,
    SUM(CASE WHEN o.status='completed' THEN o.order_total ELSE 0 END)::numeric(14,2) AS total_revenue,
    AVG(CASE WHEN o.status='completed' THEN o.order_total END)::numeric(14,2) AS avg_order_value
  FROM retail.dim_customers c
  LEFT JOIN orders_non_cancel o ON o.customer_id = c.customer_id
  GROUP BY 1
),
freq AS (
  SELECT
    customer_id,
    (COUNT(DISTINCT order_id)::numeric / NULLIF(GREATEST(EXTRACT(MONTH FROM AGE(MAX(order_date), MIN(order_date))), 1),1))::numeric(14,4)
      AS purchase_frequency_per_mo
  FROM orders_non_cancel
  GROUP BY 1
)
INSERT INTO retail.mart_customer_metrics
(
  customer_id, first_purchase_date, last_purchase_date, total_orders, total_revenue,
  avg_order_value, avg_basket_size, purchase_frequency_per_mo, days_since_last_purchase,
  returns_rate, dominant_category
)
SELECT
  b.customer_id,
  b.first_purchase_date,
  b.last_purchase_date,
  COALESCE(b.total_orders,0),
  COALESCE(b.total_revenue,0),
  COALESCE(b.avg_order_value,0),
  COALESCE(oir.avg_basket_size,0),
  COALESCE(f.purchase_frequency_per_mo,0),
  CASE WHEN b.last_purchase_date IS NULL THEN NULL
       ELSE (CURRENT_DATE - b.last_purchase_date)::int END AS days_since_last_purchase,
  COALESCE(r.returns_rate,0),
  dc.category
FROM base b
LEFT JOIN order_item_rollup oir ON oir.customer_id = b.customer_id
LEFT JOIN freq f ON f.customer_id = b.customer_id
LEFT JOIN returns r ON r.customer_id = b.customer_id
LEFT JOIN dominant_category dc ON dc.customer_id = b.customer_id
ON CONFLICT (customer_id) DO UPDATE
SET first_purchase_date=EXCLUDED.first_purchase_date,
    last_purchase_date=EXCLUDED.last_purchase_date,
    total_orders=EXCLUDED.total_orders,
    total_revenue=EXCLUDED.total_revenue,
    avg_order_value=EXCLUDED.avg_order_value,
    avg_basket_size=EXCLUDED.avg_basket_size,
    purchase_frequency_per_mo=EXCLUDED.purchase_frequency_per_mo,
    days_since_last_purchase=EXCLUDED.days_since_last_purchase,
    returns_rate=EXCLUDED.returns_rate,
    dominant_category=EXCLUDED.dominant_category;
