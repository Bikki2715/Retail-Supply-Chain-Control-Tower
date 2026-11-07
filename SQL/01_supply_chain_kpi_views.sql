-- DA-03: Retail and Supply Chain Control Tower
-- SQL Reporting Layer: KPI Views

-- 1. Inventory KPI Summary
CREATE OR REPLACE VIEW vw_inventory_kpis AS
SELECT
    COUNT(*) AS total_inventory_records,
    SUM(quantity_on_hand) AS total_stock_units,
    SUM(CASE WHEN quantity_on_hand <= 0 THEN 1 ELSE 0 END) AS stockout_records,
    ROUND(
        100.0 * SUM(CASE WHEN quantity_on_hand <= 0 THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 2
    ) AS stockout_rate_pct
FROM inventory;


-- 2. Shipment Delivery KPI Summary
CREATE OR REPLACE VIEW vw_delivery_kpis AS
SELECT
    COUNT(*) AS total_completed_shipments,
    SUM(CASE WHEN actual_delivery <= expected_delivery THEN 1 ELSE 0 END)
        AS on_time_shipments,
    SUM(CASE WHEN actual_delivery > expected_delivery THEN 1 ELSE 0 END)
        AS delayed_shipments,
    ROUND(
        100.0 * SUM(CASE WHEN actual_delivery <= expected_delivery THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 2
    ) AS on_time_delivery_rate_pct,
    ROUND(AVG(actual_delivery - shipment_date), 2)
        AS average_lead_time_days
FROM shipments
WHERE actual_delivery IS NOT NULL;


-- 3. Supplier Performance Summary
CREATE OR REPLACE VIEW vw_supplier_performance AS
SELECT
    s.supplier_id,
    s.supplier_name,
    s.location,
    s.standard_lead_time_days,
    COUNT(sh.shipment_id) AS total_shipments,
    SUM(CASE WHEN sh.actual_delivery <= sh.expected_delivery THEN 1 ELSE 0 END)
        AS on_time_shipments,
    SUM(CASE WHEN sh.actual_delivery > sh.expected_delivery THEN 1 ELSE 0 END)
        AS delayed_shipments,
    ROUND(
        100.0 * SUM(CASE WHEN sh.actual_delivery <= sh.expected_delivery THEN 1 ELSE 0 END)
        / NULLIF(COUNT(sh.shipment_id), 0), 2
    ) AS on_time_delivery_rate_pct,
    ROUND(AVG(sh.actual_delivery - sh.shipment_date), 2)
        AS average_lead_time_days
FROM suppliers s
LEFT JOIN shipments sh
    ON s.supplier_id = sh.supplier_id
    AND sh.actual_delivery IS NOT NULL
GROUP BY
    s.supplier_id,
    s.supplier_name,
    s.location,
    s.standard_lead_time_days;


-- 4. Product Inventory and Demand Summary
CREATE OR REPLACE VIEW vw_product_inventory_demand AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COALESCE(i.current_stock, 0) AS current_stock,
    COALESCE(d.total_units_sold, 0) AS total_units_sold,
    COALESCE(d.average_daily_demand, 0) AS average_daily_demand,
    ROUND(
        COALESCE(i.current_stock, 0)::NUMERIC
        / NULLIF(d.average_daily_demand, 0), 2
    ) AS days_of_inventory
FROM products p
LEFT JOIN (
    SELECT
        product_id,
        SUM(quantity_on_hand) AS current_stock
    FROM inventory
    GROUP BY product_id
) i ON p.product_id = i.product_id
LEFT JOIN (
    SELECT
        product_id,
        SUM(units_sold) AS total_units_sold,
        AVG(units_sold::NUMERIC) AS average_daily_demand
    FROM demand_history
    GROUP BY product_id
) d ON p.product_id = d.product_id;