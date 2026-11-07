

from datetime import datetime
import os
import logging
import smtplib

import psycopg2
from email.message import EmailMessage
from airflow.sdk import dag, task


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "host.docker.internal"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "retail_supply_chain"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
    )


@dag(
    dag_id="retail_supply_chain_hourly_refresh",
    schedule="@hourly",
    start_date=datetime(2026, 11, 6),
    catchup=False,
    tags=["retail", "supply_chain", "hourly_refresh", "email_alerts"],
)
def retail_supply_chain_hourly_refresh():

    @task
    def refresh_supply_chain_data():

        connection = get_db_connection()

        try:
            with connection.cursor() as cursor:

                tables = [
                    "suppliers",
                    "products",
                    "inventory",
                    "shipments",
                    "demand_history",
                ]

                record_counts = {}

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    record_counts[table] = cursor.fetchone()[0]

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pipeline_refresh_log (
                        refresh_id SERIAL PRIMARY KEY,
                        refresh_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        suppliers_count INTEGER,
                        products_count INTEGER,
                        inventory_count INTEGER,
                        shipments_count INTEGER,
                        demand_history_count INTEGER,
                        refresh_status VARCHAR(20)
                    )
                """)

                cursor.execute("""
                    INSERT INTO pipeline_refresh_log (
                        suppliers_count,
                        products_count,
                        inventory_count,
                        shipments_count,
                        demand_history_count,
                        refresh_status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    record_counts["suppliers"],
                    record_counts["products"],
                    record_counts["inventory"],
                    record_counts["shipments"],
                    record_counts["demand_history"],
                    "SUCCESS",
                ))

            connection.commit()
            logging.info("Hourly refresh completed: %s", record_counts)

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @task
    def send_supply_chain_alerts():

        connection = get_db_connection()

        try:
            with connection.cursor() as cursor:

                # Read shipment and demand anomalies
                cursor.execute("""
                    SELECT anomaly_category,
                           anomalies_detected,
                           anomaly_rate_pct
                    FROM anomaly_detection_summary
                    ORDER BY anomalies_detected DESC
                """)

                anomaly_rows = cursor.fetchall()

                # Count high-risk forecast products
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM demand_forecast_summary
                    WHERE stockout_risk = 'High'
                """)

                high_risk_products = cursor.fetchone()[0]

                # Count low-stock inventory records
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM inventory
                    WHERE quantity_on_hand <= reorder_level
                """)

                low_stock_records = cursor.fetchone()[0]

                # Create alert log to prevent repeated emails
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pipeline_alert_log (
                        alert_signature TEXT PRIMARY KEY,
                        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                signature = (
                    str(anomaly_rows)
                    + f"|high_risk={high_risk_products}"
                    + f"|low_stock={low_stock_records}"
                )

                if not anomaly_rows and not high_risk_products and not low_stock_records:
                    logging.info("No supply-chain alerts detected.")
                    return

                cursor.execute("""
                    SELECT 1
                    FROM pipeline_alert_log
                    WHERE alert_signature = %s
                """, (signature,))

                if cursor.fetchone():
                    logging.info("This alert was already sent. Skipping duplicate.")
                    return

            # Prepare email
            message = EmailMessage()
            message["Subject"] = "Retail Supply Chain - Risk Alert"
            message["From"] = os.environ["SMTP_USER"]
            message["To"] = os.environ["ALERT_EMAIL_TO"]

            body = """
RETAIL SUPPLY CHAIN CONTROL TOWER
AUTOMATED RISK ALERT

ANOMALY DETECTION:
"""

            for category, count, rate in anomaly_rows:
                body += (
                    f"\n{category}: {count} anomalies "
                    f"({rate}% anomaly rate)"
                )

            body += f"""

DEMAND FORECAST:
High-risk products: {high_risk_products}

INVENTORY:
Low-stock records: {low_stock_records}

Please review the Retail Supply Chain Control Tower dashboard.
"""

            message.set_content(body)

            # Send Gmail notification
            with smtplib.SMTP(
                os.environ["SMTP_HOST"],
                int(os.environ["SMTP_PORT"])
            ) as server:

                server.starttls()
                server.login(
                    os.environ["SMTP_USER"],
                    os.environ["SMTP_PASSWORD"]
                )
                server.send_message(message)

            # Record successful alert to prevent duplicates
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO pipeline_alert_log (alert_signature)
                    VALUES (%s)
                    ON CONFLICT (alert_signature) DO NOTHING
                """, (signature,))

            connection.commit()

            logging.info("Supply-chain risk alert email sent successfully.")

        except Exception:
            connection.rollback()
            logging.exception("Supply-chain email alert failed.")
            raise

        finally:
            connection.close()

    refresh_task = refresh_supply_chain_data()
    alert_task = send_supply_chain_alerts()

    refresh_task >> alert_task


retail_supply_chain_hourly_refresh()
