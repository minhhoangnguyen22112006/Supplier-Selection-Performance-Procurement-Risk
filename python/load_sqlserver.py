"""Run the full SQL DDL first; Python loads tables in dependency order."""
from pathlib import Path
import csv,pyodbc
ROOT=Path(__file__).resolve().parents[1]
# CHANGE this to your SSMS SQL Server instance; set Trusted_Connection=yes or your auth.
CONN_STR=r"DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=SupplierManagementB;Trusted_Connection=yes;TrustServerCertificate=yes"
TABLES=['dim_category', 'dim_material', 'dim_supplier', 'bridge_supplier_material', 'fact_material_demand_history', 'fact_purchase_order', 'fact_shipment', 'fact_quality_inspection', 'fact_invoice', 'fact_payment', 'fact_historical_capacity', 'fact_risk_event', 'fact_future_demand', 'fact_supplier_quote', 'fact_future_capacity', 'fact_baseline_allocation', 'dim_risk_assumptions', 'dim_cost_assumptions', 'agg_po_delivery_scorecard', 'agg_supplier_scorecard']
cn=pyodbc.connect(CONN_STR)
cur=cn.cursor();cur.fast_executemany=True
for table in TABLES:
    with (ROOT/'data'/f'{table}.csv').open(encoding='utf-8-sig',newline='') as f:
        data=list(csv.DictReader(f));cols=list(data[0]);vals=[[r[c] if r[c]!='' else None for c in cols] for r in data]
    q=f"INSERT INTO pb.{table} ("+','.join('['+c+']' for c in cols)+") VALUES ("+','.join('?' for _ in cols)+")"
    for i in range(0,len(vals),400):cur.executemany(q,vals[i:i+400])
    cn.commit();print(table,len(vals))
cn.close()
print('Import done. SQL Server pb schema is ready.')
