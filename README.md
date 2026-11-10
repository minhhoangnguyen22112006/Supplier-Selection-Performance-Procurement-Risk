# Project B — Supplier Selection, Performance & Procurement Risk

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
.venv\Scripts\activate
pip install numpy pandas scipy
python python/run_end_to_end.py
python python/build_reports.py
```

For SQL Server: Run `sql/01_create_tables.sql` **only on a fresh SupplierManagementB DB because it DROPS existing pb tables**; edit connection string in `python/load_sqlserver.py`; `pip install pyodbc`; import historical facts; run `sql/02_supplier_analysis.sql` and `sql/03_final_decision_views.sql`. To put modeled outputs into SQL Server, edit and run `python/load_decisions_sqlserver.py` then rerun SQL views script.

For Tableau: connect **individually** to each file in `tableau/` (`Text File`) or SQL Server reporting views; instructions in `docs/TABLEAU_STEP_BY_STEP_VI.md`. Do not physically join `scenario_comparison` with `allocation_all_policies` and then sum scenario-level costs (fanout error).

## Project status

Solved simulated decision analysis, dataset and reproducible scripts **complete**. `.twb` / `.twbx` Tableau dashboard is **not generated automatically**: manual Tableau worksheets are described. Recommended decision is conditional on stated assumptions. The historical PO OTIF metric differs from Monte Carlo aggregate on-time quantity service.

## Tableau extra prepared marts

- `tableau/rfq_unit_economics.csv`: all 240 supplier bids; quoted landed unit cost, lead time, MOQ, approved eligibility.
- `tableau/scenario_cost_breakdown_long.csv`: stacked cost-component chart with a clear `modeled cash` versus `modeled opportunity cost` tag.
- `tableau/kraljic_category.csv`: category risk/profit impact coordinate map.
- `tableau/historical_spend_by_supplier_material.csv`: pre-aggregated spend, avoiding 1-to-many invoice/shipment joins in Tableau.
- `Project_B_Executive_Dashboard_Preview.html`: standalone interactive preview (not a Tableau workbook).

**Planning feasibility limitation:** The Nov 2026–Apr 2027 forecast is a synthetic horizon. The 14-day forward ordering buffer is assumed achievable at planning time; first-month orders may have required a release date before Nov 9, 2026. The model is a forward-planning simulation rather than a live executable PO release schedule.
