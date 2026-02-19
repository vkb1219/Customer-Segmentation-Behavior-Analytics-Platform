-- 10_bronze_load_views.sql
-- Upserts raw -> dimensions/facts (lightweight approach for synthetic CSV loads)

-- Dimensions
INSERT INTO retail.dim_customers (customer_id, signup_date, country, channel, email_domain, is_active)
SELECT DISTINCT customer_id, signup_date, country, channel, email_domain, is_active
FROM retail.raw_customers
ON CONFLICT (customer_id) DO UPDATE
SET signup_date=EXCLUDED.signup_date,
    country=EXCLUDED.country,
    channel=EXCLUDED.channel,
    email_domain=EXCLUDED.email_domain,
    is_active=EXCLUDED.is_active;

INSERT INTO retail.dim_products (product_id, category, brand, unit_cost)
SELECT DISTINCT product_id, category, brand, unit_cost
FROM retail.raw_products
ON CONFLICT (product_id) DO UPDATE
SET category=EXCLUDED.category,
    brand=EXCLUDED.brand,
    unit_cost=EXCLUDED.unit_cost;

-- Date dimension: generate from raw order dates
INSERT INTO retail.dim_date (date_key, year, month, day, week, day_name, month_name)
SELECT d::date AS date_key,
       EXTRACT(YEAR FROM d)::int AS year,
       EXTRACT(MONTH FROM d)::int AS month,
       EXTRACT(DAY FROM d)::int AS day,
       EXTRACT(WEEK FROM d)::int AS week,
       TO_CHAR(d, 'Day') AS day_name,
       TO_CHAR(d, 'Month') AS month_name
FROM (
  SELECT DISTINCT order_date::date AS d FROM retail.raw_orders
) x
ON CONFLICT (date_key) DO NOTHING;

-- Facts
INSERT INTO retail.fact_orders (order_id, customer_id, order_date, status, payment_type, order_total, discount_total, shipping_total)
SELECT order_id, customer_id, order_date, status, payment_type, order_total, discount_total, shipping_total
FROM retail.raw_orders
ON CONFLICT (order_id) DO UPDATE
SET customer_id=EXCLUDED.customer_id,
    order_date=EXCLUDED.order_date,
    status=EXCLUDED.status,
    payment_type=EXCLUDED.payment_type,
    order_total=EXCLUDED.order_total,
    discount_total=EXCLUDED.discount_total,
    shipping_total=EXCLUDED.shipping_total;

INSERT INTO retail.fact_order_items (order_item_id, order_id, product_id, quantity, unit_price, line_total)
SELECT order_item_id, order_id, product_id, quantity, unit_price, line_total
FROM retail.raw_order_items
ON CONFLICT (order_item_id) DO UPDATE
SET order_id=EXCLUDED.order_id,
    product_id=EXCLUDED.product_id,
    quantity=EXCLUDED.quantity,
    unit_price=EXCLUDED.unit_price,
    line_total=EXCLUDED.line_total;
