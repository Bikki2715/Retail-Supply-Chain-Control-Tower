# Retail Supply Chain Control Tower

## 1. Project Overview

The **Retail Supply Chain Control Tower** is a data analytics project designed to monitor inventory, shipment performance, supplier efficiency, and product demand.

The system uses Python, PostgreSQL, Apache Airflow, and Apache Superset to transform supply-chain data into actionable insights through KPI reporting, anomaly detection, demand forecasting, dashboards, and automated email alerts.

## 2. Project Objectives

- Monitor inventory levels and identify low-stock products.
- Analyze shipment delivery performance.
- Evaluate supplier performance and lead times.
- Detect unusual shipment delays and demand spikes.
- Forecast product demand for the next 30 days.
- Identify potential inventory stockout risks.
- Automate hourly monitoring and email alerts.
- Present insights through an interactive dashboard.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Data processing and analytics |
| Pandas, NumPy | Data cleaning and manipulation |
| Matplotlib | Data visualization |
| Scikit-learn | Anomaly detection |
| Prophet | Demand forecasting |
| PostgreSQL | Relational database |
| Apache Airflow | Scheduled workflow automation |
| Apache Superset | Interactive dashboards |
| Docker | Containerized deployment |
| Gmail SMTP | Email notifications |

## 4. Dataset Overview

The project contains five primary datasets:

| Dataset | Records |
|---|---:|
| Suppliers | 100 |
| Products | 1,000 |
| Inventory | 10,000 |
| Shipments | 50,000 |
| Demand History | 365,000 |
| **Total** | **426,100** |

## 5. Key Performance Indicators

The following KPIs were calculated:

| KPI | Result |
|---|---:|
| Stock-out Rate | 0.21% |
| On-time Delivery Rate | 43.25% |
| Average Supplier Lead Time | 18.32 days |
| Average Days of Inventory | 81.59 days |
| Low-stock Records | 1,212 |

## 6. Anomaly Detection

Anomaly detection was performed to identify unusual supply-chain patterns.

| Anomaly Category | Records Analyzed | Anomalies |
|---|---:|---:|
| Unusual Shipment Lead Time | 47,382 | 33 |
| Demand Spike | 365,000 | 768 |

## 7. Demand Forecasting

Prophet was used to forecast demand for the next 30 days for 20 selected products.

- Total forecast records: 600
- High stockout-risk products: 17
- Moderate stockout-risk products: 3

Forecasted demand was compared with current inventory to identify potential stockout risks.

## 8. Database and SQL Analysis

The project uses PostgreSQL database `retail_supply_chain`.

Primary tables:
- suppliers
- products
- inventory
- shipments
- demand_history

SQL views were created for delivery KPIs, inventory KPIs, product inventory and demand, and supplier performance.

## 9. Dashboard Development

An interactive dashboard was developed using Apache Superset.

Dashboard visualizations include:
- Low-stock records
- Stock-out rate
- Total products
- Total inventory stock
- Warehouse inventory summary
- Shipment delivery performance
- Supplier delivery performance
- Demand forecast and stockout risk
- Shipment delivery status distribution
- Anomaly detection summary
- Seven-day supplier delay impact analysis

## 10. Workflow Automation and Email Alerts

Apache Airflow was configured to run the monitoring workflow hourly.

The workflow:
1. Checks the supply-chain database tables.
2. Records table counts and execution status.
3. Checks anomaly, forecast-risk, and low-stock summaries.
4. Sends email notifications through Gmail SMTP.
5. Records alert signatures to prevent duplicate notifications.

Successful Airflow task executions and email delivery were verified.

**Note:** The current hourly workflow monitors and logs existing database data. It does not automatically regenerate source data or rerun the forecasting and anomaly-detection models every hour.

## 11. Project Outcome

The project demonstrates how data analytics and automation can support supply-chain decision-making.

It provides visibility into inventory health, supplier performance, shipment delays, demand patterns, and potential stockout risks through database analysis, predictive forecasting, interactive dashboards, and email notifications.

## 12. Conclusion

The Retail Supply Chain Control Tower integrates data analytics, SQL, machine learning, forecasting, dashboard reporting, and workflow automation into a unified analytical solution. It helps identify operational risks and supports more informed inventory and supply-chain management decisions.

---

**Project:** Retail Supply Chain Control Tower  
**Project Category:** Data Analytics  
**Database:** PostgreSQL  
**Dashboard:** Apache Superset  
**Workflow Automation:** Apache Airflow