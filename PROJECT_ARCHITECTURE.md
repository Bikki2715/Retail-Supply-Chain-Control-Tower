# Project Architecture – Retail Supply Chain Control Tower

## System Architecture

```text
          SUPPLY CHAIN DATA GENERATION
                       |
                       v
              PYTHON DATA PIPELINE
                       |
                       v
                POSTGRESQL DB
                       |
          +------------+-------------+
          |            |             |
          v            v             v
      SQL KPIs     ANOMALY       DEMAND
                   DETECTION    FORECASTING
          |            |             |
          +------------+-------------+
                       |
                       v
                APACHE AIRFLOW
                 HOURLY MONITORING
                       |
              +--------+--------+
              |                 |
              v                 v
        APACHE SUPERSET     GMAIL SMTP
          DASHBOARDS       EMAIL ALERTS
```

## Component Responsibilities

| Component | Responsibility |
|---|---|
| Python | Data generation, cleaning, and analytics |
| PostgreSQL | Data storage and SQL analysis |
| Scikit-learn | Anomaly detection |
| Prophet | Demand forecasting |
| Apache Airflow | Hourly monitoring and workflow execution |
| Apache Superset | Interactive dashboard reporting |
| Docker | Container management |
| Gmail SMTP | Automated risk notifications |

## Data Flow

1. Supply-chain datasets are generated using Python.
2. Cleaned datasets are stored in PostgreSQL.
3. SQL and Python calculate operational KPIs.
4. Anomaly detection identifies unusual demand and shipment patterns.
5. Prophet forecasts demand for selected products.
6. Forecast results are compared with current inventory.
7. Airflow executes hourly monitoring tasks.
8. Superset presents analytical results.
9. Gmail sends alerts when risk indicators are identified.

## Monitoring and Automation

The Airflow workflow contains two tasks:

- `refresh_supply_chain_data`
- `send_supply_chain_alerts`

Both tasks have been successfully executed and verified.

The current hourly workflow monitors existing database records and logs execution status; it does not automatically regenerate source data or retrain forecasting models.

## Conclusion

The architecture integrates data engineering, analytics, predictive modeling, business intelligence, and workflow automation into one retail supply-chain monitoring solution.