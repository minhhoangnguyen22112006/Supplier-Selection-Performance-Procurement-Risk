# Supplier Selection, Performance & Procurement Risk Optimization

**End-to-End Supply Chain Analytics Portfolio | SQL Server · Python · MILP · Monte Carlo · Tableau-ready Data**

An independent portfolio case study examining how a manufacturing company can improve supplier selection, optimize purchase order allocation, and mitigate procurement risk while balancing sourcing costs, delivery reliability, and supply continuity.

> **Data Disclaimer:** This project uses 100% synthetic procurement data. All suppliers, transactions, quotations, risk probabilities, and financial assumptions are fictional. No Apple supplier information or actual commercial data is used. All reported improvements are modeled outcomes, not realized business savings.

---

## 1. Executive Summary

### Business Problem

A manufacturer sourcing precision electronic and optical components must balance competing procurement objectives:

- Minimize total landed procurement costs.
- Improve supplier delivery and quality performance.
- Ensure sufficient supply to fulfill forecast demand.
- Reduce dependency on individual suppliers.
- Mitigate disruption risks through diversified sourcing and proactive purchase order planning.

**Key question:**

*Which suppliers should the company select, how should purchase orders be allocated, and when should orders be released to minimize risk-adjusted total cost while maintaining supply continuity?*

### Dataset Overview

| Dataset Component | Scope |
|---|---|
| Suppliers | 12 fictional suppliers |
| Materials | 10 material SKUs |
| Historical Purchase Orders | 784 |
| Shipment Records | 1,022 |
| Historical Period | Nov 2024 – Oct 2026 |
| Planning Horizon | Nov 2026 – Apr 2027 |
| Forecast Demand | 126,708 units |
| Sourcing Policies Evaluated | 11 |
| Monte Carlo Simulation | 3,000 draws |

The dataset integrates historical procurement activity, supplier quality and delivery performance, RFQ pricing, supplier capacity, minimum order quantities, future demand, and explicit cost and risk assumptions.

### Key Results

| KPI | Baseline | Recommended Policy |
|---|---:|---:|
| Planned Demand Allocation | 99.24% | 100.00% |
| Allocated Quantity | 125,745 | 126,708 |
| Unallocated Demand | 963 | 0 |
| Modeled On-Time Accepted Supply | 75.75% | 98.37% |
| Expected Service Shortfall | 30,723 units | 2,071 units |
| Modeled Risk-Adjusted Total Cost | $7.73M | $5.06M |

**Modeled improvements:**

- **100% planned demand allocation** across 126,708 units.
- **+22.62 percentage points** in modeled on-time accepted supply.
- **93.3% reduction** in expected service shortfall.
- **34.5% reduction** in assumed risk-adjusted total cost.

These improvements reflect the combined effects of earlier purchase order planning and supplier allocation optimization.

**Important:** Direct sourcing, inventory-holding, and setup costs increase by approximately **$71.3K** under the recommended policy. The decrease in risk-adjusted cost reflects lower expected shortage-related losses under assumed penalty rates; it is not a realized procurement cost saving.

---

## 2. Recommended Sourcing Strategy

### Selected Policy: `RISK60_14D`

The recommended policy combines risk-aware purchase order allocation with proactive lead-time management.

| Decision Variable | Recommended Policy |
|---|---|
| Allocation Method | Risk-adjusted MILP |
| Supplier Concentration Limit | Maximum 60% per material-month |
| Sourcing Strategy | Minimum 2 approved suppliers per material-month |
| Purchase Order Planning Buffer | 14 days |
| Demand Allocation | 126,708 units |
| Evaluation | Monte Carlo simulation |

### Why This Strategy?

**1. Earlier purchase order release**

Increasing the planning buffer from 4 to 14 days provides more time to absorb supplier lead-time variability.

This is the primary driver of the modeled service-level improvement.

**2. Risk-aware supplier allocation**

A mixed-integer linear programming model allocates purchasing requirements across approved suppliers while considering:

- Landed procurement costs.
- Supplier capacity constraints.
- Minimum order quantities (MOQ).
- Supplier eligibility.
- Supply concentration limits.
- Delivery and quality risk assumptions.

**3. Supplier diversification**

The model limits supplier concentration to reduce dependence on any single source. Although the constraint requires a minimum of two suppliers, the selected solution uses at least three suppliers for each material-month.

### Separating the Benefits

| Scenario | Modeled On-Time Accepted Supply |
|---|---:|
| Original baseline — 4-day buffer | 75.75% |
| Baseline allocation — 14-day buffer | 97.46% |
| Risk-aware allocation — 14-day buffer | 98.37% |

The additional improvement from 97.46% to 98.37% demonstrates the incremental benefit of risk-aware supplier allocation when the planning buffer is held constant.

Compared with a full-coverage, cost-minimizing allocation using the same 14-day buffer, the recommended risk-aware policy reduces expected risk-adjusted cost by approximately **$6.7K**.

**Decision interpretation:** The recommendation prioritizes supply reliability and lower expected disruption losses rather than minimum direct purchase price.

---

## 3. Analytical Methodology

### Phase 1 — Supplier Performance Analysis

**Tools:** SQL Server, Python

Analyze historical procurement performance through:

- Purchase Order On-Time In-Full (PO OTIF).
- Supplier delivery reliability.
- Defect Parts Per Million (PPM).
- Landed procurement spend.
- Lead-time performance.
- Supplier performance scorecards.

The historical PO OTIF metric is distinct from the simulated on-time accepted quantity service metric used in future sourcing scenarios.

### Phase 2 — Supplier Selection & Cost Analysis

**Tools:** SQL Server, Python

Evaluate suppliers using:

- Weighted supplier scorecards.
- Landed cost and RFQ comparisons.
- Supplier eligibility and capacity.
- Kraljic portfolio classification.
- Supplier concentration analysis.

### Phase 3 — Purchase Order Allocation Optimization

**Tool:** Python — Mixed-Integer Linear Programming (MILP)

Optimize supplier award quantities subject to operational and sourcing constraints.

The model evaluates alternative purchasing policies, including cost-focused allocation, supplier diversification, concentration limits, and risk-aware sourcing.

The objective is to identify feasible purchasing plans and assess trade-offs between direct sourcing costs and expected supply risk.

### Phase 4 — Procurement Risk Simulation

**Tool:** Python — Monte Carlo Simulation

Evaluate 11 sourcing policies using 3,000 simulation draws with comparable uncertainty scenarios.

The simulations incorporate modeled delivery, quality, and disruption uncertainty.

Key outputs include:

- Expected service shortfall.
- On-time accepted supply.
- Risk-adjusted total cost.
- Policy-level uncertainty comparisons.
- Supplier concentration and allocation results.

### Phase 5 — Visualization & Decision Reporting

**Tools:** Tableau-ready CSV datasets, SQL reporting views

Prepare supplier performance, sourcing allocation, policy comparison, and risk simulation results for interactive dashboards and executive reporting.

*Current visualization status: Tableau-ready data marts and an HTML executive dashboard preview are available. A native Tableau `.twb` or `.twbx` workbook has not yet been published.*

---

## 4. Technology Stack

| Technology | Application |
|---|---|
| SQL Server | Data staging, historical procurement analysis, reporting views |
| Python | Data processing, optimization, scenario evaluation |
| pandas / NumPy | Data manipulation and analytical calculations |
| SciPy | Mixed-integer optimization |
| Monte Carlo Simulation | Procurement risk and supply uncertainty |
| Tableau | Planned interactive supplier analytics and decision dashboards |
| Excel | Input assumptions and supplier scorecard review |
| GitHub | Version control and project documentation |

---

## 5. Repository Structure

| Directory / File | Description |
|---|---|
| `data/*.csv` | Complete original synthetic procurement dataset |
| `sql/` | SQL Server table creation and analytical views |
| `python/run_end_to_end.py` | Main MILP and Monte Carlo workflow |
| `python/build_reports.py` | Generates numerical summaries and CV-ready results |
| `outputs/scenario_comparison.csv` | Comparison of 11 sourcing policies |
| `outputs/allocation_all_policies.csv` | Supplier-level purchasing plans by policy, material, and month |
| `outputs/expanded_assumptions.csv` | Cost, risk, and simulation assumptions |
| `outputs/paired_comparison_uncertainty.csv` | Simulation uncertainty comparisons |
| `tableau/*.csv` | Prepared analytical data marts |
| `docs/FINAL_REPORT_VI.md` | Detailed findings and recommended sourcing decision |
| `docs/STUDY_GUIDE_VI.md` | Step-by-step learning guide |
| `docs/TABLEAU_STEP_BY_STEP_VI.md` | Instructions for creating Tableau dashboards |
| `docs/CV_BULLETS_EN.md` | Project summary for professional portfolio use |
| `Supplier_B_Inputs_and_Scorecards.xlsx` | Curated input assumptions and scorecards |

To examine the recommended purchasing plan, filter `outputs/allocation_all_policies.csv` to:

`policy_id = RISK60_14D`

This provides supplier-level order allocations by material and planning month.

---

## 6. Reproducing the Analysis

### Requirements

- Python 3 with compatible NumPy, pandas, and SciPy versions.
- SQL Server (optional for database analysis).
- Tableau Desktop or Tableau Public (optional for dashboard development).

### Run the Python Models

Clone the repository and open the project folder in VS Code.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install numpy pandas scipy
python python/run_end_to_end.py
python python/build_reports.py
```

The scripts regenerate the optimization and Monte Carlo outputs, Tableau-ready datasets, and documented results.

### SQL Server Analysis

1. Create a fresh `SupplierManagementB` database.
2. Run `sql/01_create_tables.sql`.
3. Configure the SQL Server connection in `python/load_sqlserver.py`.
4. Install `pyodbc` and import historical data.
5. Run `sql/02_supplier_analysis.sql`.
6. Load the optimized decision outputs using `python/load_decisions_sqlserver.py`.
7. Run `sql/03_final_decision_views.sql`.

**Warning:** The initial table-creation script drops existing project tables. Run it only in a dedicated database where this behavior is acceptable.

### Tableau Visualization

Connect separately to the relevant files in `tableau/`, or use the SQL Server reporting views.

Suggested dashboards:

**Dashboard 1 — Supplier Performance**

Historical spend, PO OTIF, Defect PPM, supplier ranking, and performance trends.

**Dashboard 2 — Sourcing Optimization**

Supplier allocation, demand coverage, landed costs, concentration, and scenario comparisons.

**Dashboard 3 — Procurement Risk & Executive Decision**

Monte Carlo shortfall distributions, risk-adjusted total cost, cost breakdown, and recommended sourcing policy.

See `docs/TABLEAU_STEP_BY_STEP_VI.md` for implementation instructions.

**Data modeling note:** Do not physically join policy-level cost summaries with supplier-level allocation records and then sum the policy-level costs. Different aggregation grains can create duplicate totals.

---

## 7. Additional Tableau Data Marts

| File | Purpose |
|---|---|
| `tableau/rfq_unit_economics.csv` | Supplier bids, quoted landed unit costs, lead times, MOQ, eligibility |
| `tableau/scenario_cost_breakdown_long.csv` | Direct cost versus modeled opportunity/risk cost |
| `tableau/kraljic_category.csv` | Supply risk and profit-impact segmentation |
| `tableau/historical_spend_by_supplier_material.csv` | Supplier-material spend analysis without join duplication |

An interactive HTML executive dashboard preview is also included in `Project_B_Executive_Dashboard_Preview.html`. This preview is not a Tableau workbook.

---

## 8. Assumptions & Limitations

This is a synthetic decision-support case study, not a live production sourcing system.

Key limitations include:

- Supplier profiles, RFQ prices, capacity, and performance histories are fictional.
- Monte Carlo risk distributions rely on explicit assumptions rather than empirically validated supplier probabilities.
- Risk-adjusted cost depends on assumed shortage penalties and associated cost parameters.
- The recommended strategy is the best-performing policy under the modeled objective and evaluated scenarios, not a proven global optimum across every possible procurement strategy.
- The 14-day planning buffer is assumed feasible. Some first-month purchase orders could require release before the planning horizon begins.
- The simulated service metrics do not represent realized supplier performance.

The model demonstrates analytical decision-making and sourcing trade-offs, not guaranteed business outcomes.

---

## 9. Final Business Recommendation

**Recommended policy: `RISK60_14D`**

Adopt risk-aware supplier allocation with a 60% supplier concentration cap, minimum dual sourcing, and a 14-day purchase order planning buffer.

Under the stated assumptions, this policy provides complete planned demand allocation, higher modeled delivery reliability, and lower expected risk-adjusted total cost than the original baseline.

The central finding is that **proactive lead-time management produces the largest service improvement, while supplier allocation optimization provides additional resilience and cost-risk benefits**.

---

**Project Type:** Independent Portfolio Case Study  
**Industry Context:** Electronics & Precision Component Procurement  
**Data Source:** 100% Synthetic  
**Year:** 2026
