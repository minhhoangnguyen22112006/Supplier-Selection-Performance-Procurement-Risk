/*
Project B | Run after importing initial CSVs with python/load_sqlserver.py.
Historical scorecards must be computed at PO level first, not by joining 1:N shipment and invoice facts.
Synthetic case only. Final optimized portfolio outputs can be read by Tableau directly from CSV,
or loaded into pb.b_decision_* using python/load_decisions_sqlserver.py.
*/
USE SupplierManagementB;
GO
CREATE OR ALTER VIEW pb.v_supplier_po_performance AS
WITH receipts AS (
    SELECT p.po_id,p.supplier_id,p.material_id,p.order_month,p.ordered_units,p.required_date,
           ISNULL(SUM(s.received_units),0) AS received_units,
           ISNULL(SUM(CASE WHEN s.receipt_date<=p.required_date THEN s.received_units ELSE 0 END),0) AS on_time_received_units
    FROM pb.fact_purchase_order p
    LEFT JOIN pb.fact_shipment s ON s.po_id=p.po_id
    GROUP BY p.po_id,p.supplier_id,p.material_id,p.order_month,p.ordered_units,p.required_date
), qual AS (
    SELECT p.po_id,SUM(i.inspected_units) inspected_units,SUM(i.rejected_units) rejected_units
    FROM pb.fact_purchase_order p
    JOIN pb.fact_shipment s ON s.po_id=p.po_id
    JOIN pb.fact_quality_inspection i ON i.shipment_id=s.shipment_id
    GROUP BY p.po_id
), spend AS (
    SELECT po_id,SUM(total_landed_cost_usd) AS landed_spend_usd
    FROM pb.fact_invoice GROUP BY po_id
)
SELECT r.po_id,r.supplier_id,r.material_id,r.order_month,r.ordered_units,
       r.received_units,r.on_time_received_units,
       CASE WHEN r.on_time_received_units>=r.ordered_units THEN 1 ELSE 0 END AS po_otif_flag,
       ISNULL(q.inspected_units,0) AS inspected_units,ISNULL(q.rejected_units,0) AS rejected_units,
       ISNULL(s.landed_spend_usd,0) AS landed_spend_usd
FROM receipts r LEFT JOIN qual q ON q.po_id=r.po_id LEFT JOIN spend s ON s.po_id=r.po_id;
GO
CREATE OR ALTER VIEW pb.v_supplier_monthly_tableau AS
SELECT order_month AS month_id,supplier_id,
 COUNT(*) AS po_count,
 SUM(ordered_units) AS ordered_units,SUM(received_units) AS received_units,
 SUM(on_time_received_units) AS on_time_received_units,
 SUM(po_otif_flag) AS po_otif_count,
 SUM(inspected_units) AS inspected_units,SUM(rejected_units) AS rejected_units,
 SUM(landed_spend_usd) AS landed_spend_usd,
 CAST(100.0*SUM(po_otif_flag)/NULLIF(COUNT(*),0) AS DECIMAL(10,2)) AS po_otif_pct,
 CAST(1000000.0*SUM(rejected_units)/NULLIF(SUM(inspected_units),0) AS DECIMAL(14,2)) AS defect_ppm
FROM pb.v_supplier_po_performance
GROUP BY order_month,supplier_id;
GO
CREATE OR ALTER VIEW pb.v_rfqs_unit_economics AS
SELECT q.plan_month,q.material_id,m.material_name,m.criticality,
       q.supplier_id,s.supplier_name,s.region,q.quoted_lead_time_days,
       q.minimum_order_qty_units,q.maximum_capacity_units,q.eligible_for_award,
       q.quoted_unit_price_usd,q.freight_usd_per_unit,q.duty_pct,
       q.quoted_unit_price_usd*(1+q.duty_pct)+q.freight_usd_per_unit AS landed_unit_cost_usd
FROM pb.fact_supplier_quote q
JOIN pb.dim_supplier s ON s.supplier_id=q.supplier_id
JOIN pb.dim_material m ON m.material_id=q.material_id;
GO
CREATE OR ALTER VIEW pb.v_kraljic_materials AS
SELECT m.material_id,m.material_name,m.criticality,c.category_name,
       c.supply_risk_score,c.profit_impact_score,c.kraljic_quadrant
FROM pb.dim_material m JOIN pb.dim_category c ON c.category_id=m.category_id;
GO
-- Optional views on imported optimizer outputs (created by load_decisions_sqlserver.py):
IF OBJECT_ID('pb.b_decision_scenario_summary','U') IS NOT NULL
 EXEC('CREATE OR ALTER VIEW pb.v_decision_scenarios AS SELECT * FROM pb.b_decision_scenario_summary');
GO
IF OBJECT_ID('pb.b_decision_allocation','U') IS NOT NULL
 EXEC('CREATE OR ALTER VIEW pb.v_decision_allocation AS SELECT * FROM pb.b_decision_allocation');
GO
