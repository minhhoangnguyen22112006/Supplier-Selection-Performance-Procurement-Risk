-- Historical supplier scorecard: correct grain = one row per PO, aggregate receipts first.
WITH receipt_rollup AS (
 SELECT p.po_id, p.supplier_id, p.material_id, p.ordered_units, p.required_date,
        COALESCE(SUM(s.received_units),0) AS received_units,
        COALESCE(SUM(CASE WHEN s.receipt_date <= p.required_date THEN s.received_units ELSE 0 END),0) AS on_time_received,
        MAX(s.receipt_date) AS last_receipt_date
 FROM pb.fact_purchase_order p LEFT JOIN pb.fact_shipment s ON p.po_id=s.po_id
 GROUP BY p.po_id,p.supplier_id,p.material_id,p.ordered_units,p.required_date
), po_scorecard AS (
 SELECT *, CASE WHEN on_time_received >= ordered_units THEN 1 ELSE 0 END AS otif_po,
           CASE WHEN last_receipt_date <= required_date AND received_units>0 THEN 1 ELSE 0 END AS otd_po
 FROM receipt_rollup
), defects AS (
 SELECT sh.supplier_id,SUM(q.inspected_units) inspected_units,SUM(q.rejected_units) rejected_units
 FROM pb.fact_quality_inspection q JOIN pb.fact_shipment sh ON q.shipment_id=sh.shipment_id
 GROUP BY sh.supplier_id
), costs AS (
 SELECT p.supplier_id,SUM(i.total_landed_cost_usd) AS spend_usd
 FROM pb.fact_invoice i JOIN pb.fact_purchase_order p ON p.po_id=i.po_id
 GROUP BY p.supplier_id
)
SELECT s.supplier_id,s.supplier_name,
 COUNT(ps.po_id) purchase_orders, SUM(ps.ordered_units) ordered_units,SUM(ps.received_units) received_units,
 CAST(100.0*SUM(ps.otif_po)/NULLIF(COUNT(ps.po_id),0) AS DECIMAL(9,2)) otif_po_pct,
 CAST(100.0*SUM(ps.otd_po)/NULLIF(COUNT(ps.po_id),0) AS DECIMAL(9,2)) otd_po_pct,
 CAST(1000000.0*MAX(d.rejected_units)/NULLIF(MAX(d.inspected_units),0) AS DECIMAL(14,2)) defect_ppm,
 CAST(MAX(c.spend_usd) AS DECIMAL(18,2)) spend_usd
FROM pb.dim_supplier s JOIN po_scorecard ps ON s.supplier_id=ps.supplier_id
LEFT JOIN defects d ON d.supplier_id=s.supplier_id
LEFT JOIN costs c ON c.supplier_id=s.supplier_id
GROUP BY s.supplier_id,s.supplier_name ORDER BY spend_usd DESC;

-- Future quoted landed unit cost and supplier capacity for Python MILP.
SELECT plan_month, supplier_id, material_id, minimum_order_qty_units, maximum_capacity_units,
 quoted_unit_price_usd, freight_usd_per_unit, duty_pct,
 quoted_unit_price_usd*(1+duty_pct)+freight_usd_per_unit AS landed_unit_cost_usd
FROM pb.fact_supplier_quote WHERE eligible_for_award=1;

-- Historical spend by category (no fanout: invoice -> PO -> material -> category)
SELECT m.category_id, SUM(i.total_landed_cost_usd) AS spend_usd
FROM pb.fact_invoice i JOIN pb.fact_purchase_order p ON i.po_id=p.po_id
JOIN pb.dim_material m ON m.material_id=p.material_id
GROUP BY m.category_id ORDER BY spend_usd DESC;
