#!/usr/bin/env python3
"""Supplier Portfolio B: reproducible sourcing MILP and common-random-number Monte Carlo.
Run: python python/run_end_to_end.py
No external data fetched; original dataset is synthetic. Requires pandas, numpy, scipy.
"""
from __future__ import annotations
from pathlib import Path
import json, math, time
import numpy as np
import pandas as pd
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix
from scipy.stats import norm

ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data'; OUT=ROOT/'outputs'; TAB=ROOT/'tableau'
OUT.mkdir(exist_ok=True);TAB.mkdir(exist_ok=True)
SEED=20261109; DRAWS=3000
ONBOARD=1200.0; HOLD=0.015; BASE_BUFFER=4
PENALTY={'High':120.0,'Medium':60.0,'Low':30.0}
REGIONAL_PROB={'East Asia':0.012, 'Southeast Asia':0.009, 'Europe':0.006}
REGIONAL_LOSS_RANGE=(0.10,0.30); REGIONAL_EXTRA_LEAD=(1.0,4.0)

q=pd.read_csv(D/'fact_supplier_quote.csv');q=q[q.eligible_for_award.eq(1)].copy().sort_values(['plan_month','material_id','supplier_id']).reset_index(drop=True)
demand=pd.read_csv(D/'fact_future_demand.csv'); mats=pd.read_csv(D/'dim_material.csv'); sups=pd.read_csv(D/'dim_supplier.csv'); risks=pd.read_csv(D/'dim_risk_assumptions.csv'); hist_base=pd.read_csv(D/'fact_baseline_allocation.csv')
score=pd.read_csv(D/'agg_supplier_scorecard.csv')
months=sorted(demand.month_id.unique()); materials=sorted(demand.material_id.unique()); suppliers=sorted(sups.supplier_id.unique()); regions=sorted(risks.regional_correlation_group.unique());
month_id={k:v for v,k in enumerate(months)}; supplier_id={k:v for v,k in enumerate(suppliers)};region_id={k:v for v,k in enumerate(regions)}
keys=list(zip(demand.month_id, demand.material_id)); keys.sort(); keys_id={k:i for i,k in enumerate(keys)}; demands=dict(zip(zip(demand.month_id,demand.material_id),demand.demand_units))
critical=dict(zip(mats.material_id,mats.criticality));mat_name=dict(zip(mats.material_id,mats.material_name)); sup_name=dict(zip(sups.supplier_id,sups.supplier_name))
q['key']=[(m,k) for m,k in zip(q.plan_month,q.material_id)]
q['key_idx']=q.key.map(keys_id);q['month_idx']=q.plan_month.map(month_id);q['supplier_idx']=q.supplier_id.map(supplier_id)
q['landed_unit']=q.quoted_unit_price_usd*(1+q.duty_pct)+q.freight_usd_per_unit
q['penalty']=q.material_id.map(lambda k:PENALTY[critical[k]])
q=q.merge(risks.drop(columns=['model_basis']),on='supplier_id',validate='many_to_one')
q['region_idx']=q.regional_correlation_group.map(region_id)
q['row_capacity']=q.maximum_capacity_units.astype(int)
N=len(q);K=len(keys);S=len(suppliers);assert N==240 and K==60
key_rows={k:np.flatnonzero(q.key_idx.to_numpy()==j) for k,j in keys_id.items()}
supplier_rows={s:np.flatnonzero(q.supplier_idx.to_numpy()==j) for s,j in supplier_id.items()}
key_demand=np.array([demands[k] for k in keys],dtype=int)

# All experimental policies are explicit; baseline from supplied synthetic file is unchanged.
POLICIES=[
 {'id':'BASE_GREEDY','label':'S0 • Greedy historical benchmark','mode':'baseline','share':None,'dual':False,'risk_weight':0,'buffer_high':4,'buffer_medium':4},
 {'id':'BASE_GREEDY_14D','label':'S0b • Greedy with +14-day buffer','mode':'baseline','share':None,'dual':False,'risk_weight':0,'buffer_high':14,'buffer_medium':14},
 {'id':'COST_FULL','label':'S1 • Minimum cost, full demand','mode':'opt','share':None,'dual':False,'risk_weight':0,'buffer_high':4,'buffer_medium':4},
 {'id':'COST_FULL_14D','label':'S1b • Minimum cost, +14-day buffer','mode':'opt','share':None,'dual':False,'risk_weight':0,'buffer_high':14,'buffer_medium':14},
 {'id':'DUAL70_4D','label':'S2 • Dual source 70%, +4-day buffer','mode':'opt','share':0.70,'dual':True,'risk_weight':0,'buffer_high':4,'buffer_medium':4},
 {'id':'DUAL70_14D','label':'S2b • Dual source 70%, +14-day buffer','mode':'opt','share':0.70,'dual':True,'risk_weight':0,'buffer_high':14,'buffer_medium':14},
 {'id':'RISK70_4D','label':'S3 • Risk-aware 70%, +4 days','mode':'opt','share':0.70,'dual':True,'risk_weight':1,'buffer_high':4,'buffer_medium':4},
 {'id':'RISK70_10D','label':'S4 • Risk-aware 70%, +10 days','mode':'opt','share':0.70,'dual':True,'risk_weight':1,'buffer_high':10,'buffer_medium':10},
 {'id':'RISK70_14D','label':'S5 • Risk-aware 70%, +14 days','mode':'opt','share':0.70,'dual':True,'risk_weight':1,'buffer_high':14,'buffer_medium':14},
 {'id':'RISK70_SELECT','label':'S6 • Selective buffer 14/10 days','mode':'opt','share':0.70,'dual':True,'risk_weight':1,'buffer_high':14,'buffer_medium':10},
 {'id':'RISK60_14D','label':'S7 • Diversified 60%, +14 days','mode':'opt','share':0.60,'dual':True,'risk_weight':1,'buffer_high':14,'buffer_medium':14},
]

def bufs(policy):
    return q.material_id.map(lambda k:policy['buffer_high'] if critical[k]=='High' else policy['buffer_medium']).to_numpy(dtype=float)

def calc_unit_cost(policy):
    buffer=bufs(policy)
    # marginal holding cost for order placement earlier than the 4-day reference policy
    carry=q.landed_unit.to_numpy()*HOLD*np.maximum(buffer-BASE_BUFFER,0.0)/30.0
    approx_disc=q.monthly_disruption_probability.to_numpy()*0.35*0.75
    p_late=norm.sf(buffer/q.lead_time_std_days.to_numpy())
    failure_proxy=1-(1-p_late)*(1-approx_disc)*(1-q.defect_rate_mean.to_numpy())
    risk=q.penalty.to_numpy()*failure_proxy*policy['risk_weight']
    return q.landed_unit.to_numpy()+carry+risk,carry,failure_proxy

def optimize(policy):
    # Layout [integer allocated N][binary bid active N][binary supplier active S].
    # Nonnegative exact-demand allocation, bid-level MOQ and capacity; optional source share and dual rule.
    # A supplier onboarding charge is applied only once per horizon if any awarded quote is used.
    cost,carry,failure_proxy=calc_unit_cost(policy)
    c=np.r_[cost, np.zeros(N),np.full(S,ONBOARD)]
    integral=np.ones(2*N+S,dtype=int)
    upper=np.r_[np.full(N,np.inf),np.ones(N+S)]
    lower=np.zeros(2*N+S)
    nrow=K+3*N+(K if policy['dual'] else 0)
    A=lil_matrix((nrow,2*N+S),dtype=float)
    lb=np.full(nrow,-np.inf);ub=np.full(nrow,np.inf)
    # Demand equality
    for j, key in enumerate(keys):
        A[j,key_rows[key]]=1;lb[j]=ub[j]=demands[key]
    for i,row in q.iterrows():
        cap=int(row.row_capacity)
        if policy['share'] is not None:cap=min(cap,int(math.floor(demands[row.key]*policy['share']+1e-7)))
        # x<=cap*y
        A[K+i,i]=1;A[K+i,N+i]=-cap;ub[K+i]=0
        # x>=moq*y
        A[K+N+i,i]=-1;A[K+N+i,N+i]=int(row.minimum_order_qty_units);ub[K+N+i]=0
        # y<=z
        A[K+2*N+i,N+i]=1;A[K+2*N+i,2*N+int(row.supplier_idx)]=-1;ub[K+2*N+i]=0
    if policy['dual']:
        for j,key in enumerate(keys):
            A[K+3*N+j,N+key_rows[key]]=1;lb[K+3*N+j]=2
    result=milp(c,integrality=integral,bounds=Bounds(lower,upper),constraints=LinearConstraint(A.tocsr(),lb,ub),options={'time_limit':100,'mip_rel_gap':0.0005})
    if result.x is None:raise RuntimeError(f'{policy["id"]}: MILP failed {result.message}')
    vals=np.rint(result.x[:N]).astype(int);y=np.rint(result.x[N:2*N]).astype(int)
    if np.any(np.abs(result.x[:N]-vals)>0.01):raise AssertionError('noninteger units')
    assert np.all(np.bincount(q.key_idx,weights=vals,minlength=K)==key_demand),policy['id']
    assert np.all(vals<=q.row_capacity) and np.all((vals==0) | (vals>=q.minimum_order_qty_units))
    if policy['share'] is not None:
        assert np.all(vals<=np.floor(q.key.map(demands).to_numpy()*policy['share']+1e-7))
    if policy['dual']:
        assert min(sum(vals[idx]>0) for idx in key_rows.values())>=2
    return vals,{'solver_status':result.message,'solver_obj_internal':float(result.fun),'mip_gap':float(getattr(result,'mip_gap',np.nan))}

b=hist_base[hist_base.supplier_id!='UNALLOCATED'].copy()
baseline_map={(r.plan_month,r.material_id,r.supplier_id):int(r.allocated_units) for r in b.itertuples()}
ALLOC={};META={}
for p in POLICIES:
    if p['mode']=='baseline':
        vals=np.array([baseline_map.get((r.plan_month,r.material_id,r.supplier_id),0) for r in q.itertuples()],dtype=int)
        META[p['id']]={'solver_status':'Original greedy benchmark','solver_obj_internal':None,'mip_gap':None}
        assert np.all(np.bincount(q.key_idx,weights=vals,minlength=K)<=key_demand)
    else:
        vals,META[p['id']]=optimize(p)
    ALLOC[p['id']]=vals
    print('SOLVED',p['id'],'allocated',vals.sum(),'landed',round(float(vals@q.landed_unit.to_numpy()),2),'suppliers',len(set(q.loc[vals>0,'supplier_id'])),flush=True)

# MC common random numbers: each policy sees identical supplier/month and region/month shocks.
rng=np.random.default_rng(SEED)
region_to_sup=np.array([region_id[r] for r in risks.sort_values('supplier_id').regional_correlation_group])
risk_by_sup=risks.set_index('supplier_id').loc[suppliers]
prob=risk_by_sup.monthly_disruption_probability.to_numpy()
lead_std=risk_by_sup.lead_time_std_days.to_numpy()
defect_mean=risk_by_sup.defect_rate_mean.to_numpy()
defect_std=risk_by_sup.defect_rate_std.to_numpy()
reg_probs=np.array([REGIONAL_PROB[r] for r in regions])
regional_active=rng.random((DRAWS,len(months),len(regions))) < reg_probs[None,None,:]
regional_loss=rng.uniform(*REGIONAL_LOSS_RANGE,size=regional_active.shape)*regional_active
regional_lead=rng.uniform(*REGIONAL_EXTRA_LEAD,size=regional_active.shape)*regional_active
idio_active=rng.random((DRAWS,len(months),S))<prob[None,None,:]
idio_loss=rng.uniform(0.15,0.55,size=idio_active.shape)*idio_active
lead_jitter=rng.normal(0,lead_std[None,None,:],size=(DRAWS,len(months),S))
defect=np.clip(rng.normal(defect_mean[None,None,:],defect_std[None,None,:],size=(DRAWS,len(months),S)),0,0.10)
combined_capacity_loss=1-(1-idio_loss)*(1-regional_loss[:,:,region_to_sup])
combined_lead=lead_jitter+regional_lead[:,:,region_to_sup]
mi=q.month_idx.to_numpy(dtype=int);si=q.supplier_idx.to_numpy(dtype=int);ri=q.region_idx.to_numpy(dtype=int);ki=q.key_idx.to_numpy(dtype=int)
cap=q.row_capacity.to_numpy(dtype=int)
Q=q.landed_unit.to_numpy(dtype=float);pener=np.array([PENALTY[critical[m]] for mm,m in keys])
# Per draw x material/month expected shortfall by matrix operations; use deterministic row-level key mapping
key_mat=np.zeros((N,K),dtype=np.float64);key_mat[np.arange(N),ki]=1
all_records=[];alloc_records=[];monthly_rows=[];supplier_rows=[];sku_rows=[];hist_rows=[];policy_matrix=[];risk_draws={}
for p in POLICIES:
    pid=p['id']; x=ALLOC[pid]; buffer=bufs(p)
    total_demand=int(key_demand.sum());allocated=int(x.sum());nom_unallocated=total_demand-allocated
    landed=float(x@Q)
    carrying=float(x@(Q*HOLD*np.maximum(buffer-BASE_BUFFER,0)/30.0))
    active_suppliers=sorted(q.loc[x>0,'supplier_id'].unique());onboarding=len(active_suppliers)*ONBOARD
    max_share=0.0
    source_counts=[]
    for j,key in enumerate(keys):
        idx=key_rows[key];own=x[idx];source_counts.append(int((own>0).sum()));max_share=max(max_share,float(own.max()/demands[key]))
    # Each allocation cannot deliver more than scenario realized physical capacity.
    available=np.floor(cap[None,:]*(1-combined_capacity_loss[:,mi,si])+1e-9)
    available=np.maximum(available,0)
    physically_received=np.minimum(x[None,:],available)
    timely=combined_lead[:,mi,si] <= buffer[None,:]
    on_time_good=physically_received*timely*(1-defect[:,mi,si]);
    delivered_by_key=on_time_good@key_mat
    shortage=np.maximum(0,key_demand[None,:]-delivered_by_key)
    short_units=shortage.sum(axis=1)
    timely_rate=(total_demand-short_units)/total_demand
    shortage_cost=shortage@pener
    policy_cost=landed+carrying+onboarding
    risk_adjusted=policy_cost+shortage_cost
    risk_draws[pid]=risk_adjusted
    p95_short=float(np.quantile(short_units,0.95));
    summary={
        'scenario_id':pid,'scenario_name':p['label'],'planned_demand_units':total_demand,
        'planned_allocated_units':allocated,'planned_unallocated_units':nom_unallocated,
        'planned_coverage_pct':100*allocated/total_demand,
        'landed_purchase_cost_usd':round(landed,2),'early_order_carrying_cost_usd':round(carrying,2),
        'supplier_activation_cost_usd':round(onboarding,2),'deterministic_policy_cost_usd':round(policy_cost,2),
        'mc_mean_on_time_accepted_units':round(float((total_demand-short_units).mean()),1),
        'mc_expected_at_risk_units':round(float(short_units.mean()),1),
        'mc_expected_on_time_accepted_pct':round(float(timely_rate.mean()*100),3),
        'mc_p95_shortfall_units':round(p95_short,1),
        'mc_prob_on_time_accepted_ge_95pct':round(float((timely_rate>=0.95).mean()*100),2),
        'mc_prob_on_time_accepted_ge_98pct':round(float((timely_rate>=0.98).mean()*100),2),
        'mc_mean_service_loss_usd':round(float(shortage_cost.mean()),2),
        'mc_mean_risk_adjusted_total_usd':round(float(risk_adjusted.mean()),2),
        'mc_p95_risk_adjusted_total_usd':round(float(np.quantile(risk_adjusted,0.95)),2),
        'active_suppliers':len(active_suppliers),'min_sources_per_sku_month':min(source_counts),
        'max_supplier_share_per_sku_month_pct':round(100*max_share,2),
        'buffer_high_days':int(p['buffer_high']),'buffer_medium_days':int(p['buffer_medium']),
        'supplier_share_policy_cap_pct':None if p['share'] is None else int(100*p['share']),
        'risk_weight_in_optimization':p['risk_weight'],
        'source_data':'100% synthetic; MC 3000 draws; scenarios evaluated on common draws'
    }
    all_records.append(summary)
    # Tableau row allocation: complete 240 per policy, include price and cost, scorecard.
    for i,r in enumerate(q.itertuples()):
        if x[i]<=0:continue
        alloc_records.append({'scenario_id':pid,'plan_month':r.plan_month,'material_id':r.material_id,
          'material_name':mat_name[r.material_id],'criticality':critical[r.material_id],
          'supplier_id':r.supplier_id,'supplier_name':sup_name[r.supplier_id],'supplier_region':r.regional_correlation_group,
          'allocated_units':int(x[i]),'demand_units':int(demands[r.key]),'share_sku_month_pct':round(100*x[i]/demands[r.key],3),
          'unit_landed_cost_usd':round(float(Q[i]),4),'landed_cost_usd':round(float(x[i]*Q[i]),2),
          'carrying_cost_usd':round(float(x[i]*Q[i]*HOLD*max(0,buffer[i]-BASE_BUFFER)/30),2),
          'buffer_days':int(buffer[i]),'moq_units':int(r.minimum_order_qty_units),
          'normal_capacity_units':int(r.row_capacity),
          'capacity_load_pct':round(100*x[i]/r.row_capacity,2),'data_source':'Synthetic allocation output'})
    for j,(month,mat) in enumerate(keys):
        sku_rows.append({'scenario_id':pid,'plan_month':month,'material_id':mat,'material_name':mat_name[mat],
          'criticality':critical[mat],'demand_units':int(key_demand[j]),
          'planned_allocated_units':int(x[key_rows[(month,mat)]].sum()),
          'expected_shortfall_units':round(float(shortage[:,j].mean()),2),
          'expected_on_time_accepted_pct':round(float((1-shortage[:,j]/key_demand[j]).mean()*100),2),
          'prob_any_shortfall_pct':round(float((shortage[:,j]>0).mean()*100),2),
          'p95_shortfall_units':round(float(np.quantile(shortage[:,j],.95)),1)})
    for m, month in enumerate(months):
        mat_idxs=[j for j,k in enumerate(keys) if k[0]==month]; ds=key_demand[mat_idxs].sum(); ms=shortage[:,mat_idxs].sum(axis=1)
        rows=q.month_idx.to_numpy()==m
        monthly_rows.append({'scenario_id':pid,'plan_month':month,'demand_units':int(ds),'allocated_units':int(x[rows].sum()),
          'landed_cost_usd':round(float(x[rows]@Q[rows]),2),
          'expected_shortfall_units':round(float(ms.mean()),2),
          'expected_on_time_accepted_pct':round(float((1-ms/ds).mean()*100),3),
          'prob_monthly_shortfall_above_5pct':round(float((ms/ds>0.05).mean()*100),2)})
    # risk distribution output: 60 bins per policy and compact per-draw sample for independent Tableau reference
    hist,edges=np.histogram(short_units,bins=55,range=(0,max(1,max(short_units))))
    for k,cnt in enumerate(hist):
        hist_rows.append({'scenario_id':pid,'shortfall_bin_mid_units':round(float((edges[k]+edges[k+1])/2),1),
          'simulation_count':int(cnt),'simulation_probability_pct':round(float(100*cnt/DRAWS),3)})
    for s in suppliers:
        idx=q.supplier_id.eq(s).to_numpy();supplier_rows.append({'scenario_id':pid,'supplier_id':s,'supplier_name':sup_name[s],
          'allocated_units':int(x[idx].sum()),'supplier_share_of_total_pct':round(float(100*x[idx].sum()/total_demand),2),
          'landed_cost_usd':round(float(x[idx]@Q[idx]),2)})
    # 200 evenly-spaced simulations per scenario, allows Tableau risk exploration without huge files
    for ix in range(0,DRAWS,15):
        policy_matrix.append({'scenario_id':pid,'simulation_id':int(ix+1),'on_time_accepted_units':round(float(total_demand-short_units[ix]),1),
          'service_shortfall_units':round(float(short_units[ix]),1),'on_time_accepted_pct':round(float(timely_rate[ix]*100),3),
          'service_loss_cost_usd':round(float(shortage_cost[ix]),2),'risk_adjusted_total_usd':round(float(risk_adjusted[ix]),2)})
    print('SIM',pid,'mc service',round(summary['mc_expected_on_time_accepted_pct'],2),'risk adjusted',round(summary['mc_mean_risk_adjusted_total_usd']),flush=True)

summ=pd.DataFrame(all_records).sort_values('mc_mean_risk_adjusted_total_usd').reset_index(drop=True)
# The lowest mean simulated risk-adjusted total cost is selected within the stated candidate policies.
chosen=str(summ.iloc[0].scenario_id);base_summ=summ.set_index('scenario_id').loc['BASE_GREEDY'];winner=summ.iloc[0]
summ['is_recommended']=summ.scenario_id.eq(chosen).astype(int)
summ['risk_adjusted_savings_vs_greedy_usd']=round(base_summ.mc_mean_risk_adjusted_total_usd-summ.mc_mean_risk_adjusted_total_usd,2)
summ['risk_adjusted_savings_vs_greedy_pct']=round(100*(base_summ.mc_mean_risk_adjusted_total_usd-summ.mc_mean_risk_adjusted_total_usd)/base_summ.mc_mean_risk_adjusted_total_usd,3)
summ['incremental_policy_cost_vs_greedy_usd']=round(summ.deterministic_policy_cost_usd-base_summ.deterministic_policy_cost_usd,2)
summ['expected_shortfall_reduction_vs_greedy_pct']=round(100*(base_summ.mc_expected_at_risk_units-summ.mc_expected_at_risk_units)/base_summ.mc_expected_at_risk_units,3)
summ['expected_service_improvement_vs_greedy_pp']=round(summ.mc_expected_on_time_accepted_pct-base_summ.mc_expected_on_time_accepted_pct,3)

summ.to_csv(OUT/'scenario_comparison.csv',index=False);summ.to_csv(TAB/'scenario_comparison.csv',index=False)
pd.DataFrame(alloc_records).to_csv(OUT/'allocation_all_policies.csv',index=False);pd.DataFrame(alloc_records).to_csv(TAB/'allocation_all_policies.csv',index=False)
pd.DataFrame(monthly_rows).to_csv(TAB/'scenario_monthly.csv',index=False)
pd.DataFrame(sku_rows).to_csv(TAB/'sku_month_risk.csv',index=False)
pd.DataFrame(supplier_rows).to_csv(TAB/'scenario_supplier_exposure.csv',index=False)
pd.DataFrame(hist_rows).to_csv(TAB/'mc_shortfall_histogram.csv',index=False)
pd.DataFrame(policy_matrix).to_csv(TAB/'mc_sample_draws.csv',index=False)
# per material awarded suppliers, top allocation, backup source, six-month totals for recommendation
alloc=pd.DataFrame(alloc_records)
recommend=alloc[alloc.scenario_id.eq(chosen)].copy()
sku_supply=recommend.groupby(['material_id','material_name','criticality','supplier_id','supplier_name'],as_index=False).agg(allocated_units=('allocated_units','sum'),cost_usd=('landed_cost_usd','sum'))
mat_tot=sku_supply.groupby('material_id').allocated_units.sum().to_dict();sku_supply['material_supplier_share_pct']=(100*sku_supply.allocated_units/sku_supply.material_id.map(mat_tot)).round(2)
sku_supply=sku_supply.sort_values(['material_id','allocated_units'],ascending=[True,False]);sku_supply['source_priority']=sku_supply.groupby('material_id').cumcount()+1
sku_supply.to_csv(TAB/'recommended_supplier_by_material.csv',index=False)
# transparent economics by scenario and all criticality values
assumptions=[
 ('shortage_penalty_existing',8,'USD/unallocated unit/month','Original synthetic dataset assumption; NOT used to value production line stop in new risk-adjusted policy'),
 ('service_loss_high_critical',120,'USD/on-time unaccepted unit','New scenario assumption for critical materials; opportunity cost, not actual booked cash'),
 ('service_loss_medium_critical',60,'USD/on-time unaccepted unit','New scenario assumption for medium-critical materials'),
 ('service_loss_low_critical',30,'USD/on-time unaccepted unit','Fallback assumption; current materials have none with Low criticality'),
 ('supplier_activation',ONBOARD,'USD/supplier/horizon','New sourcing plan setup/mobilization per distinct supplier awarded once in 6 months'),
 ('inventory_carrying',HOLD,'share of inventory value/month','Original dataset assumption; incremental buffer beyond 4 days only'),
 ('reference_advance_order',BASE_BUFFER,'days','Original synthetic dataset order lead buffer'),
 ('regional_monthly_shock_EastAsia',REGIONAL_PROB['East Asia'],'probability per month','New correlated Monte Carlo shock'),
 ('regional_monthly_shock_SoutheastAsia',REGIONAL_PROB['Southeast Asia'],'probability per month','New correlated Monte Carlo shock'),
 ('regional_monthly_shock_Europe',REGIONAL_PROB['Europe'],'probability per month','New correlated Monte Carlo shock'),
 ('regional_loss_min',REGIONAL_LOSS_RANGE[0],'fraction','New shared capacity loss range'),
 ('regional_loss_max',REGIONAL_LOSS_RANGE[1],'fraction','New shared capacity loss range'),
 ('supplier_idiosyncratic_shock','per-supplier dim_risk_assumptions','probability/month','Original dataset rates used unchanged'),
 ('idiosyncratic_loss_min',0.15,'fraction','Original dataset supplier disruption loss lower bound'),
 ('idiosyncratic_loss_max',0.55,'fraction','Original dataset supplier disruption loss upper bound'),
 ('lead_time_early_order_buffer','4/10/14 depending on policy','days','Synthetic planning policy; model includes stochastic supplier month lead time deviations'),
 ('risk_draws',DRAWS,'common Monte Carlo draws','Identical shocks across all eight policies'),
 ('risk_random_seed',SEED,'seed','Reproducibility'),
 ('milp_primary_objective','landed+carry+activation+risk-proxy','USD equivalent','Optimized with per-unit expected on-time service loss proxy; evaluated independently via MC'),
 ('risk_valuation_scope','service loss is production opportunity cost','classification','Risk-adjusted USD equivalent is not invoiced cash and not audited savings'),
]
ass=pd.DataFrame(assumptions,columns=['assumption_id','assumption_value','unit','definition']);ass.to_csv(OUT/'expanded_assumptions.csv',index=False);ass.to_csv(TAB/'expanded_assumptions.csv',index=False)
# Paired policy-comparison uncertainty on 3,000 identical stochastic experiments.
# Monte Carlo SE measures simulation error only; it does not quantify uncertainty in assumed input parameters.
paired=[]
for a, b_id in [('RISK60_14D','RISK70_14D'),('RISK60_14D','DUAL70_14D'),('RISK60_14D','COST_FULL_14D'),('RISK60_14D','BASE_GREEDY_14D'),('RISK60_14D','BASE_GREEDY')]:
    delta=risk_draws[b_id]-risk_draws[a]  # positive is model A saving vs model B
    avg=float(delta.mean()); se=float(delta.std(ddof=1)/np.sqrt(DRAWS))
    paired.append({'policy_a':a,'policy_b':b_id,'estimated_savings_a_vs_b_usd':round(avg,2),
                   'mc_standard_error_usd':round(se,2),
                   'mc_approx_95_ci_lower_usd':round(avg-1.96*se,2),
                   'mc_approx_95_ci_upper_usd':round(avg+1.96*se,2),
                   'sampling_draws':DRAWS})
pd.DataFrame(paired).to_csv(OUT/'paired_comparison_uncertainty.csv',index=False)
# Sensitivity: compare each fixed evaluated portfolio at multiple risk-valuation scales
sense=[]
for mult in [0,0.1,0.25,0.5,1.0,1.5,2.0]:
    tmp=summ.copy();tmp['sensitivity_expected_total_usd']=tmp.deterministic_policy_cost_usd+mult*tmp.mc_mean_service_loss_usd
    w=tmp.loc[tmp.sensitivity_expected_total_usd.idxmin(),'scenario_id']
    for r in tmp.itertuples():
        sense.append({'risk_penalty_multiplier':mult,'scenario_id':r.scenario_id,'expected_total_usd':round(r.sensitivity_expected_total_usd,2),'winner_at_multiplier':w,'is_winner':int(r.scenario_id==w)})
pd.DataFrame(sense).to_csv(TAB/'risk_penalty_sensitivity.csv',index=False)
# Technical verification
valid={
 'demand_units':int(key_demand.sum()), 'source_quotations':N,'month_material_pairs':K,
 'historical_purchase_orders':len(pd.read_csv(D/'fact_purchase_order.csv')),
 'monte_carlo_draws':DRAWS,
 'supplier_count':S,'policies_evaluated':len(POLICIES),
 'all_optimized_plans_cover_100pct':bool(all(ALLOC[p['id']].sum()==key_demand.sum() for p in POLICIES if p['mode']=='opt')),
 'optimizer_moq_and_capacity_checked':True,
 'baseline_unallocated_units':int(key_demand.sum()-ALLOC['BASE_GREEDY'].sum()),
 'risk_simulation_uses_common_random_numbers':True,
 'recommended_scenario':chosen,
 'simulation_provenance':'entirely synthetic, probabilistic scenarios are assumptions, not company actuals',
 'disclaimer':'on_time_accepted_pct is a simulated aggregate quantity service proxy; NOT historical supplier PO OTIF'
}
(OUT/'validation_report.json').write_text(json.dumps(valid,indent=2,ensure_ascii=False),encoding='utf-8')
(OUT/'model_run_meta.json').write_text(json.dumps({'scenario_metadata':META,'seed':SEED,'draws':DRAWS,'chosen':chosen},indent=2,ensure_ascii=False),encoding='utf-8')
print('\n======= RESULTS SORTED =======');print(summ[['scenario_id','deterministic_policy_cost_usd','mc_expected_at_risk_units','mc_expected_on_time_accepted_pct','mc_mean_risk_adjusted_total_usd','mc_prob_on_time_accepted_ge_95pct','mc_p95_shortfall_units','risk_adjusted_savings_vs_greedy_pct']].to_string(index=False));print('\nRECOMMENDED',chosen);print('\nTOP MATERIAL SOURCES');print(sku_supply[sku_supply.source_priority<=2][['material_id','supplier_id','material_supplier_share_pct','source_priority']].to_string(index=False));print('VERIFIED',valid)
