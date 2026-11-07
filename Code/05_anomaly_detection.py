
import pandas as pd
import numpy as np
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data" / "processed"
REPORT_DIR = BASE_DIR / "Reports"

# Create reports folder if needed
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Z-score threshold
Z_THRESHOLD = 3

print("\n======================================")
print("SUPPLY CHAIN ANOMALY DETECTION")
print("======================================")

# -------------------------------------
# 1. SHIPMENT DELAY ANOMALY DETECTION
# -------------------------------------

shipments = pd.read_csv(DATA_DIR / "shipments_clean.csv")

shipments["shipment_date"] = pd.to_datetime(shipments["shipment_date"])
shipments["actual_delivery"] = pd.to_datetime(
    shipments["actual_delivery"], errors="coerce"
)

# Use completed shipments only
completed = shipments[
    shipments["actual_delivery"].notna()
].copy()

# Calculate actual delivery duration
completed["lead_time_days"] = (
    completed["actual_delivery"] - completed["shipment_date"]
).dt.days

# Calculate Z-score
mean_lead = completed["lead_time_days"].mean()
std_lead = completed["lead_time_days"].std()

if std_lead > 0:
    completed["delay_z_score"] = (
        completed["lead_time_days"] - mean_lead
    ) / std_lead
else:
    completed["delay_z_score"] = 0

# Identify unusual shipment durations
shipment_anomalies = completed[
    completed["delay_z_score"].abs() > Z_THRESHOLD
].copy()

shipment_anomalies["anomaly_type"] = "Unusual Shipment Lead Time"

shipment_anomalies.to_csv(
    REPORT_DIR / "shipment_anomalies.csv",
    index=False
)

# -------------------------------------
# 2. DEMAND SPIKE ANOMALY DETECTION
# -------------------------------------

demand = pd.read_csv(DATA_DIR / "demand_history_clean.csv")

demand["demand_date"] = pd.to_datetime(demand["demand_date"])

# Calculate Z-score separately for each product
product_stats = demand.groupby("product_id")["units_sold"].agg(
    ["mean", "std"]
).reset_index()

product_stats.rename(
    columns={
        "mean": "average_demand",
        "std": "demand_std"
    },
    inplace=True
)

demand = demand.merge(
    product_stats,
    on="product_id",
    how="left"
)

# Avoid division by zero
demand["demand_z_score"] = np.where(
    demand["demand_std"] > 0,
    (demand["units_sold"] - demand["average_demand"])
    / demand["demand_std"],
    0
)

# Identify unusually high demand
demand_anomalies = demand[
    demand["demand_z_score"] > Z_THRESHOLD
].copy()

demand_anomalies["anomaly_type"] = "Demand Spike"

demand_anomalies.to_csv(
    REPORT_DIR / "demand_anomalies.csv",
    index=False
)

# -------------------------------------
# 3. ANOMALY SUMMARY
# -------------------------------------

summary = pd.DataFrame({
    "Anomaly Category": [
        "Unusual Shipment Lead Time",
        "Demand Spike"
    ],
    "Total Records Analyzed": [
        len(completed),
        len(demand)
    ],
    "Anomalies Detected": [
        len(shipment_anomalies),
        len(demand_anomalies)
    ]
})

summary["Anomaly Rate (%)"] = (
    summary["Anomalies Detected"]
    / summary["Total Records Analyzed"] * 100
).round(2)

summary.to_csv(
    REPORT_DIR / "anomaly_detection_summary.csv",
    index=False
)

print("\nSHIPMENT ANOMALIES")
print("Completed shipments:", len(completed))
print("Unusual shipment durations:", len(shipment_anomalies))

print("\nDEMAND ANOMALIES")
print("Demand records:", len(demand))
print("Demand spikes:", len(demand_anomalies))

print("\nANOMALY SUMMARY")
print(summary.to_string(index=False))

print("\n======================================")
print("ANOMALY DETECTION COMPLETED")
print("Reports saved in:", REPORT_DIR)
print("======================================")
