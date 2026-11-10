from pathlib import Path
import json
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[1];D=R/'data';T=R/'tableau';O=R/'outputs'
s=pd.read_csv(O/'scenario_comparison.csv');a=pd.read_csv(T/'allocation_all_policies.csv');q=pd.read_csv(D/'fact_supplier_quote.csv');d=pd.read_csv(D/'fact_future_demand.csv');score=pd.read_csv(D/'agg_supplier_scorecard.csv');
assert len(s)==11 and s.scenario_id.nunique()==11
assert len(score)==12 and len(pd.read_csv(D/'dim_material.csv'))==10
assert len(pd.read_csv(D/'fact_purchase_order.csv'))==784
assert len(q)==240 and len(d)==60 and d.demand_units.sum()==126708
assert s.is_recommended.sum()==1 and s.loc[s.is_recommended.eq(1),'scenario_id'].iloc[0]=='RISK60_14D'
assert (s['landed_purchase_cost_usd']+s['early_order_carrying_cost_usd']+s['supplier_activation_cost_usd']-s['deterministic_policy_cost_usd']).abs().max()<=0.02
assert (s['deterministic_policy_cost_usd']+s['mc_mean_service_loss_usd']-s['mc_mean_risk_adjusted_total_usd']).abs().max()<=0.02
for t,r in s.set_index('scenario_id').iterrows():
    tab=a[a.scenario_id==t]
    assert int(tab.allocated_units.sum())==r.planned_allocated_units
    if t not in ('BASE_GREEDY','BASE_GREEDY_14D'):
        assert r.planned_unallocated_units==0
        assert (tab.allocated_units>=tab.moq_units).all()
        assert (tab.allocated_units<=tab.normal_capacity_units).all()
    assert abs(r.mc_expected_on_time_accepted_pct-100*(r.planned_demand_units-r.mc_expected_at_risk_units)/r.planned_demand_units)<0.002
rec=a[a.scenario_id=='RISK60_14D']
assert (rec.share_sku_month_pct<=60.001).all()
assert rec.groupby(['plan_month','material_id']).supplier_id.nunique().min()>=2
assert rec.groupby(['plan_month','material_id']).allocated_units.sum().eq(d.set_index(['month_id','material_id']).demand_units).all() if False else True
real_d=d.rename(columns={'month_id':'plan_month'}).set_index(['plan_month','material_id']).demand_units
real_alloc=rec.groupby(['plan_month','material_id']).allocated_units.sum()
assert (real_alloc==real_d).all()
assert abs(float(s.loc[s.scenario_id=='BASE_GREEDY','planned_unallocated_units'].iloc[0])-963)<0.0001
assert len(pd.read_csv(T/'risk_penalty_sensitivity.csv'))==11*7
assert len(pd.read_csv(T/'recommended_supplier_by_material.csv'))>=20
assert (R/'Project_B_Executive_Dashboard_Preview.html').stat().st_size>100000
assert (R/'notebooks/Project_B_Study_and_Review.ipynb').exists()
print('VALIDATED: 11 policies, 12 suppliers, 10 materials, 784 POs, 240 quotes, 60 demand pairs, correct cost sums, material-month allocations, MOQ, capacity, cap and risk outputs')
