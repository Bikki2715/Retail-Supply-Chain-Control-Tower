
import pandas as pd
import numpy as np
from pathlib import Path

# ==========================================
# 1. PROJECT DIRECTORIES
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_DIR / "Data" / "processed"
REPORT_DIR = PROJECT_DIR / "Reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. LOAD PROCESSED DATASETS
# ==========================================

inventory = pd.read_csv(DATA_DIR / "inventory_clean.csv")
shipments = pd.read_csv(DATA_DIR / "shipments_clean.csv")
demand = pd.read_csv(DATA_DIR / "demand_history_clean.csv")

# ==========================================
# 3. DATA TYPE CONVERSION
# ==========================================

shipments["shipment_date"] = pd.to_datetime(
    shipments["shipment_date"], errors="coerce"
)

shipments["expected_delivery"] = pd.to_datetime(
    shipments["expected_delivery"], errors="coerce"
)

shipments["actual_delivery"] = pd.to_datetime(
    shipments["actual_delivery"], errors="coerce"
)

demand["demand_date"] = pd.to_datetime(
    demand["demand_date"], errors="coerce"
)

# ==========================================
# 4. KPI 1: STOCK-OUT RATE
# ==========================================

total_inventory_records = len(inventory)

stockout_records = (
    inventory["quantity_on_hand"] <= 0
).sum()

stockout_rate = (
    stockout_records / total_inventory_records * 100
    if total_inventory_records > 0 else 0
)

# ==========================================
# 5. PREPARE COMPLETED SHIPMENTS
# ==========================================

# Include both Delivered and Delayed shipments.
# Exclude In Transit shipments because they have
# no actual delivery date yet.

completed = shipments[
    shipments["status"].isin(["Delivered", "Delayed"])
].copy()

# Keep records with valid delivery dates.

completed = completed.dropna(
    subset=["shipment_date", "expected_delivery", "actual_delivery"]
)

total_completed = len(completed)

# ==========================================
# 6. KPI 2: ON-TIME DELIVERY RATE
# ==========================================

on_time_shipments = (
    completed["actual_delivery"] <= completed["expected_delivery"]
).sum()

on_time_rate = (
    on_time_shipments / total_completed * 100
    if total_completed > 0 else 0
)

# ==========================================
# 7. KPI 3: AVERAGE SUPPLIER LEAD TIME
# ==========================================

completed["lead_time_days"] = (
    completed["actual_delivery"] -
    completed["shipment_date"]
).dt.days

average_lead_time = (
    completed["lead_time_days"].mean()
    if total_completed > 0 else 0
)

# ==========================================
# 8. KPI 4: DAYS OF INVENTORY
# ==========================================

# Calculate average daily demand for each product.

average_daily_demand = (
    demand.groupby("product_id")["units_sold"].mean()
)

# Calculate total current stock for each product
# across all warehouses.

current_stock = (
    inventory.groupby("product_id")["quantity_on_hand"].sum()
)

# Combine stock and demand.

inventory_summary = pd.DataFrame({
    "average_daily_demand": average_daily_demand,
    "current_stock": current_stock
})

# Calculate days of inventory.

inventory_summary["days_of_inventory"] = np.where(
    inventory_summary["average_daily_demand"] > 0,
    inventory_summary["current_stock"] /
    inventory_summary["average_daily_demand"],
    np.nan
)

average_days_inventory = (
    inventory_summary["days_of_inventory"].mean()
)

# ==========================================
# 9. CREATE KPI SUMMARY
# ==========================================

kpi_df = pd.DataFrame({
    "KPI": [
        "Stock-out Rate (%)",
        "On-time Delivery Rate (%)",
        "Average Supplier Lead Time (Days)",
        "Average Days of Inventory"
    ],

    "Value": [
        round(stockout_rate, 2),
        round(on_time_rate, 2),
        round(average_lead_time, 2),
        round(average_days_inventory, 2)
    ]
})

# ==========================================
# 10. SAVE REPORTS
# ==========================================

kpi_df.to_csv(
    REPORT_DIR / "supply_chain_kpis.csv",
    index=False
)

inventory_summary.to_csv(
    REPORT_DIR / "product_inventory_analysis.csv"
)

# ==========================================
# 11. DISPLAY RESULTS
# ==========================================

print("\n===================================")
print("SUPPLY CHAIN KPI RESULTS")
print("===================================")

print(kpi_df.to_string(index=False))

print("\n===================================")
print("ADDITIONAL INFORMATION")
print("===================================")

print("Total inventory records:", total_inventory_records)

print("Stock-out records:", stockout_records)

print("Total shipments:", len(shipments))

print("Completed shipments:", total_completed)

print("In-transit shipments:",
      (shipments["status"] == "In Transit").sum())

print("On-time shipments:", on_time_shipments)

print("Delayed shipments:",
      (completed["actual_delivery"] >
       completed["expected_delivery"]).sum())

print("\nAverage daily demand:",
      round(average_daily_demand.mean(), 2))

print("\n===================================")
print("KPI CALCULATION COMPLETED")
print("===================================")

print("\nReports saved in:", REPORT_DIR)

