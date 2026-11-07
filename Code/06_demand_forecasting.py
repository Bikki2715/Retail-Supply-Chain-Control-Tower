
import pandas as pd
from pathlib import Path
from prophet import Prophet

# -------------------------------------
# 1. PROJECT PATHS AND SETTINGS
# -------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data" / "processed"
REPORT_DIR = BASE_DIR / "Reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

FORECAST_DAYS = 30
TOP_PRODUCTS = 20

print("\n======================================")
print("PROPHET DEMAND FORECASTING")
print("======================================")

# -------------------------------------
# 2. LOAD DATA
# -------------------------------------

demand = pd.read_csv(DATA_DIR / "demand_history_clean.csv")
inventory = pd.read_csv(DATA_DIR / "inventory_clean.csv")

demand["demand_date"] = pd.to_datetime(demand["demand_date"])

print("Demand records loaded:", len(demand))
print("Inventory records loaded:", len(inventory))

# -------------------------------------
# 3. IDENTIFY TOP 20 PRODUCTS
# -------------------------------------

product_demand = (
    demand.groupby("product_id")["units_sold"]
    .sum()
    .sort_values(ascending=False)
)

top_product_ids = product_demand.head(TOP_PRODUCTS).index.tolist()

print("\nTop products selected:", len(top_product_ids))

# -------------------------------------
# 4. PREPARE INVENTORY
# -------------------------------------

current_inventory = (
    inventory.groupby("product_id")["quantity_on_hand"]
    .sum()
    .reset_index()
)

current_inventory.rename(
    columns={"quantity_on_hand": "current_stock"},
    inplace=True
)

# -------------------------------------
# 5. TRAIN PROPHET AND FORECAST
# -------------------------------------

all_forecasts = []
forecast_summary = []

for position, product_id in enumerate(top_product_ids, start=1):

    print(
        f"\nTraining model {position}/{len(top_product_ids)} "
        f"for Product ID {product_id}"
    )

    product_data = demand[
        demand["product_id"] == product_id
    ][["demand_date", "units_sold"]].copy()

    product_data = product_data.rename(
        columns={
            "demand_date": "ds",
            "units_sold": "y"
        }
    )

    product_data = (
        product_data.groupby("ds")["y"]
        .sum()
        .reset_index()
    )

    # Configure Prophet
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="additive"
    )

    # Train model
    model.fit(product_data)

    # Generate future dates
    future = model.make_future_dataframe(
        periods=FORECAST_DAYS,
        freq="D"
    )

    # Generate forecast
    forecast = model.predict(future)

    # Keep only future predictions
    future_forecast = forecast[
        forecast["ds"] > product_data["ds"].max()
    ][["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

    # Demand cannot be negative
    future_forecast["yhat"] = future_forecast["yhat"].clip(lower=0)
    future_forecast["yhat_lower"] = (
        future_forecast["yhat_lower"].clip(lower=0)
    )
    future_forecast["yhat_upper"] = (
        future_forecast["yhat_upper"].clip(lower=0)
    )

    future_forecast["product_id"] = product_id

    # Calculate forecast totals
    forecast_demand = future_forecast["yhat"].sum()
    average_daily_forecast = forecast_demand / FORECAST_DAYS

    # Retrieve current inventory
    stock_row = current_inventory[
        current_inventory["product_id"] == product_id
    ]

    if stock_row.empty:
        current_stock = 0
    else:
        current_stock = stock_row["current_stock"].iloc[0]

    # Calculate inventory coverage
    if average_daily_forecast > 0:
        days_of_inventory = current_stock / average_daily_forecast
    else:
        days_of_inventory = float("inf")

    # Identify stockout risk
    if forecast_demand > current_stock:
        risk = "High"
    elif days_of_inventory <= 45:
        risk = "Moderate"
    else:
        risk = "Low"

    forecast_summary.append({
        "product_id": product_id,
        "current_stock": current_stock,
        "forecast_demand_30_days": round(forecast_demand, 2),
        "average_daily_forecast": round(average_daily_forecast, 2),
        "days_of_inventory": (
            round(days_of_inventory, 2)
            if days_of_inventory != float("inf")
            else None
        ),
        "stockout_risk": risk
    })

    all_forecasts.append(future_forecast)

# -------------------------------------
# 6. SAVE FORECAST REPORTS
# -------------------------------------

forecast_details = pd.concat(
    all_forecasts,
    ignore_index=True
)

summary_df = pd.DataFrame(forecast_summary)

forecast_details.to_csv(
    REPORT_DIR / "demand_forecast_details.csv",
    index=False
)

summary_df.to_csv(
    REPORT_DIR / "demand_forecast_summary.csv",
    index=False
)

# -------------------------------------
# 7. DISPLAY RESULTS
# -------------------------------------

print("\n======================================")
print("30-DAY DEMAND FORECAST SUMMARY")
print("======================================")

print(summary_df.to_string(index=False))

print("\nSTOCKOUT RISK DISTRIBUTION")

print(
    summary_df["stockout_risk"]
    .value_counts()
    .to_string()
)

print("\n======================================")
print("FORECASTING COMPLETED")
print("Forecast records:", len(forecast_details))
print("Products forecast:", len(summary_df))
print("Forecast horizon:", FORECAST_DAYS, "days")
print("Reports saved in:", REPORT_DIR)
print("======================================")
