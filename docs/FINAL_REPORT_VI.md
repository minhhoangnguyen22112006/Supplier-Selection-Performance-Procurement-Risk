# PROJECT B — FINAL SOURCING DECISION REPORT

**Supplier Selection, Performance & Procurement Risk | Synthetic electronics-component procurement | 2026**

## 1. Executive decision

**Recommended tested policy: `RISK60_14D`.** Place orders for the next six planning months using integer MILP allocations, approved supplier eligibility, quoted landed cost, MOQ/capacity, **60% maximum supplier share of each material-month**, and **at least two sources per material-month**. Place POs at the quoted supplier lead time **plus a 14-day planning buffer** before the hypothetical required receipt date. For each material/month, use the exact `tableau/allocation_all_policies.csv` purchase quantities filtered to `RISK60_14D`.

The recommendation is **best among 11 enumerated policies under explicitly synthetic economic/risk assumptions**, not a mathematically proven global stochastic optimum or a real-world recommendation to Apple.

### Measured results from 3,000 common Monte Carlo draws

- Plan **126,708 of 126,708 units = 100% planned allocation**, versus 963 unallocated in the greedy baseline. This is **planned coverage, not OTIF**.
- Expected simulated **on-time accepted material units: 124,637** or **98.366% of demand**; baseline 75.753% (**+22.613 percentage points**).
- Expected modeled **service shortfall: 2,070.9 units**, versus 30,723.2; **93.26% reduction**. This includes late arrival and rejected units, not just unallocated purchase order quantities.
- **97.93%** of simulation draws achieved at least 95% total on-time accepted supply across the six months. P95 total service shortfall = **5,131 units**.
- Deterministic six-month sourcing policy cost = **$4,858,147** (landed purchase **$4,820,842**, incremental carrying **$24,104**, activation **$13,200**). Baseline = **$4,786,802**, a policy cash-cost **increase of $71,345** (not procurement savings).
- Expected risk-adjusted total = **$5,057,013**, versus **$7,725,726** at baseline, **34.543% lower**. This includes **hypothetical opportunity costs of late/missing production materials**, not realized accounting savings.

## 2. Fair attribution: what actually helped?

**Early PO release is the dominant lever.** With exactly the original greedy suppliers/quantities but a 14-day buffer, expected modeled service improves from **75.753% to 97.457%** and expected shortfall from 30,723.2 to 3,222.2 units.

**Supplier allocation then improves it further.** Keeping 14 days fixed, the recommended MILP increases expected service from **97.457% to 98.366%** (**+0.909 pp**), reduces expected shortfall by **35.73%**, and lowers risk-adjusted expected total by **$82,709**.

**Like-for-like full-service allocation:** `COST_FULL_14D` also allocates all units with a 14-day buffer, costing **$5,063,722** after modeled risk. `RISK60_14D` improves this by **$6,709** (= **0.132%**). This smaller difference is the attributable incremental value of *risk-sensitive sourcing decisions* after fixing the lead-time buffer and demand-coverage policy.

**60% vs 70% concentration:** expected risk-adjusted cost difference **$1,011** in favor of 60%, with a deterministic sourcing-cost increase of **$848**. The MC paired-sampling 95% interval for the risk-adjusted difference is **$750 to $1,273**, conditional on fixed assumed risks and unit penalties. Parameter uncertainty is **not** in this interval.

## 3. Scenario decision table

| Policy | Unallocated planned units | Policy cost (USD) | Expected on-time accepted % | Expected service shortfall units | Risk-adjusted total (USD) |
|---|---:|---:|---:|---:|---:|
| BASE_GREEDY | 963 | $4,786,802 | 75.75% | 30,723 | $7,725,726 |
| BASE_GREEDY_14D | 963 | $4,810,664 | 97.46% | 3,222 | $5,139,722 |
| COST_FULL_14D | 0 | $4,850,140 | 98.22% | 2,257 | $5,063,722 |
| RISK70_10D | 0 | $4,857,970 | 95.86% | 5,246 | $5,391,332 |
| RISK70_14D | 0 | $4,857,298 | 98.35% | 2,087 | $5,058,024 |
| RISK60_14D | 0 | $4,858,147 | 98.37% | 2,071 | $5,057,013 |

See `outputs/scenario_comparison.csv` for all 11 scenarios and `outputs/paired_comparison_uncertainty.csv` for paired Monte Carlo standard errors.

## 4. Operational award recommendations (six-month aggregate)

Each material-month is allocated across **at least three awarded supplier rows in the selected solution**, with a maximum observed single-source share of **58.95%**; the percentages below are aggregate across the full six months and should **not** replace the monthly PO schedule.

| Material ID | Item | Criticality | Top three awarded sources in six-month portfolio |
|---|---|---|---|
| MAT001 | Aluminosilicate glass blank | High | SUP004 53.5%, SUP001 34.1%, SUP002 10.2% |
| MAT002 | Glass-ceramic preform | High | SUP003 39.1%, SUP001 35.5%, SUP007 21.5% |
| MAT003 | Anti-reflective coating solution | High | SUP005 43.6%, SUP003 34.5%, SUP012 21.9% |
| MAT004 | Vacuum deposition target | High | SUP005 45.0%, SUP002 35.6%, SUP006 19.4% |
| MAT005 | CNC precision frame | Medium | SUP004 45.6%, SUP001 36.0%, SUP008 10.4% |
| MAT006 | Stainless mounting bracket | Medium | SUP009 50.8%, SUP004 34.6%, SUP007 14.6% |
| MAT007 | Polishing slurry | Medium | SUP009 44.1%, SUP007 34.8%, SUP011 21.1% |
| MAT008 | Diamond grinding pad | Medium | SUP008 43.7%, SUP003 34.5%, SUP012 21.8% |
| MAT009 | UV optical adhesive | High | SUP006 44.9%, SUP002 35.6%, SUP011 19.5% |
| MAT010 | High-temperature bonding resin | High | SUP012 55.9%, SUP003 35.4%, SUP006 8.7% |

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
| 0.00× | BASE_GREEDY |
| 0.10× | BASE_GREEDY_14D |
| 0.25× | BASE_GREEDY_14D |
| 0.50× | COST_FULL_14D |
| 1.00× | RISK60_14D |
| 1.50× | RISK60_14D |
| 2.00× | RISK60_14D |

The selection is **sensitive to how costly late/rejected critical materials are assumed to be**. In a real sourcing business case, Finance/Operations must validate those figures. For production-sustaining Apple-style GSM, the action is a contingent recommendation subject to validation of line-stop costs, real lead time, quality and contract terms.

## 7. Additional integrity and interpretation notes

- All original supplier data are **fully synthetic**, not sourced from Kaggle or Apple.
- This project is a **solved simulated planning case**. Neither cost reduction nor on-time performance has been observed in production.
- Historical PO OTIF = strict share of PO orders received *in full* by requested date; it is **not comparable** to six-month MC aggregate on-time accepted **quantity** metric.
- This is not a two-stage recourse model: there is **no** dynamic month-to-month inventory carryover, capacity recovery, supplier substitution after shocks, expediting, FX volatility optimization, order splitting logistics or real payment terms cashflow optimization. Quote/lead times are assumed valid during plan.
- Regional correlation monthly shock probability and production line-stop opportunity-cost rates were introduced by this extension; they are assumptions, not statistically calibrated estimates.
- Optimizer uses deterministic analytical risk proxy, then 3,000-draw Monte Carlo validation. It is not a globally optimal stochastic MILP over all possible policies. The recommended policy is the **best tested under its assumptions**, not universal.
- Results can change materially with the random seed, simulated shocks, cost penalties, feasible allocation settings, alternative lead-time buffers and supplier contracts. Paired simulation CI measures only sampling error given assumptions.

## 8. Thời điểm triển khai và khả năng thực thi

Kịch bản giả định đặt PO sớm hơn theo `quoted_lead_time_days + 14 ngày`, nhưng **không có ngày cần hàng thực tế ở cấp đơn hàng** để tính ngày release chính xác. Kỳ forecast bắt đầu từ 11/2026; nếu triển khai sau 09/11/2026, một số PO đầu kỳ có thể đã quá hạn phát hành để kịp buffer 14 ngày. Vì vậy đây là **kế hoạch tối ưu tham chiếu**, không phải lịch PO khả thi được xác nhận tại ngày hiện tại. Trong ứng dụng thật phải thay bằng due date thực, inventory hiện tại, order-in-transit, confirmed capacity, expedite options và reoptimize rolling weekly.
