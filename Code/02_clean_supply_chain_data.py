
import pandas as pd
from pathlib import Path

# Project directories
PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "Data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "Data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Load and clean suppliers
suppliers = pd.read_csv(RAW_DIR / "suppliers.csv")
suppliers = suppliers.drop_duplicates()
suppliers.to_csv(PROCESSED_DIR / "suppliers_clean.csv", index=False)

# Load and clean products
products = pd.read_csv(RAW_DIR / "products.csv")
products = products.drop_duplicates()
products.to_csv(PROCESSED_DIR / "products_clean.csv", index=False)

# Load and clean inventory
inventory = pd.read_csv(RAW_DIR / "inventory.csv")
inventory = inventory.drop_duplicates()
inventory.to_csv(PROCESSED_DIR / "inventory_clean.csv", index=False)

# Load and clean shipments
shipments = pd.read_csv(RAW_DIR / "shipments.csv")
shipments = shipments.drop_duplicates()

shipments["shipment_date"] = pd.to_datetime(
    shipments["shipment_date"], errors="coerce"
)
shipments["expected_delivery"] = pd.to_datetime(
    shipments["expected_delivery"], errors="coerce"
)
shipments["actual_delivery"] = pd.to_datetime(
    shipments["actual_delivery"], errors="coerce"
)

# Preserve missing actual_delivery for In Transit shipments
shipments.to_csv(
    PROCESSED_DIR / "shipments_clean.csv", index=False
)

# Load and clean demand history
demand = pd.read_csv(RAW_DIR / "demand_history.csv")
demand = demand.drop_duplicates()
demand["demand_date"] = pd.to_datetime(
    demand["demand_date"], errors="coerce"
)
demand.to_csv(
    PROCESSED_DIR / "demand_history_clean.csv", index=False
)

# Final summary
datasets = {
    "Suppliers": suppliers,
    "Products": products,
    "Inventory": inventory,
    "Shipments": shipments,
    "Demand History": demand,
}

print("\n===================================")
print("DATA CLEANING COMPLETED")
print("===================================")

for name, df in datasets.items():
    print(f"{name}: {len(df):,} records")

print("\nProcessed files saved in:", PROCESSED_DIR)
