-- 20_silver_clean.sql
-- Basic cleaning logic applied in queries that feed the gold marts.

-- For analytics, we typically exclude cancelled orders, but keep returned for returns-rate calculations.
-- Create helper views for clean order set.
CREATE OR REPLACE VIEW retail.v_orders_completed AS
SELECT *
FROM retail.fact_orders
WHERE status = 'completed';

CREATE OR REPLACE VIEW retail.v_orders_non_cancelled AS
SELECT *
FROM retail.fact_orders
WHERE status IN ('completed','returned');

CREATE OR REPLACE VIEW retail.v_order_items_clean AS
SELECT oi.*
FROM retail.fact_order_items oi
JOIN retail.fact_orders o ON o.order_id = oi.order_id
WHERE o.status IN ('completed','returned')
  AND oi.quantity > 0
  AND oi.unit_price >= 0;
