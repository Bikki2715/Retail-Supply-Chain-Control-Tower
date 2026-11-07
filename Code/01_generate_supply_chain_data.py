
import os
from pathlib import Path
from datetime import date, timedelta

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# --------------------------------------------------
# 1. PROJECT PATHS AND DATABASE CONNECTION
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "Data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_DIR / ".env")

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

rng = np.random.default_rng(42)

print("Connected to:", os.getenv("DB_NAME"))

# --------------------------------------------------
# 2. GENERATE SUPPLIERS
# --------------------------------------------------

supplier_rows = []

for i in range(1, 101):
    supplier_rows.append((
        f"Supplier_{i:03d}",
        rng.choice(["India", "China", "USA", "Germany", "Japan"]),
        int(rng.integers(3, 31))
    ))

supplier_ids = execute_values(
    conn.cursor(),
    """
    INSERT INTO suppliers
    (supplier_name, location, standard_lead_time_days)
    VALUES %s RETURNING supplier_id
    """,
    supplier_rows,
    fetch=True
)

supplier_ids = [row[0] for row in supplier_ids]
print("Suppliers generated:", len(supplier_ids))

# --------------------------------------------------
# 3. GENERATE PRODUCTS
# --------------------------------------------------

categories = [
    "Electronics", "Clothing", "Home",
    "Food", "Beauty", "Sports",
    "Automotive", "Toys"
]

product_rows = []

for i in range(1, 1001):
    product_rows.append((
        f"Product_{i:04d}",
        str(rng.choice(categories)),
        round(float(rng.uniform(10, 2000)), 2)
    ))

product_ids = execute_values(
    conn.cursor(),
    """
    INSERT INTO products
    (product_name, category, unit_price)
    VALUES %s RETURNING product_id
    """,
    product_rows,
    fetch=True
)

product_ids = [row[0] for row in product_ids]
print("Products generated:", len(product_ids))

# --------------------------------------------------
# 4. GENERATE INVENTORY
# --------------------------------------------------

warehouses = [f"Warehouse_{i:02d}" for i in range(1, 11)]
inventory_rows = []

for product_id in product_ids:
    for warehouse in warehouses:
        reorder_level = int(rng.integers(20, 101))
        quantity = int(rng.integers(0, 501))

        inventory_rows.append((
            product_id,
            warehouse,
            quantity,
            reorder_level
        ))

execute_values(
    conn.cursor(),
    """
    INSERT INTO inventory
    (product_id, warehouse, quantity_on_hand, reorder_level)
    VALUES %s
    """,
    inventory_rows,
    page_size=2000
)

print("Inventory records generated:", len(inventory_rows))

# --------------------------------------------------
# 5. GENERATE SHIPMENTS
# --------------------------------------------------

today = date.today()
start_date = today - timedelta(days=364)

shipment_rows = []

for _ in range(50000):
    supplier_id = int(rng.choice(supplier_ids))
    product_id = int(rng.choice(product_ids))

    lead_time = int(
        conn.cursor().execute(
            "SELECT standard_lead_time_days FROM suppliers WHERE supplier_id = %s",
            (supplier_id,)
        ) or 0
    ) if False else None

    shipment_date = start_date + timedelta(
        days=int(rng.integers(0, 365))
    )

    expected_days = int(rng.integers(3, 31))
    expected_delivery = shipment_date + timedelta(days=expected_days)

    delay = int(rng.choice(
        [-2, -1, 0, 1, 2, 3, 5, 7, 10, 15],
        p=[0.05, 0.08, 0.30, 0.15, 0.12, 0.10, 0.08, 0.06, 0.04, 0.02]
    ))

    actual_delivery = expected_delivery + timedelta(days=delay)
    quantity = int(rng.integers(10, 501))

    if actual_delivery > today:
        actual_delivery_value = None
        status = "In Transit"
    else:
        actual_delivery_value = actual_delivery
        status = "Delayed" if delay > 0 else "Delivered"

    shipment_rows.append((
        supplier_id,
        product_id,
        quantity,
        shipment_date,
        expected_delivery,
        actual_delivery_value,
        status
    ))

execute_values(
    conn.cursor(),
    """
    INSERT INTO shipments
    (supplier_id, product_id, quantity, shipment_date,
     expected_delivery, actual_delivery, status)
    VALUES %s
    """,
    shipment_rows,
    page_size=2000
)

print("Shipment records generated:", len(shipment_rows))

# --------------------------------------------------
# 6. GENERATE ONE YEAR OF DEMAND HISTORY
# --------------------------------------------------

demand_rows = []

for product_id in product_ids:
    base_demand = int(rng.integers(5, 100))

    for day_number in range(365):
        demand_date = start_date + timedelta(days=day_number)

        # Weekly and yearly demand patterns
        weekly_factor = 1.15 if demand_date.weekday() in [5, 6] else 1.0
        seasonal_factor = 1 + 0.20 * np.sin(
            2 * np.pi * day_number / 365
        )

        units_sold = max(
            0,
            int(rng.poisson(
                base_demand * weekly_factor * seasonal_factor
            ))
        )

        demand_rows.append((
            product_id,
            demand_date,
            units_sold
        ))

        if len(demand_rows) >= 10000:
            execute_values(
                conn.cursor(),
                """
                INSERT INTO demand_history
                (product_id, demand_date, units_sold)
                VALUES %s
                """,
                demand_rows,
                page_size=10000
            )
            demand_rows.clear()

if demand_rows:
    execute_values(
        conn.cursor(),
        """
        INSERT INTO demand_history
        (product_id, demand_date, units_sold)
        VALUES %s
        """,
        demand_rows,
        page_size=10000
    )

print("Demand history generated:", 365 * len(product_ids))

# --------------------------------------------------
# 7. SAVE SOURCE DATA AS CSV FILES
# --------------------------------------------------

pd.DataFrame(
    supplier_rows,
    columns=["supplier_name", "location", "standard_lead_time_days"]
).to_csv(RAW_DIR / "suppliers.csv", index=False)

pd.DataFrame(
    product_rows,
    columns=["product_name", "category", "unit_price"]
).to_csv(RAW_DIR / "products.csv", index=False)

pd.DataFrame(
    inventory_rows,
    columns=["product_id", "warehouse", "quantity_on_hand", "reorder_level"]
).to_csv(RAW_DIR / "inventory.csv", index=False)

pd.DataFrame(
    shipment_rows,
    columns=[
        "supplier_id", "product_id", "quantity",
        "shipment_date", "expected_delivery",
        "actual_delivery", "status"
    ]
).to_csv(RAW_DIR / "shipments.csv", index=False)

print("CSV source files saved in:", RAW_DIR)

# --------------------------------------------------
# 8. COMMIT AND CLOSE
# --------------------------------------------------

conn.commit()
conn.close()

print("\n===================================")
print("SUPPLY CHAIN DATA GENERATION DONE")
print("===================================")
print("Suppliers: 100")
print("Products: 1,000")
print("Inventory: 10,000")
print("Shipments: 50,000")
print("Demand history: 365,000")
print("Database: retail_supply_chain")
print("===================================")
