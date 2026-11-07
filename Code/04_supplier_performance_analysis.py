import pandas as pd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data" / "processed"
REPORT_DIR = BASE_DIR / "Reports"

# Load shipment and supplier data
shipments = pd.read_csv(DATA_DIR / "shipments_clean.csv")
suppliers = pd.read_csv(DATA_DIR / "suppliers_clean.csv")
suppliers.insert(0, "supplier_id", range(1, len(suppliers) + 1))

# Convert date columns
shipments["shipment_date"] = pd.to_datetime(shipments["shipment_date"])
shipments["expected_delivery"] = pd.to_datetime(shipments["expected_delivery"])
shipments["actual_delivery"] = pd.to_datetime(
    shipments["actual_delivery"], errors="coerce"
)

# Consider only completed shipments
completed = shipments[
    shipments["status"].isin(["Delivered", "Delayed"])
].copy()

# Calculate delivery performance
completed["lead_time_days"] = (
    completed["actual_delivery"] - completed["shipment_date"]
).dt.days

completed["on_time"] = (
    completed["actual_delivery"] <= completed["expected_delivery"]
)

# Group by supplier
performance = completed.groupby("supplier_id").agg(
    total_shipments=("quantity", "count"),
    on_time_shipments=("on_time", "sum"),
    average_lead_time_days=("lead_time_days", "mean")
).reset_index()

# Calculate delayed shipments and on-time rate
performance["delayed_shipments"] = (
    performance["total_shipments"] - performance["on_time_shipments"]
)

performance["on_time_rate_percent"] = (
    performance["on_time_shipments"] /
    performance["total_shipments"] * 100
)

# Add supplier names and standard lead times
performance = performance.merge(
    suppliers[["supplier_id", "supplier_name", "standard_lead_time_days"]],
    on="supplier_id",
    how="left"
)

# Rank suppliers by on-time performance
performance = performance.sort_values(
    by=["on_time_rate_percent", "average_lead_time_days"],
    ascending=[False, True]
)

performance.insert(
    0, "performance_rank", range(1, len(performance) + 1)
)

# Round numerical values
performance["average_lead_time_days"] = (
    performance["average_lead_time_days"].round(2)
)
performance["on_time_rate_percent"] = (
    performance["on_time_rate_percent"].round(2)
)

# Save report
output_file = REPORT_DIR / "supplier_performance_analysis.csv"
performance.to_csv(output_file, index=False)

# Display summary
print("\n======================================")
print("SUPPLIER PERFORMANCE ANALYSIS")
print("======================================")

print("Total suppliers analyzed:", len(performance))
print("Total completed shipments:", len(completed))

print("\nTOP 10 SUPPLIERS")
print(
    performance[
        [
            "performance_rank",
            "supplier_name",
            "total_shipments",
            "on_time_rate_percent",
            "average_lead_time_days"
        ]
    ].head(10).to_string(index=False)
)

print("\nBOTTOM 10 SUPPLIERS")
print(
    performance[
        [
            "performance_rank",
            "supplier_name",
            "total_shipments",
            "on_time_rate_percent",
            "average_lead_time_days"
        ]
    ].tail(10).to_string(index=False)
)

print("\n======================================")
print("SUPPLIER ANALYSIS COMPLETED")
print("Report saved at:", output_file)
print("======================================")