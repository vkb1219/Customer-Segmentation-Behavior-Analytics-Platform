import argparse
import os
import numpy as np
import pandas as pd
from datetime import date, timedelta

COUNTRIES = ["US", "CA", "GB", "IN", "AU"]
CHANNELS = ["web", "mobile", "marketplace"]
PAYMENT_TYPES = ["card", "paypal", "apple_pay", "google_pay"]
CATEGORIES = ["Electronics", "Apparel", "Home", "Beauty", "Sports", "Grocery"]
BRANDS = ["Nova", "Apex", "Zenith", "Orbit", "Pulse", "Vertex"]

def make_customers(n_customers: int, start_date: date, end_date: date, rng: np.random.Generator):
    days = (end_date - start_date).days
    signup_offsets = rng.integers(0, days, size=n_customers)
    signup_dates = [start_date + timedelta(days=int(x)) for x in signup_offsets]
    customers = pd.DataFrame({
        "customer_id": np.arange(1, n_customers + 1, dtype=int),
        "signup_date": signup_dates,
        "country": rng.choice(COUNTRIES, size=n_customers, p=[0.55,0.10,0.10,0.20,0.05]),
        "channel": rng.choice(CHANNELS, size=n_customers, p=[0.45,0.45,0.10]),
        "email_domain": rng.choice(["gmail.com","outlook.com","yahoo.com","proton.me"], size=n_customers),
        "is_active": rng.choice([True, False], size=n_customers, p=[0.92,0.08])
    })
    return customers

def make_products(n_products: int, rng: np.random.Generator):
    product_ids = np.arange(1, n_products + 1, dtype=int)
    categories = rng.choice(CATEGORIES, size=n_products)
    brands = rng.choice(BRANDS, size=n_products)
    unit_cost = np.round(rng.uniform(2, 120, size=n_products), 2)
    products = pd.DataFrame({
        "product_id": product_ids,
        "category": categories,
        "brand": brands,
        "unit_cost": unit_cost
    })
    return products

def simulate_orders(customers: pd.DataFrame, products: pd.DataFrame, start_date: date, days: int, rng: np.random.Generator):
    """
    Generates realistic-ish retail behavior:
    - Heavy-tail: a small % customers are high-frequency/high-spend
    - Seasonality: slight increase in Q4
    - Order status mix: completed mostly, some cancelled/returned
    """
    n_customers = customers.shape[0]
    customer_ids = customers["customer_id"].to_numpy()

    # propensity multipliers (high-value customers)
    hv_flag = rng.choice([0,1], size=n_customers, p=[0.93,0.07])
    propensity = np.where(hv_flag==1, rng.uniform(2.5, 6.0, size=n_customers), rng.uniform(0.6, 1.4, size=n_customers))

    orders = []
    order_items = []
    order_id = 10_000_000
    order_item_id = 50_000_000

    for d in range(days):
        day = start_date + timedelta(days=d)
        month = day.month
        seasonal = 1.25 if month in (11,12) else 1.0

        # base number of orders per day
        base_orders = int((n_customers / 140) * seasonal)  # scales with customer count
        day_orders = max(10, int(rng.poisson(base_orders)))

        # choose customers weighted by propensity
        weights = propensity / propensity.sum()
        chosen_customers = rng.choice(customer_ids, size=day_orders, replace=True, p=weights)

        for cid in chosen_customers:
            order_id += 1
            status = rng.choice(["completed","cancelled","returned"], p=[0.90,0.06,0.04])
            payment = rng.choice(["card","paypal","apple_pay","google_pay"], p=[0.65,0.18,0.09,0.08])
            shipping = float(np.round(rng.uniform(0, 12), 2))

            # number of line items
            n_items = int(rng.integers(1, 6))
            pids = rng.choice(products["product_id"].to_numpy(), size=n_items, replace=False)
            quantities = rng.integers(1, 4, size=n_items)

            # price model: cost * markup + noise
            product_costs = products.set_index("product_id").loc[pids]["unit_cost"].to_numpy()
            markup = rng.uniform(1.35, 2.8, size=n_items)
            unit_prices = np.round(product_costs * markup * rng.uniform(0.95, 1.05, size=n_items), 2)

            line_totals = np.round(unit_prices * quantities, 2)
            subtotal = float(np.round(line_totals.sum(), 2))

            # discount: higher for marketplace + seasonal promos
            discount_rate = 0.00
            if customers.set_index("customer_id").loc[cid]["channel"] == "marketplace":
                discount_rate += float(rng.uniform(0.02, 0.10))
            if month in (11,12):
                discount_rate += float(rng.uniform(0.00, 0.12))
            discount = float(np.round(subtotal * discount_rate, 2))

            order_total = float(np.round(subtotal - discount + shipping, 2))

            orders.append({
                "order_id": order_id,
                "customer_id": int(cid),
                "order_date": day,
                "status": status,
                "payment_type": payment,
                "order_total": order_total if status != "cancelled" else 0.0,
                "discount_total": discount if status != "cancelled" else 0.0,
                "shipping_total": shipping if status != "cancelled" else 0.0
            })

            for pid, q, up, lt in zip(pids, quantities, unit_prices, line_totals):
                order_item_id += 1
                order_items.append({
                    "order_item_id": order_item_id,
                    "order_id": order_id,
                    "product_id": int(pid),
                    "quantity": int(q),
                    "unit_price": float(up),
                    "line_total": float(lt) if status != "cancelled" else 0.0
                })

    return pd.DataFrame(orders), pd.DataFrame(order_items)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw", help="Output folder for raw CSVs")
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--customers", type=int, default=5000)
    ap.add_argument("--products", type=int, default=600)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    end_date = date.today()
    start_date = end_date - timedelta(days=args.days)

    customers = make_customers(args.customers, start_date - timedelta(days=90), end_date, rng)
    products = make_products(args.products, rng)
    orders, order_items = simulate_orders(customers, products, start_date, args.days, rng)

    customers.to_csv(os.path.join(args.out, "customers.csv"), index=False)
    products.to_csv(os.path.join(args.out, "products.csv"), index=False)
    orders.to_csv(os.path.join(args.out, "orders.csv"), index=False)
    order_items.to_csv(os.path.join(args.out, "order_items.csv"), index=False)

    print(f"Wrote CSVs to: {args.out}")
    print(customers.head(2))
    print(orders.head(2))

if __name__ == "__main__":
    main()
