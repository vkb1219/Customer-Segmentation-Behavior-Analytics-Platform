# Data Dictionary (Synthetic Retail)

## dim_customers
- customer_id (PK): int
- signup_date: date
- country: text
- channel: text (web, mobile, marketplace)
- email_domain: text (synthetic)
- is_active: bool

## dim_products
- product_id (PK): int
- category: text
- brand: text
- unit_cost: numeric

## dim_date
- date_key (PK): date
- year, month, day, week, day_name, month_name

## fact_orders
- order_id (PK): bigint
- customer_id (FK)
- order_date (FK to dim_date.date_key)
- status: text (completed, cancelled, returned)
- payment_type: text
- order_total: numeric
- discount_total: numeric
- shipping_total: numeric

## fact_order_items
- order_item_id (PK): bigint
- order_id (FK)
- product_id (FK)
- quantity: int
- unit_price: numeric
- line_total: numeric
