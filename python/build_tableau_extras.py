from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1];D=R/'data';T=R/'tableau'
q=pd.read_csv(D/'fact_supplier_quote.csv');m=pd.read_csv(D/'dim_material.csv');s=pd.read_csv(D/'dim_supplier.csv');cats=pd.read_csv(D/'dim_category.csv');sc=pd.read_csv(T/'scenario_comparison.csv')
q['unit_landed_cost_usd']=(q.quoted_unit_price_usd*(1+q.duty_pct)+q.freight_usd_per_unit).round(4)
q=q.merge(m[['material_id','material_name','criticality','category_id']],on='material_id',validate='many_to_one').merge(s[['supplier_id','supplier_name','region']],on='supplier_id',validate='many_to_one')
q.to_csv(T/'rfq_unit_economics.csv',index=False)
cats.to_csv(T/'kraljic_category.csv',index=False)
# long form avoids Tableau parameter reshaping: one cost segment per scenario
segments=[('landed_purchase_cost_usd','Landed purchase','modeled cash'),('early_order_carrying_cost_usd','Early-order carrying','modeled cash'),('supplier_activation_cost_usd','Supplier activation','modeled cash'),('mc_mean_service_loss_usd','Expected service loss','modeled opportunity cost')]
records=[]
for r in sc.itertuples():
 for k,label,kind in segments:
  records.append({'scenario_id':r.scenario_id,'cost_component':label,'economic_type':kind,'amount_usd':getattr(r,k),'is_recommended':r.is_recommended})
pd.DataFrame(records).to_csv(T/'scenario_cost_breakdown_long.csv',index=False)
# Reproducing historical landed spend at material+supplier level without PO/shipment join fanout.
p=pd.read_csv(D/'fact_purchase_order.csv'); inv=pd.read_csv(D/'fact_invoice.csv')
sp=inv.groupby('po_id',as_index=False).total_landed_cost_usd.sum().merge(p[['po_id','supplier_id','material_id']],on='po_id',validate='one_to_one')
sp=sp.merge(m[['material_id','material_name','category_id']],on='material_id').merge(cats[['category_id','category_name','kraljic_quadrant']],on='category_id')
sp=sp.groupby(['supplier_id','material_id','material_name','category_name','kraljic_quadrant'],as_index=False).total_landed_cost_usd.sum()
sp=sp.merge(s[['supplier_id','supplier_name']],on='supplier_id');sp.to_csv(T/'historical_spend_by_supplier_material.csv',index=False)
print('Extras generated')
