-- 00_schema.sql
-- Creates schema, raw tables, and star schema tables.

CREATE SCHEMA IF NOT EXISTS retail;

-- Bronze (raw)
CREATE TABLE IF NOT EXISTS retail.raw_customers (
  customer_id       INT,
  signup_date       DATE,
  country           TEXT,
  channel           TEXT,
  email_domain      TEXT,
  is_active         BOOLEAN
);

CREATE TABLE IF NOT EXISTS retail.raw_products (
  product_id        INT,
  category          TEXT,
  brand             TEXT,
  unit_cost         NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS retail.raw_orders (
  order_id          BIGINT,
  customer_id       INT,
  order_date        DATE,
  status            TEXT,
  payment_type      TEXT,
  order_total       NUMERIC(12,2),
  discount_total    NUMERIC(12,2),
  shipping_total    NUMERIC(12,2)
);

CREATE TABLE IF NOT EXISTS retail.raw_order_items (
  order_item_id     BIGINT,
  order_id          BIGINT,
  product_id        INT,
  quantity          INT,
  unit_price        NUMERIC(12,2),
  line_total        NUMERIC(12,2)
);

-- Dimensions
CREATE TABLE IF NOT EXISTS retail.dim_customers (
  customer_id       INT PRIMARY KEY,
  signup_date       DATE,
  country           TEXT,
  channel           TEXT,
  email_domain      TEXT,
  is_active         BOOLEAN
);

CREATE TABLE IF NOT EXISTS retail.dim_products (
  product_id        INT PRIMARY KEY,
  category          TEXT,
  brand             TEXT,
  unit_cost         NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS retail.dim_date (
  date_key          DATE PRIMARY KEY,
  year              INT,
  month             INT,
  day               INT,
  week              INT,
  day_name          TEXT,
  month_name        TEXT
);

-- Facts
CREATE TABLE IF NOT EXISTS retail.fact_orders (
  order_id          BIGINT PRIMARY KEY,
  customer_id       INT REFERENCES retail.dim_customers(customer_id),
  order_date        DATE REFERENCES retail.dim_date(date_key),
  status            TEXT,
  payment_type      TEXT,
  order_total       NUMERIC(12,2),
  discount_total    NUMERIC(12,2),
  shipping_total    NUMERIC(12,2)
);

CREATE TABLE IF NOT EXISTS retail.fact_order_items (
  order_item_id     BIGINT PRIMARY KEY,
  order_id          BIGINT REFERENCES retail.fact_orders(order_id),
  product_id        INT REFERENCES retail.dim_products(product_id),
  quantity          INT,
  unit_price        NUMERIC(12,2),
  line_total        NUMERIC(12,2)
);

-- Gold marts
CREATE TABLE IF NOT EXISTS retail.mart_customer_metrics (
  customer_id               INT PRIMARY KEY,
  first_purchase_date       DATE,
  last_purchase_date        DATE,
  total_orders              INT,
  total_revenue             NUMERIC(14,2),
  avg_order_value           NUMERIC(14,2),
  avg_basket_size           NUMERIC(14,2),
  purchase_frequency_per_mo NUMERIC(14,4),
  days_since_last_purchase  INT,
  returns_rate              NUMERIC(10,4),
  dominant_category         TEXT
);

CREATE TABLE IF NOT EXISTS retail.mart_rfm_base (
  customer_id      INT PRIMARY KEY,
  recency_days     INT,
  frequency_orders INT,
  monetary_value   NUMERIC(14,2)
);

CREATE TABLE IF NOT EXISTS retail.mart_rfm_scored (
  customer_id   INT PRIMARY KEY,
  r_score       INT,
  f_score       INT,
  m_score       INT,
  rfm_score     INT,
  segment       TEXT
);

CREATE TABLE IF NOT EXISTS retail.mart_cohort_retention (
  cohort_month   DATE,
  active_month   DATE,
  cohort_size    INT,
  active_users   INT,
  retention_rate NUMERIC(10,4)
);
