"""Optional: import final model outputs into SQL Server and connect Tableau via SQL views.
Run after schema & base data load. Requires pyodbc and ODBC Driver 18.
CAUTION: replaces only pb.b_decision_* reporting tables; does not drop original facts.
"""
import csv
from pathlib import Path
import pyodbc
ROOT=Path(__file__).resolve().parents[1]
CONN_STR=r'DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=SupplierManagementB;Trusted_Connection=yes;TrustServerCertificate=yes'
# Name, input CSV, schema in SQL Server; record counts are validated on load.
TABLES={
 'b_decision_scenario_summary': ('outputs/scenario_comparison.csv', {
    'scenario_id':'NVARCHAR(32)', 'scenario_name':'NVARCHAR(90)','planned_demand_units':'INT',
    'planned_allocated_units':'INT','planned_unallocated_units':'INT','planned_coverage_pct':'FLOAT',
    'landed_purchase_cost_usd':'FLOAT','early_order_carrying_cost_usd':'FLOAT','supplier_activation_cost_usd':'FLOAT',
    'deterministic_policy_cost_usd':'FLOAT','mc_mean_on_time_accepted_units':'FLOAT','mc_expected_at_risk_units':'FLOAT',
    'mc_expected_on_time_accepted_pct':'FLOAT','mc_p95_shortfall_units':'FLOAT',
    'mc_prob_on_time_accepted_ge_95pct':'FLOAT','mc_prob_on_time_accepted_ge_98pct':'FLOAT',
    'mc_mean_service_loss_usd':'FLOAT','mc_mean_risk_adjusted_total_usd':'FLOAT',
    'mc_p95_risk_adjusted_total_usd':'FLOAT','active_suppliers':'INT','min_sources_per_sku_month':'INT',
    'max_supplier_share_per_sku_month_pct':'FLOAT','buffer_high_days':'INT','buffer_medium_days':'INT',
    'supplier_share_policy_cap_pct':'FLOAT','risk_weight_in_optimization':'INT',
    'source_data':'NVARCHAR(180)','is_recommended':'INT',
    'risk_adjusted_savings_vs_greedy_usd':'FLOAT','risk_adjusted_savings_vs_greedy_pct':'FLOAT',
    'incremental_policy_cost_vs_greedy_usd':'FLOAT','expected_shortfall_reduction_vs_greedy_pct':'FLOAT',
    'expected_service_improvement_vs_greedy_pp':'FLOAT'
 }),
 'b_decision_allocation': ('outputs/allocation_all_policies.csv', {
    'scenario_id':'NVARCHAR(32)','plan_month':'CHAR(7)','material_id':'NVARCHAR(24)',
    'material_name':'NVARCHAR(80)','criticality':'NVARCHAR(12)','supplier_id':'NVARCHAR(24)',
    'supplier_name':'NVARCHAR(100)','supplier_region':'NVARCHAR(40)',
    'allocated_units':'INT','demand_units':'INT','share_sku_month_pct':'FLOAT',
    'unit_landed_cost_usd':'FLOAT','landed_cost_usd':'FLOAT','carrying_cost_usd':'FLOAT',
    'buffer_days':'INT','moq_units':'INT','normal_capacity_units':'INT','capacity_load_pct':'FLOAT',
    'data_source':'NVARCHAR(50)'
 }),
}
conn=pyodbc.connect(CONN_STR);cur=conn.cursor();cur.fast_executemany=True
for table,(rel,types) in TABLES.items():
    with (ROOT/rel).open(newline='',encoding='utf-8-sig') as f:
        data=list(csv.DictReader(f));cols=list(data[0]);assert set(cols)==set(types),(table,set(cols)-set(types),set(types)-set(cols))
    q=f'IF OBJECT_ID(\'pb.{table}\',\'U\') IS NOT NULL DROP TABLE pb.{table}; CREATE TABLE pb.{table} ('+', '.join(f'[{c}] {types[c]} NULL' for c in cols)+')'
    cur.execute(q);conn.commit()
    sql=f'INSERT INTO pb.{table} ('+', '.join(f'[{c}]' for c in cols)+') VALUES ('+', '.join('?' for _ in cols)+')'
    for k in range(0,len(data),400):
        cur.executemany(sql,[tuple(row[c] if row[c] not in ('',None) else None for c in cols) for row in data[k:k+400]])
    conn.commit();print(table,len(data))
cur.close();conn.close()
print('Now run sql/03_final_decision_views.sql to create views.')
