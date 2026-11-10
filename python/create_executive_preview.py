from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.io import to_html
R=Path(__file__).resolve().parents[1];T=R/'tableau';O=R/'outputs'
s=pd.read_csv(T/'scenario_comparison.csv');a=pd.read_csv(T/'allocation_all_policies.csv');h=pd.read_csv(T/'mc_shortfall_histogram.csv')
sel=s[s.scenario_id.isin(['BASE_GREEDY','BASE_GREEDY_14D','COST_FULL_14D','RISK70_10D','RISK70_14D','RISK60_14D'])].copy()
fig1=px.scatter(s,x='deterministic_policy_cost_usd',y='mc_expected_on_time_accepted_pct',text='scenario_id',size='mc_expected_at_risk_units',
 hover_data=['planned_unallocated_units','mc_mean_risk_adjusted_total_usd','mc_prob_on_time_accepted_ge_95pct','buffer_high_days'],
 title='Sourcing policies: cash cost vs modeled on-time accepted supply',labels={'deterministic_policy_cost_usd':'Policy cash cost (USD)','mc_expected_on_time_accepted_pct':'Modeled on-time accepted supply (%)'})
fig1.update_traces(textposition='top center',marker=dict(opacity=.66))
fig1.update_layout(height=460,margin=dict(l=60,r=30,t=70,b=70))
fig2=go.Figure()
for col,label in [('landed_purchase_cost_usd','Landed purchase'),('early_order_carrying_cost_usd','Early ordering carry'),('supplier_activation_cost_usd','Activation/setup'),('mc_mean_service_loss_usd','Assumed service-loss risk')]:
 fig2.add_bar(x=sel.scenario_id,y=sel[col],name=label)
fig2.update_layout(title='Risk-adjusted cost composition (USD; risk penalty is not cash)',barmode='stack',height=430,margin=dict(l=55,r=20,t=75,b=90),xaxis_tickangle=-35,yaxis_title='USD')
chosen=a[a.scenario_id.eq('RISK60_14D')].groupby(['material_id','supplier_id'],as_index=False).allocated_units.sum()
piv=chosen.pivot(index='material_id',columns='supplier_id',values='allocated_units').fillna(0)
fig3=px.imshow(piv,aspect='auto',text_auto='.0f',title='Recommended six-month volume by material × supplier (units)',labels={'x':'Supplier','y':'Material','color':'Units'})
fig3.update_layout(height=500,margin=dict(l=55,r=25,t=80,b=70));fig3.update_traces(textfont_size=9)
mini=h[h.scenario_id.isin(['BASE_GREEDY','BASE_GREEDY_14D','RISK60_14D'])]
fig4=px.line(mini,x='shortfall_bin_mid_units',y='simulation_probability_pct',color='scenario_id',title='Simulated six-month on-time shortfall: distribution by policy',labels={'shortfall_bin_mid_units':'Material units not available on time','simulation_probability_pct':'Probability per histogram bin (%)'})
fig4.update_layout(height=440,margin=dict(l=55,r=20,t=75,b=65))
forms=[fig1,fig2,fig3,fig4]
sections=[]
for k,f in enumerate(forms):
 sections.append('<section class="chart">'+to_html(f,include_plotlyjs=(True if k==0 else False),full_html=False,config={'displaylogo':False,'responsive':True})+'</section>')
w=s.set_index('scenario_id').loc['RISK60_14D'];base=s.set_index('scenario_id').loc['BASE_GREEDY'];b14=s.set_index('scenario_id').loc['BASE_GREEDY_14D']
head=f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Project B | Sourcing Decision Preview</title><style>
body{{font-family:Arial,Helvetica,sans-serif;background:#f4f6f8;color:#17222b;max-width:1380px;margin:auto;padding:22px}}header{{margin:14px 0 22px}}h1{{font-size:29px;margin:0 0 9px}}h2{{font-size:19px}}.sub{{color:#596775;font-size:14px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}}.card{{background:#fff;padding:19px;border-radius:13px;border:1px solid #e1e7eb}}.v{{font-size:27px;font-weight:700;margin:8px 0}}.label{{font-size:13px;color:#596775}}.chart{{background:#fff;border:1px solid #e1e7eb;border-radius:13px;margin-top:15px;padding:6px}}.note{{margin:20px 0;padding:15px;background:#fff;border-left:3px solid #8595a5;font-size:14px;line-height:1.65}}a{{color:#245f99}}@media(max-width:750px){{body{{padding:10px}}}}</style></head><body><header><p class="sub">PROJECT B / 2026 • 100% SYNTHETIC DATA</p><h1>Supplier Selection, Performance & Procurement Risk</h1><p class="sub">Exploratory preview for Tableau build. These are simulated scenarios, not real supplier awards or verified financial savings.</p></header>
<div class="cards"><div class="card"><div class="label">Recommended tested policy</div><div class="v">RISK60_14D</div><div class="sub">60% max supplier / 14-day buffer</div></div>
<div class="card"><div class="label">Planned allocation coverage</div><div class="v">100%</div><div class="sub">126,708/126,708 units</div></div>
<div class="card"><div class="label">Modeled on-time accepted</div><div class="v">{w.mc_expected_on_time_accepted_pct:.2f}%</div><div class="sub">vs {base.mc_expected_on_time_accepted_pct:.2f}% at baseline</div></div>
<div class="card"><div class="label">Risk-adjusted expected total</div><div class="v">${w.mc_mean_risk_adjusted_total_usd/1e6:.2f}M</div><div class="sub">−{w.risk_adjusted_savings_vs_greedy_pct:.2f}% vs original modeled baseline</div></div></div>
<div class="note"><strong>Critical interpretation:</strong> The direct sourcing/holding/setup cost <strong>increases by ${w.incremental_policy_cost_vs_greedy_usd:,.0f}</strong>. Risk-adjusted cost is lower only after applying hypothetical service-loss opportunity costs ($120 per high-critical and $60 per medium-critical affected unit). Most performance improvement is lead-time buffer: original greedy allocation with the same 14-day buffer achieves {b14.mc_expected_on_time_accepted_pct:.2f}%.</div>'''
footer='''<div class="note">For Tableau Desktop, use separate scenario-, monthly-, allocation- and Monte-Carlo-grain CSV files from the accompanying package. Full instructions: <code>docs/TABLEAU_STEP_BY_STEP_VI.md</code>. All statements are outputs from reproducible Python Monte Carlo (3,000 common draws) under fictional inputs.</div></body></html>'''
(R/'Project_B_Executive_Dashboard_Preview.html').write_text(head+'\n'.join(sections)+footer,encoding='utf-8')
print((R/'Project_B_Executive_Dashboard_Preview.html').stat().st_size)
