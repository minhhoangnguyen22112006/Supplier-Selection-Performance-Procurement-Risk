-- Project B synthetic supplier management SQL Server schema
-- CAUTION: rerunning drops pb tables and existing data.
IF DB_ID(N'SupplierManagementB') IS NULL CREATE DATABASE SupplierManagementB;
GO
USE SupplierManagementB;
GO
IF SCHEMA_ID('pb') IS NULL EXEC('CREATE SCHEMA pb');
GO
IF OBJECT_ID('pb.agg_supplier_scorecard', 'U') IS NOT NULL DROP TABLE pb.agg_supplier_scorecard;
GO
IF OBJECT_ID('pb.agg_po_delivery_scorecard', 'U') IS NOT NULL DROP TABLE pb.agg_po_delivery_scorecard;
GO
IF OBJECT_ID('pb.dim_cost_assumptions', 'U') IS NOT NULL DROP TABLE pb.dim_cost_assumptions;
GO
IF OBJECT_ID('pb.dim_risk_assumptions', 'U') IS NOT NULL DROP TABLE pb.dim_risk_assumptions;
GO
IF OBJECT_ID('pb.fact_baseline_allocation', 'U') IS NOT NULL DROP TABLE pb.fact_baseline_allocation;
GO
IF OBJECT_ID('pb.fact_future_capacity', 'U') IS NOT NULL DROP TABLE pb.fact_future_capacity;
GO
IF OBJECT_ID('pb.fact_supplier_quote', 'U') IS NOT NULL DROP TABLE pb.fact_supplier_quote;
GO
IF OBJECT_ID('pb.fact_future_demand', 'U') IS NOT NULL DROP TABLE pb.fact_future_demand;
GO
IF OBJECT_ID('pb.fact_risk_event', 'U') IS NOT NULL DROP TABLE pb.fact_risk_event;
GO
IF OBJECT_ID('pb.fact_historical_capacity', 'U') IS NOT NULL DROP TABLE pb.fact_historical_capacity;
GO
IF OBJECT_ID('pb.fact_payment', 'U') IS NOT NULL DROP TABLE pb.fact_payment;
GO
IF OBJECT_ID('pb.fact_invoice', 'U') IS NOT NULL DROP TABLE pb.fact_invoice;
GO
IF OBJECT_ID('pb.fact_quality_inspection', 'U') IS NOT NULL DROP TABLE pb.fact_quality_inspection;
GO
IF OBJECT_ID('pb.fact_shipment', 'U') IS NOT NULL DROP TABLE pb.fact_shipment;
GO
IF OBJECT_ID('pb.fact_purchase_order', 'U') IS NOT NULL DROP TABLE pb.fact_purchase_order;
GO
IF OBJECT_ID('pb.fact_material_demand_history', 'U') IS NOT NULL DROP TABLE pb.fact_material_demand_history;
GO
IF OBJECT_ID('pb.bridge_supplier_material', 'U') IS NOT NULL DROP TABLE pb.bridge_supplier_material;
GO
IF OBJECT_ID('pb.dim_supplier', 'U') IS NOT NULL DROP TABLE pb.dim_supplier;
GO
IF OBJECT_ID('pb.dim_material', 'U') IS NOT NULL DROP TABLE pb.dim_material;
GO
IF OBJECT_ID('pb.dim_category', 'U') IS NOT NULL DROP TABLE pb.dim_category;
GO
CREATE TABLE pb.dim_category (
    [category_id] NVARCHAR(24) NOT NULL,
    [category_name] NVARCHAR(35) NULL,
    [supply_risk_score] DECIMAL(18,6) NULL,
    [profit_impact_score] DECIMAL(18,6) NULL,
    [kraljic_quadrant] NVARCHAR(24) NULL,
    CONSTRAINT PK_dim_category PRIMARY KEY ([category_id])
);
GO
CREATE TABLE pb.dim_material (
    [material_id] NVARCHAR(24) NOT NULL,
    [material_name] NVARCHAR(42) NULL,
    [category_id] NVARCHAR(24) NULL,
    [uom] NVARCHAR(24) NULL,
    [reference_price_usd] DECIMAL(18,6) NULL,
    [monthly_demand_base_units] INT NULL,
    [criticality] NVARCHAR(24) NULL,
    CONSTRAINT PK_dim_material PRIMARY KEY ([material_id])
);
GO
CREATE TABLE pb.dim_supplier (
    [supplier_id] NVARCHAR(24) NOT NULL,
    [supplier_name] NVARCHAR(37) NULL,
    [country] NVARCHAR(24) NULL,
    [region] NVARCHAR(24) NULL,
    [financial_health_score] INT NULL,
    [baseline_otd_probability] DECIMAL(18,6) NULL,
    [baseline_defect_probability] DECIMAL(18,6) NULL,
    [baseline_late_probability] DECIMAL(18,6) NULL,
    [annual_disruption_probability] DECIMAL(18,6) NULL,
    [payment_terms_days] INT NULL,
    [qualification_status] NVARCHAR(24) NULL,
    [assumption_source] NVARCHAR(35) NULL,
    CONSTRAINT PK_dim_supplier PRIMARY KEY ([supplier_id])
);
GO
CREATE TABLE pb.bridge_supplier_material (
    [supplier_id] NVARCHAR(24) NOT NULL,
    [material_id] NVARCHAR(24) NOT NULL,
    [approved_since] DATE NULL,
    [is_approved] INT NULL,
    [preferred_supplier] INT NULL,
    [nominal_monthly_capacity_units] INT NULL,
    [minimum_order_qty_units] INT NULL,
    [standard_lead_time_days] INT NULL,
    [freight_usd_per_unit] DECIMAL(18,6) NULL,
    [import_duty_pct] DECIMAL(18,6) NULL,
    [price_modifier] DECIMAL(18,6) NULL,
    CONSTRAINT PK_bridge_supplier_material PRIMARY KEY ([supplier_id],[material_id])
);
GO
CREATE TABLE pb.fact_material_demand_history (
    [month_id] CHAR(7) NOT NULL,
    [material_id] NVARCHAR(24) NOT NULL,
    [demand_units] INT NULL,
    [demand_type] NVARCHAR(27) NULL,
    [forecast_method] NVARCHAR(24) NULL,
    [planning_version] NVARCHAR(24) NULL,
    CONSTRAINT PK_fact_material_demand_history PRIMARY KEY ([month_id],[material_id])
);
GO
CREATE TABLE pb.fact_purchase_order (
    [po_id] NVARCHAR(24) NOT NULL,
    [order_date] DATE NULL,
    [required_date] DATE NULL,
    [order_month] CHAR(7) NULL,
    [material_id] NVARCHAR(24) NULL,
    [supplier_id] NVARCHAR(24) NULL,
    [ordered_units] INT NULL,
    [unit_price_usd] DECIMAL(18,6) NULL,
    [currency] NVARCHAR(24) NULL,
    [incoterm] NVARCHAR(24) NULL,
    [po_status] NVARCHAR(24) NULL,
    [buyer_team] NVARCHAR(37) NULL,
    CONSTRAINT PK_fact_purchase_order PRIMARY KEY ([po_id])
);
GO
CREATE TABLE pb.fact_shipment (
    [shipment_id] NVARCHAR(24) NOT NULL,
    [po_id] NVARCHAR(24) NULL,
    [supplier_id] NVARCHAR(24) NULL,
    [material_id] NVARCHAR(24) NULL,
    [receipt_date] DATE NULL,
    [received_units] INT NULL,
    [on_time_flag] INT NULL,
    [days_late] NVARCHAR(24) NULL,
    [delivery_note] NVARCHAR(24) NULL,
    CONSTRAINT PK_fact_shipment PRIMARY KEY ([shipment_id])
);
GO
CREATE TABLE pb.fact_quality_inspection (
    [inspection_id] NVARCHAR(24) NOT NULL,
    [shipment_id] NVARCHAR(24) NULL,
    [inspection_date] DATE NULL,
    [inspected_units] INT NULL,
    [accepted_units] INT NULL,
    [rejected_units] INT NULL,
    [defect_ppm] DECIMAL(18,6) NULL,
    [inspection_result] NVARCHAR(24) NULL,
    [defect_type] NVARCHAR(32) NULL,
    CONSTRAINT PK_fact_quality_inspection PRIMARY KEY ([inspection_id])
);
GO
CREATE TABLE pb.fact_invoice (
    [invoice_id] NVARCHAR(24) NOT NULL,
    [po_id] NVARCHAR(24) NULL,
    [shipment_id] NVARCHAR(24) NULL,
    [invoice_date] DATE NULL,
    [invoiced_units] INT NULL,
    [unit_price_usd] DECIMAL(18,6) NULL,
    [material_amount_usd] DECIMAL(18,6) NULL,
    [freight_usd] DECIMAL(18,6) NULL,
    [duty_usd] DECIMAL(18,6) NULL,
    [total_landed_cost_usd] DECIMAL(18,6) NULL,
    [currency] NVARCHAR(24) NULL,
    CONSTRAINT PK_fact_invoice PRIMARY KEY ([invoice_id])
);
GO
CREATE TABLE pb.fact_payment (
    [payment_id] NVARCHAR(24) NOT NULL,
    [invoice_id] NVARCHAR(24) NULL,
    [payment_date] DATE NULL,
    [paid_amount_usd] DECIMAL(18,6) NULL,
    [payment_status] NVARCHAR(24) NULL,
    CONSTRAINT PK_fact_payment PRIMARY KEY ([payment_id])
);
GO
CREATE TABLE pb.fact_historical_capacity (
    [month_id] CHAR(7) NOT NULL,
    [supplier_id] NVARCHAR(24) NOT NULL,
    [material_id] NVARCHAR(24) NOT NULL,
    [available_capacity_units] INT NULL,
    [event_id] NVARCHAR(24) NULL,
    [capacity_basis] NVARCHAR(45) NULL,
    CONSTRAINT PK_fact_historical_capacity PRIMARY KEY ([month_id],[supplier_id],[material_id])
);
GO
CREATE TABLE pb.fact_risk_event (
    [event_id] NVARCHAR(24) NOT NULL,
    [begin_month] CHAR(7) NULL,
    [end_month] CHAR(7) NULL,
    [supplier_id] NVARCHAR(24) NULL,
    [disruption_type] NVARCHAR(34) NULL,
    [capacity_loss_pct] DECIMAL(18,6) NULL,
    [additional_lead_time_days] INT NULL,
    [impact_class] NVARCHAR(36) NULL,
    CONSTRAINT PK_fact_risk_event PRIMARY KEY ([event_id])
);
GO
CREATE TABLE pb.fact_future_demand (
    [month_id] CHAR(7) NOT NULL,
    [material_id] NVARCHAR(24) NOT NULL,
    [demand_units] INT NULL,
    [demand_type] NVARCHAR(29) NULL,
    [forecast_method] NVARCHAR(46) NULL,
    [planning_version] NVARCHAR(25) NULL,
    CONSTRAINT PK_fact_future_demand PRIMARY KEY ([month_id],[material_id])
);
GO
CREATE TABLE pb.fact_supplier_quote (
    [quote_id] NVARCHAR(24) NOT NULL,
    [plan_month] CHAR(7) NULL,
    [supplier_id] NVARCHAR(24) NULL,
    [material_id] NVARCHAR(24) NULL,
    [quoted_unit_price_usd] DECIMAL(18,6) NULL,
    [freight_usd_per_unit] DECIMAL(18,6) NULL,
    [duty_pct] DECIMAL(18,6) NULL,
    [minimum_order_qty_units] INT NULL,
    [maximum_capacity_units] INT NULL,
    [quoted_lead_time_days] INT NULL,
    [quote_valid_until] DATE NULL,
    [eligible_for_award] INT NULL,
    [currency] NVARCHAR(24) NULL,
    CONSTRAINT PK_fact_supplier_quote PRIMARY KEY ([quote_id])
);
GO
CREATE TABLE pb.fact_future_capacity (
    [plan_month] CHAR(7) NOT NULL,
    [supplier_id] NVARCHAR(24) NOT NULL,
    [material_id] NVARCHAR(24) NOT NULL,
    [normal_capacity_units] INT NULL,
    [stress_capacity_units] INT NULL,
    [scenario_name] NVARCHAR(36) NULL,
    CONSTRAINT PK_fact_future_capacity PRIMARY KEY ([plan_month],[supplier_id],[material_id])
);
GO
CREATE TABLE pb.fact_baseline_allocation (
    [plan_month] CHAR(7) NOT NULL,
    [material_id] NVARCHAR(24) NOT NULL,
    [supplier_id] NVARCHAR(24) NOT NULL,
    [allocated_units] INT NULL,
    [allocation_policy] NVARCHAR(55) NULL,
    [quote_id] NVARCHAR(24) NULL,
    [expected_landed_cost_usd] DECIMAL(18,6) NULL,
    CONSTRAINT PK_fact_baseline_allocation PRIMARY KEY ([plan_month],[material_id],[supplier_id])
);
GO
CREATE TABLE pb.dim_risk_assumptions (
    [supplier_id] NVARCHAR(24) NOT NULL,
    [monthly_disruption_probability] DECIMAL(18,6) NULL,
    [disruption_capacity_loss_min_pct] DECIMAL(18,6) NULL,
    [disruption_capacity_loss_max_pct] DECIMAL(18,6) NULL,
    [lead_time_std_days] INT NULL,
    [defect_rate_mean] DECIMAL(18,6) NULL,
    [defect_rate_std] DECIMAL(18,6) NULL,
    [price_volatility_std_pct] DECIMAL(18,6) NULL,
    [regional_correlation_group] NVARCHAR(24) NULL,
    [model_basis] NVARCHAR(42) NULL,
    CONSTRAINT PK_dim_risk_assumptions PRIMARY KEY ([supplier_id])
);
GO
CREATE TABLE pb.dim_cost_assumptions (
    [assumption_id] NVARCHAR(24) NOT NULL,
    [assumption_name] NVARCHAR(40) NULL,
    [assumption_value] DECIMAL(18,6) NULL,
    [unit] NVARCHAR(35) NULL,
    [definition] NVARCHAR(72) NULL,
    [source] NVARCHAR(28) NULL,
    CONSTRAINT PK_dim_cost_assumptions PRIMARY KEY ([assumption_id])
);
GO
CREATE TABLE pb.agg_po_delivery_scorecard (
    [po_id] NVARCHAR(24) NOT NULL,
    [month_id] CHAR(7) NULL,
    [supplier_id] NVARCHAR(24) NULL,
    [material_id] NVARCHAR(24) NULL,
    [ordered_units] INT NULL,
    [received_units] INT NULL,
    [on_time_received_units] INT NULL,
    [accepted_units] INT NULL,
    [rejected_units] INT NULL,
    [otif_po_flag] INT NULL,
    [any_on_time_receipt_flag] INT NULL,
    [otif_volume_pct] DECIMAL(18,6) NULL,
    [landed_cost_usd] DECIMAL(18,6) NULL,
    [quoted_price_to_reference] NVARCHAR(24) NULL,
    CONSTRAINT PK_agg_po_delivery_scorecard PRIMARY KEY ([po_id])
);
GO
CREATE TABLE pb.agg_supplier_scorecard (
    [supplier_id] NVARCHAR(24) NOT NULL,
    [supplier_name] NVARCHAR(37) NULL,
    [purchase_orders] NVARCHAR(24) NULL,
    [ordered_units] INT NULL,
    [received_units] INT NULL,
    [accepted_units] INT NULL,
    [spent_usd] DECIMAL(18,6) NULL,
    [on_time_volume_pct] DECIMAL(18,6) NULL,
    [po_otif_pct] DECIMAL(18,6) NULL,
    [defect_ppm] DECIMAL(18,6) NULL,
    [price_index_vs_sku_reference] NVARCHAR(24) NULL,
    [quality_score_100] DECIMAL(18,6) NULL,
    [delivery_score_100] DECIMAL(18,6) NULL,
    [cost_score_100] DECIMAL(18,6) NULL,
    [resilience_score_100] DECIMAL(18,6) NULL,
    [weighted_score_100] DECIMAL(18,6) NULL,
    CONSTRAINT PK_agg_supplier_scorecard PRIMARY KEY ([supplier_id])
);
GO
-- Optional FK checks (run after importing all CSV files)
ALTER TABLE pb.dim_material ADD CONSTRAINT FK_dim_material_category_id FOREIGN KEY ([category_id]) REFERENCES pb.dim_category([category_id]);
GO
ALTER TABLE pb.bridge_supplier_material ADD CONSTRAINT FK_bridge_supplier_material_supplier_id FOREIGN KEY ([supplier_id]) REFERENCES pb.dim_supplier([supplier_id]);
GO
ALTER TABLE pb.bridge_supplier_material ADD CONSTRAINT FK_bridge_supplier_material_material_id FOREIGN KEY ([material_id]) REFERENCES pb.dim_material([material_id]);
GO
ALTER TABLE pb.fact_purchase_order ADD CONSTRAINT FK_fact_purchase_order_supplier_id FOREIGN KEY ([supplier_id]) REFERENCES pb.dim_supplier([supplier_id]);
GO
ALTER TABLE pb.fact_purchase_order ADD CONSTRAINT FK_fact_purchase_order_material_id FOREIGN KEY ([material_id]) REFERENCES pb.dim_material([material_id]);
GO
ALTER TABLE pb.fact_shipment ADD CONSTRAINT FK_fact_shipment_po_id FOREIGN KEY ([po_id]) REFERENCES pb.fact_purchase_order([po_id]);
GO
ALTER TABLE pb.fact_quality_inspection ADD CONSTRAINT FK_fact_quality_inspection_shipment_id FOREIGN KEY ([shipment_id]) REFERENCES pb.fact_shipment([shipment_id]);
GO
ALTER TABLE pb.fact_invoice ADD CONSTRAINT FK_fact_invoice_shipment_id FOREIGN KEY ([shipment_id]) REFERENCES pb.fact_shipment([shipment_id]);
GO
ALTER TABLE pb.fact_payment ADD CONSTRAINT FK_fact_payment_invoice_id FOREIGN KEY ([invoice_id]) REFERENCES pb.fact_invoice([invoice_id]);
GO
ALTER TABLE pb.fact_risk_event ADD CONSTRAINT FK_fact_risk_event_supplier_id FOREIGN KEY ([supplier_id]) REFERENCES pb.dim_supplier([supplier_id]);
GO
ALTER TABLE pb.fact_supplier_quote ADD CONSTRAINT FK_fact_supplier_quote_supplier_id FOREIGN KEY ([supplier_id]) REFERENCES pb.dim_supplier([supplier_id]);
GO
ALTER TABLE pb.fact_supplier_quote ADD CONSTRAINT FK_fact_supplier_quote_material_id FOREIGN KEY ([material_id]) REFERENCES pb.dim_material([material_id]);
GO