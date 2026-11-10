# Hướng tự học lại Project B (SQL → MILP → Monte Carlo → Tableau)

## Module 1 — Business context và data dictionary (1–2 sessions)

- Đọc `README.md`, `docs/FINAL_REPORT_VI.md`, `docs/DATA_DICTIONARY_original.csv`, `data/dim_cost_assumptions.csv`, `outputs/expanded_assumptions.csv`.
- Học 4 granularity: PO-level (`fact_purchase_order`), shipment-level (`fact_shipment`), supplier/material/month quote (`fact_supplier_quote`), material/month demand (`fact_future_demand`).
- Tự giải thích vì sao join `fact_shipment` trực tiếp với `fact_invoice` qua `po_id` làm nhân đôi số dòng; link qua shipment_id hoặc aggregate về PO trước khi join.
- Phân biệt **Kraljic category** với **supplier scorecard**; category đánh giá supply risk/profit impact, supplier rank đánh giá delivery-quality-cost-resilience.

## Module 2 — Historical SQL Supplier Performance (2 sessions)

1. Mở `sql/01_create_tables.sql` để dựng DB **mới** (cảnh báo script drop tables cũ).
2. Load CSV bằng `python/load_sqlserver.py` (cần chỉnh connection string).
3. Chạy `sql/03_final_decision_views.sql`.
4. Tự viết query `COUNT(*)`, sum spend, gross PO OTIF, Defect PPM; đối chiếu 784 POs, $17,000,113.25 spend, 48.72% PO OTIF, ~3,997 PPM.
5. Tự xây top-10 supplier scorecard theo `po_otif_pct`, `defect_ppm`, landed spend; giải thích xung đột giữa chất lượng và giá.
6. Join `dim_category` → `dim_material` để dựng Kraljic matrix.

## Module 3 — Supplier Selection MILP (2–3 sessions)

- Đọc `python/run_end_to_end.py` các hàm `calc_unit_cost`, `optimize`.
- Decision variables: `x` = awarded integer units, `y` = binary quote-active; `z` = binary supplier activated in 6-month horizon.
- Ràng buộc: forecast demand exactly allocated, supplier qualified, each supplier ≤ capacity, MOQ nếu chọn, max 60% mỗi material/month, tối thiểu 2 sources mỗi material/month.
- Objective terms: landed quote cost + carrying early-order + supplier activation + analytic service-loss risk proxy.
- So sánh `COST_FULL_14D` với `RISK60_14D`. Cùng đáp ứng 100% planned demand và 14-day buffer, nhưng allocation risk-aware thay đổi để giảm late/reject risk.
- Exercise: tự đổi supplier share cap 60% → 70%, 80%, kiểm tra kết quả/MOQ feasibility.

## Module 4 — Monte Carlo risk simulation (2–3 sessions)

- Đọc các blocks `regional_active`, `idio_active`, `lead_jitter`, `defect` và `physically_received`.
- Understand **common random numbers**: all policies face exactly the same simulated supplier/month shocks, reducing noise in paired comparisons.
- On-time good quantity = `min(allocated, disrupted_available_capacity) × on_time_flag × (1-defect_rate)`.
- Compute demand gap (at each material/month) and risk-adjusted objective = policy cost + material-criticality-weighted expected service shortfall.
- Interpret `mc_p95_shortfall_units` and `mc_prob_on_time_accepted_ge_95pct`.
- Distinguish **Monte Carlo sampling uncertainty** (paired CI) vs **parameter uncertainty** (cost/lead-time/disruption assumptions). Only the former is estimated here.
- Exercise: vary opportunity-cost penalty multiplier 0.25× / 1× / 2× (see `tableau/risk_penalty_sensitivity.csv`), explain how recommended policy changes.

## Module 5 — Tableau (2–4 sessions)

Follow `docs/TABLEAU_STEP_BY_STEP_VI.md`; create Dashboard 1/2/3/4. Compare original supplier rank with risk-selected suppliers. Export dashboard screenshots and document who would execute what sourcing decision in the six-month plan.

## Interview preparation — 8 questions to answer yourself

1. Why is a high PO OTIF score not necessarily the cheapest supplier?
2. What is the difference between *planned allocation coverage*, historical PO OTIF, and simulated on-time accepted quantity?
3. Why could more expensive quotes yield a lower **risk-adjusted** TCO?
4. Why isn't the 34.54% modeled risk-adjusted improvement cash savings?
5. Why did increasing the order buffer provide most of the improvement?
6. Why force supplier share ≤60%, and what is the cost of lowering the cap?
7. What happens if production-line stop penalties are only 25% of assumed values?
8. What additional real data (quote validity, contracts, lead-time distributions, recovery strategies) would you need to recommend actual supplier awards?
