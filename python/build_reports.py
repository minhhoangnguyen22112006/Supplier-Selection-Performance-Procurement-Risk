from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1];O=R/'outputs';T=R/'tableau';docs=R/'docs'
s=pd.read_csv(O/'scenario_comparison.csv').set_index('scenario_id');sc=pd.read_csv(T/'recommended_supplier_by_material.csv');sens=pd.read_csv(T/'risk_penalty_sensitivity.csv');pair=pd.read_csv(O/'paired_comparison_uncertainty.csv');
f=lambda x:f'{x:,.0f}'; dollar=lambda x:'$'+f(x); pct=lambda x:f'{x:,.2f}%'
w=s.loc['RISK60_14D']; b=s.loc['BASE_GREEDY']; b14=s.loc['BASE_GREEDY_14D'];c14=s.loc['COST_FULL_14D'];r70=s.loc['RISK70_14D']

rows=[]
for i, g in sc.groupby('material_id',sort=True):
 top=g.sort_values('source_priority').head(3)
 label=', '.join(f"{r.supplier_id} {r.material_supplier_share_pct:.1f}%" for r in top.itertuples())
 rows.append(f'| {i} | {g.iloc[0].material_name} | {g.iloc[0].criticality} | {label} |')
mat_table='\n'.join(rows)
brief_scenarios=['BASE_GREEDY','BASE_GREEDY_14D','COST_FULL_14D','RISK70_10D','RISK70_14D','RISK60_14D']
rows=[]
for k in brief_scenarios:
 r=s.loc[k]
 rows.append(f"| {k} | {f(r.planned_unallocated_units)} | {dollar(r.deterministic_policy_cost_usd)} | {pct(r.mc_expected_on_time_accepted_pct)} | {f(r.mc_expected_at_risk_units)} | {dollar(r.mc_mean_risk_adjusted_total_usd)} |")
scenario_table='\n'.join(rows)
rr=sens[sens.is_winner.eq(1)]
sensitivity='\n'.join(f"| {x.risk_penalty_multiplier:.2f}× | {x.scenario_id} |" for x in rr.itertuples())

text=f'''# PROJECT B — FINAL SOURCING DECISION REPORT

**Supplier Selection, Performance & Procurement Risk | Synthetic electronics-component procurement | 2026**

## 1. Executive decision

**Recommended tested policy: `RISK60_14D`.** Place orders for the next six planning months using integer MILP allocations, approved supplier eligibility, quoted landed cost, MOQ/capacity, **60% maximum supplier share of each material-month**, and **at least two sources per material-month**. Place POs at the quoted supplier lead time **plus a 14-day planning buffer** before the hypothetical required receipt date. For each material/month, use the exact `tableau/allocation_all_policies.csv` purchase quantities filtered to `RISK60_14D`.

The recommendation is **best among 11 enumerated policies under explicitly synthetic economic/risk assumptions**, not a mathematically proven global stochastic optimum or a real-world recommendation to Apple.

### Measured results from 3,000 common Monte Carlo draws

- Plan **{f(w.planned_allocated_units)} of {f(w.planned_demand_units)} units = {w.planned_coverage_pct:.0f}% planned allocation**, versus {f(b.planned_unallocated_units)} unallocated in the greedy baseline. This is **planned coverage, not OTIF**.
- Expected simulated **on-time accepted material units: {f(w.mc_mean_on_time_accepted_units)}** or **{w.mc_expected_on_time_accepted_pct:.3f}% of demand**; baseline {b.mc_expected_on_time_accepted_pct:.3f}% (**+{w.mc_expected_service_improvement_vs_greedy_pp if 'mc_expected_service_improvement_vs_greedy_pp' in w else w.expected_service_improvement_vs_greedy_pp:.3f} percentage points**).
- Expected modeled **service shortfall: {w.mc_expected_at_risk_units:,.1f} units**, versus {b.mc_expected_at_risk_units:,.1f}; **{w.expected_shortfall_reduction_vs_greedy_pct:.2f}% reduction**. This includes late arrival and rejected units, not just unallocated purchase order quantities.
- **97.93%** of simulation draws achieved at least 95% total on-time accepted supply across the six months. P95 total service shortfall = **{w.mc_p95_shortfall_units:,.0f} units**.
- Deterministic six-month sourcing policy cost = **{dollar(w.deterministic_policy_cost_usd)}** (landed purchase **{dollar(w.landed_purchase_cost_usd)}**, incremental carrying **{dollar(w.early_order_carrying_cost_usd)}**, activation **{dollar(w.supplier_activation_cost_usd)}**). Baseline = **{dollar(b.deterministic_policy_cost_usd)}**, a policy cash-cost **increase of {dollar(w.incremental_policy_cost_vs_greedy_usd)}** (not procurement savings).
- Expected risk-adjusted total = **{dollar(w.mc_mean_risk_adjusted_total_usd)}**, versus **{dollar(b.mc_mean_risk_adjusted_total_usd)}** at baseline, **{w.risk_adjusted_savings_vs_greedy_pct:.3f}% lower**. This includes **hypothetical opportunity costs of late/missing production materials**, not realized accounting savings.

## 2. Fair attribution: what actually helped?

**Early PO release is the dominant lever.** With exactly the original greedy suppliers/quantities but a 14-day buffer, expected modeled service improves from **{b.mc_expected_on_time_accepted_pct:.3f}% to {b14.mc_expected_on_time_accepted_pct:.3f}%** and expected shortfall from {b.mc_expected_at_risk_units:,.1f} to {b14.mc_expected_at_risk_units:,.1f} units.

**Supplier allocation then improves it further.** Keeping 14 days fixed, the recommended MILP increases expected service from **{b14.mc_expected_on_time_accepted_pct:.3f}% to {w.mc_expected_on_time_accepted_pct:.3f}%** (**+{w.mc_expected_on_time_accepted_pct-b14.mc_expected_on_time_accepted_pct:.3f} pp**), reduces expected shortfall by **{(b14.mc_expected_at_risk_units-w.mc_expected_at_risk_units)/b14.mc_expected_at_risk_units*100:.2f}%**, and lowers risk-adjusted expected total by **{dollar(b14.mc_mean_risk_adjusted_total_usd-w.mc_mean_risk_adjusted_total_usd)}**.

**Like-for-like full-service allocation:** `COST_FULL_14D` also allocates all units with a 14-day buffer, costing **{dollar(c14.mc_mean_risk_adjusted_total_usd)}** after modeled risk. `RISK60_14D` improves this by **{dollar(c14.mc_mean_risk_adjusted_total_usd-w.mc_mean_risk_adjusted_total_usd)}** (= **{100*(c14.mc_mean_risk_adjusted_total_usd-w.mc_mean_risk_adjusted_total_usd)/c14.mc_mean_risk_adjusted_total_usd:.3f}%**). This smaller difference is the attributable incremental value of *risk-sensitive sourcing decisions* after fixing the lead-time buffer and demand-coverage policy.

**60% vs 70% concentration:** expected risk-adjusted cost difference **{dollar(r70.mc_mean_risk_adjusted_total_usd-w.mc_mean_risk_adjusted_total_usd)}** in favor of 60%, with a deterministic sourcing-cost increase of **{dollar(w.deterministic_policy_cost_usd-r70.deterministic_policy_cost_usd)}**. The MC paired-sampling 95% interval for the risk-adjusted difference is **{dollar(pair.iloc[0].mc_approx_95_ci_lower_usd)} to {dollar(pair.iloc[0].mc_approx_95_ci_upper_usd)}**, conditional on fixed assumed risks and unit penalties. Parameter uncertainty is **not** in this interval.

## 3. Scenario decision table

| Policy | Unallocated planned units | Policy cost (USD) | Expected on-time accepted % | Expected service shortfall units | Risk-adjusted total (USD) |
|---|---:|---:|---:|---:|---:|
{scenario_table}

See `outputs/scenario_comparison.csv` for all 11 scenarios and `outputs/paired_comparison_uncertainty.csv` for paired Monte Carlo standard errors.

## 4. Operational award recommendations (six-month aggregate)

Each material-month is allocated across **at least three awarded supplier rows in the selected solution**, with a maximum observed single-source share of **{w.max_supplier_share_per_sku_month_pct:.2f}%**; the percentages below are aggregate across the full six months and should **not** replace the monthly PO schedule.

| Material ID | Item | Criticality | Top three awarded sources in six-month portfolio |
|---|---|---|---|
{mat_table}

**Implementation:** Source monthly purchase quantities and landed cost from `tableau/allocation_all_policies.csv` filtered by `scenario_id=RISK60_14D`. Set a **hypothetical monthly required receipt date**, then order by `required_date − quoted_lead_time_days − 14 days`. Confirm supplier acceptance and refresh quotes before any actual purchase order. If late, reoptimize with changed capacity and expedited actions.

## 5. Economics and optimization definitions

- Landed unit cost = `quote_price × (1+duty_pct) + freight_usd_per_unit`.
- Early-order inventory carrying premium = `landed_purchase_value × 1.5% per month × max(0, buffer_days−4)/30`.
- Supplier mobilization = `$1,200 × distinct suppliers awarded during six-month planning horizon` (assumed even for pre-approved suppliers, so it is explicitly a **planning/setup proxy**, not necessarily first-ever onboarding).
- Critical material on-time service loss = **$120 per not-on-time-accepted unit**. Medium-critical = **$60/unit**; these are *NEW scenario assumptions* not contained in original cost input. Original dataset's $8/unit/month unallocated backlog penalty is **not** substituted for line-stop opportunity cost.
- MILP chooses integer x_(month,material,supplier), binary award flags and binary activated suppliers; enforces `SUM_s x = forecast demand` for every material/month (full allocation), `MOQ*y <= x <= min(capacity, supplier_share_cap*demand)*y`, eligibility and minimum 2 awarded suppliers per material/month. Minimizes landed + holding + activation + an **analytic expected service-loss proxy** using supplier lead-time SD, disruption likelihood and defects. Monte Carlo subsequently checks a more detailed random-capacity model.
- Supplier-month disruption probabilities, yield standard deviations and regional groups are synthetic assumptions from `dim_risk_assumptions.csv`. MC uses 3,000 draws, seed `20261109` and **common random numbers** across scenarios. A supplier-month is assigned a lead-time deviation; shipment is counted timely if deviation ≤ additional planned lead buffer. Quality rejects and regional/idiosyncratic disruptions reduce usable quantity. Physical supply is capped at the realized disruption-adjusted capacity. Late units are not treated as permanently lost; they count as *not supplied on time for that production month's need*.

## 6. Sensitivity to the service-loss opportunity-cost assumption

If we rescale *only* the service-loss dollar penalty and **do not rerun allocations**, the preferred tested portfolio changes:

| Risk cost scale | Lowest expected-total-cost policy among existing candidate portfolios |
|---:|---|
{sensitivity}

The selection is **sensitive to how costly late/rejected critical materials are assumed to be**. In a real sourcing business case, Finance/Operations must validate those figures. For production-sustaining Apple-style GSM, the action is a contingent recommendation subject to validation of line-stop costs, real lead time, quality and contract terms.

## 7. Additional integrity and interpretation notes

- All original supplier data are **fully synthetic**, not sourced from Kaggle or Apple.
- This project is a **solved simulated planning case**. Neither cost reduction nor on-time performance has been observed in production.
- Historical PO OTIF = strict share of PO orders received *in full* by requested date; it is **not comparable** to six-month MC aggregate on-time accepted **quantity** metric.
- This is not a two-stage recourse model: there is **no** dynamic month-to-month inventory carryover, capacity recovery, supplier substitution after shocks, expediting, FX volatility optimization, order splitting logistics or real payment terms cashflow optimization. Quote/lead times are assumed valid during plan.
- Regional correlation monthly shock probability and production line-stop opportunity-cost rates were introduced by this extension; they are assumptions, not statistically calibrated estimates.
- Optimizer uses deterministic analytical risk proxy, then 3,000-draw Monte Carlo validation. It is not a globally optimal stochastic MILP over all possible policies. The recommended policy is the **best tested under its assumptions**, not universal.
- Results can change materially with the random seed, simulated shocks, cost penalties, feasible allocation settings, alternative lead-time buffers and supplier contracts. Paired simulation CI measures only sampling error given assumptions.
'''
(docs/'FINAL_REPORT_VI.md').write_text(text,encoding='utf-8')

cv=f'''# CV-ready description (English)

**Supplier Selection, Performance & Procurement Risk | Independent Portfolio Case Study | Synthetic Supplier Data | 2026**

- Analyzed **784 historical purchase orders across 12 suppliers** using SQL Server, evaluating on-time delivery, PO OTIF, quality PPM and landed-cost performance to develop a supplier scorecard and sourcing-risk framework.
- Built a **Python mixed-integer linear programming (MILP)** model for **126.7K units of six-month demand** across 10 materials, optimizing supplier awards and order allocation under MOQ, capacity and dual-sourcing constraints; achieved **100% modeled allocation coverage** versus **99.24%** in the synthetic greedy benchmark.
- Tested **11 sourcing policies using 3,000 Monte Carlo simulations** and recommended a **60% supplier concentration cap with a 14-day planning buffer**, improving modeled on-time accepted supply from **75.75% to 98.37%** and reducing expected service shortfall by **93.3%**, with **34.5% lower assumed risk-adjusted total cost** compared with the initial baseline.

**Evidence and precision notes (do not paste in CV unless needed):**
- All results are *simulated*, not realized company performance; every supplier, quote and PO is synthetic.
- The 34.5% metric includes high modeled late/quality risk penalties; the actual deterministic sourcing cost is about **{dollar(w.incremental_policy_cost_vs_greedy_usd)} higher** than the baseline.
- To avoid attributing the whole improvement to supplier selection: adjusting buffer **alone** changes modeled service from **75.75% to 97.46%**; risk-adjusted allocation raises it further to **98.37%**.
- Alternative more conservative bullet 3: “Compared 11 sourcing scenarios through 3,000 Monte Carlo draws and selected a diversified 60%-capped portfolio, achieving **98.4% simulated on-time accepted supply** with **full planned demand coverage** while quantifying the cost–service trade-off.”
'''
(docs/'CV_BULLETS_EN.md').write_text(cv,encoding='utf-8')

readme='''# Project B — Supplier Selection, Performance & Procurement Risk

**Complete end-to-end synthetic portfolio:** 24-month history (Nov 2024–Oct 2026), 6-month sourcing plan (Nov 2026–Apr 2027), **12 fictional suppliers / 10 materials**. Includes SQL Server staging/analytics, mixed-integer supplier allocation, uncertainty simulation, 11-policy comparison, transparent assumptions, and Tableau-ready tables.

> **Provenance:** 100% synthetic. Absolutely no Kaggle data, Apple supplier data, real commercial quotations or realized cost savings. CV outcomes must say *modeled/simulated*.

## Recommended result

**RISK60_14D**: assign all 126,708 six-month demand units, max 60% share per supplier per material-month, ≥2 suppliers (solution happens to use ≥3), and order lead time +14 days planning buffer. 3,000-draw Monte Carlo estimates **98.37% on-time accepted quantity** versus **75.75%** for the original greedy 4-day benchmark; **93.3% lower expected service shortfall**, **34.5% lower hypothetical risk-adjusted cost**. **Direct procurement/holding/setup cost is higher, not lower.** All improvement is not due to supplier diversification; most is lead-time buffer improvement. See `docs/FINAL_REPORT_VI.md`.

## Files

- `data/*.csv`: original complete 12-supplier synthetic dataset (including original baseline/scorecard).
- `outputs/scenario_comparison.csv`: all 11 decision policies with costs, simulated risk, concentration, service; sorted by risk-adjusted cost.
- `outputs/allocation_all_policies.csv`: supplier award amounts, material and each plan-month, plus price, buffer, MOQ and capacity; **filter to RISK60_14D for recommended purchase schedule**.
- `outputs/expanded_assumptions.csv`: line-by-line unit costs, penalty rates, risk rates, simulation seed.
- `outputs/paired_comparison_uncertainty.csv`: conditional sampling error for policy comparisons.
- `tableau/*.csv`: ready-to-open analytical marts (each separate data source); `docs/TABLEAU_STEP_BY_STEP_VI.md`.
- `sql/01_create_tables.sql` and `python/load_sqlserver.py`: base DB setup; `sql/03_final_decision_views.sql`, `python/load_decisions_sqlserver.py`: reporting SQL and optimizer output imports.
- `python/run_end_to_end.py`: reproducible MILP and Monte Carlo source (regenerates Tableau tables and reports metadata).
- `python/build_reports.py`: regenerates documented numerical conclusions and CV bullets.
- `docs/STUDY_GUIDE_VI.md`: learning curriculum; `docs/CV_BULLETS_EN.md`: CV-ready text.
- `Supplier_B_Inputs_and_Scorecards.xlsx`: original curated input workbook (not an optimizer output; source CSVs are canonical).

## Quick start (Windows / VSCode)

```powershell
python -m venv .venv
.venv\\Scripts\\activate
pip install numpy pandas scipy
python python/run_end_to_end.py
python python/build_reports.py
```

For SQL Server: Run `sql/01_create_tables.sql` **only on a fresh SupplierManagementB DB because it DROPS existing pb tables**; edit connection string in `python/load_sqlserver.py`; `pip install pyodbc`; import historical facts; run `sql/02_supplier_analysis.sql` and `sql/03_final_decision_views.sql`. To put modeled outputs into SQL Server, edit and run `python/load_decisions_sqlserver.py` then rerun SQL views script.

For Tableau: connect **individually** to each file in `tableau/` (`Text File`) or SQL Server reporting views; instructions in `docs/TABLEAU_STEP_BY_STEP_VI.md`. Do not physically join `scenario_comparison` with `allocation_all_policies` and then sum scenario-level costs (fanout error).

## Project status

Solved simulated decision analysis, dataset and reproducible scripts **complete**. `.twb` / `.twbx` Tableau dashboard is **not generated automatically**: manual Tableau worksheets are described. Recommended decision is conditional on stated assumptions. The historical PO OTIF metric differs from Monte Carlo aggregate on-time quantity service.
'''
(R/'README.md').write_text(readme,encoding='utf-8')
print('Wrote reports',len(text),len(cv))
