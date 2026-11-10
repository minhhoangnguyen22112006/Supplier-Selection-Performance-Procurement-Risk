# PROJECT B — TABLEAU DASHBOARD GUIDE (CHI TIẾT)

**Đầu vào:** các CSV trong `tableau/`. Dữ liệu 100% synthetic. Nên tạo **4 dashboards, mỗi dashboard dùng nguồn dữ liệu ở đúng granularity** để tránh cộng trùng (fanout). Các con số dưới đây là **kết quả mô hình**, không phải hiệu quả kinh doanh thực tế.

## 0. Chuẩn bị nguồn dữ liệu

1. Tableau Desktop / Tableau Public → **Connect → Text File** → chọn từng CSV trong `tableau/`.
2. Tạo data source riêng cho từng file. Tốt nhất không dùng **physical join** giữa `scenario_comparison` (1 row/scenario) và `allocation_all_policies` (nhiều rows/scenario). Nếu join trực tiếp và `SUM([deterministic_policy_cost_usd])` sẽ **nhân đôi tổng chi phí**.
3. Cột `plan_month`, `year_month` lưu `YYYY-MM` dạng text; để sort chronological có thể tạo calculated field: `DATE(DATEPARSE('yyyy-MM', [plan_month]))`. Nếu phiên bản Tableau hỗ trợ tự nhận month hoặc chuỗi thứ tự ISO, có thể dùng text `YYYY-MM` theo thứ tự chữ cái.
4. Đặt field `scenario_id` làm **Dimension**; trong các worksheets chi phí và service chỉ dùng `scenario_comparison.csv`.
5. Các cột hậu tố `_pct` đều là thang 0–100; khi cần định dạng Tableau Percentage (0–1), phải chia 100.
6. Tên supplier và material đã được thêm vào bảng allocation; không cần join thêm dimension chỉ để lấy tên.

## Dashboard 1 — Supplier Performance & Spend

**Data source chính:** `supplier_monthly_kpis_tableau.csv` (grain: 1 supplier × 1 tháng). **Data source phụ:** `supplier_scorecard_tableau.csv` (grain: 1 supplier).

### KPI Worksheets

- Historical Spend: `SUM([landed_spend_usd])` → **$17.00M** toàn thời kỳ.
- PO OTIF: tạo `SUM([po_otif_count]) / SUM([orders])`, Format **Percentage** → ~**48.72%**. Không dùng `AVG([otif_pct])` vì trọng số mỗi supplier-month khác nhau.
- Quality Defect PPM: `1000000 * SUM([rejected_units]) / (SUM([accepted_units]) + SUM([rejected_units]))` → ~**3,997 PPM** (đúng khi nhận đủ inspection).
- PO Count: `SUM([orders])` → **784**.

### Worksheets

1. **Monthly PO OTIF trend**: Columns `[year_month]`, Rows ratio OTIF như trên; Color `[supplier_id]` hoặc filter một supplier. Line chart.
2. **Spend Pareto**: Rows supplier ID, Columns `SUM([landed_spend_usd])` Sort descending; optional Running Total with table calculation and secondary percent axis.
3. **Supplier Quality vs Delivery**: data source `supplier_scorecard_tableau`; Columns `[po_otif_pct]`, Rows `[defect_ppm]`; Detail `[supplier_name]`; Size `[spent_usd]`; Tooltip supplier score. Axis PPM lower is better.
4. **Weighted Supplier Ranking**: data source scorecard; Rows `[supplier_name]`, Columns `[weighted_score_100]`; sort DESC; show tooltip `po_otif_pct`, `defect_ppm`, `spent_usd`.

**Câu hỏi cần trả lời:** supplier có score tổng thể cao nhất có thật sự delivery/quality tốt nhất không? Đừng khuyến nghị supplier chỉ dựa vào rank tổng thể — các SKU không đồng nhất.

## Dashboard 2 — Sourcing Allocation & Total Cost

**Data source chính:** `scenario_comparison.csv` để làm KPI/scenario comparisons; `allocation_all_policies.csv` để phân tích supplier × material × month. Đặt `scenario_id` filter = `RISK60_14D` mặc định cho các allocation worksheets.

### KPI Worksheets

- Forecast Demand: `SUM([planned_demand_units])` khi filter một scenario → **126,708**.
- Planned Coverage: `AVG([planned_coverage_pct])` với một scenario = **100%**. Đây không phải OTIF.
- Landed Spend: `SUM([landed_purchase_cost_usd])` → **$4,820,842** cho recommended.
- Incremental buffer carrying cost: `SUM([early_order_carrying_cost_usd])` → **$24,104**.
- Modeled setup cost: `SUM([supplier_activation_cost_usd])` → **$13,200**.
- `SUM([deterministic_policy_cost_usd])` → **$4,858,147**, **cao hơn** baseline $4,786,802.

### Worksheets

1. **Policy trade-off bars**: Rows `[scenario_id]`, Columns `[deterministic_policy_cost_usd]`; filter all scenarios; compare baseline vs full-coverage vs risk-based.
2. **Allocation heatmap**: Rows `[material_name]`, Columns `[supplier_name]`, Color `SUM([allocated_units])`; filter to `RISK60_14D`. Supplier absence means zero award, not missing data.
3. **Supplier allocation share**: Columns `[plan_month]`, Rows `[material_name]`, Color `[supplier_name]`, Measure `SUM([allocated_units])`. Stacked bar by material/month; Tooltip `[share_sku_month_pct]` (field at supplier-material-month grain). Confirm max single-source share <60%.
4. **Award PO line detail**: Rows plan_month > material_name > supplier_name; Text `SUM([allocated_units])`; Tooltip unit_landed_cost_usd, moq_units, normal_capacity_units and buffer_days. This is the monthly buyer action list.
5. **Kraljic matrix**: separate `dim_category.csv` from `data/`; Columns `[profit_impact_score]`, Rows `[supply_risk_score]`, Color `[kraljic_quadrant]`, Label `[category_name]`; draw quadrant reference lines at 0.5 (illustrative thresholds).

**Lưu ý:** `SUM([landed_cost_usd])` trong allocation là đúng trong **một scenario** nếu lấy toàn bộ rows; tránh `AVG([unit_landed_cost_usd])` không trọng số để so sánh TCO giữa policies.

## Dashboard 3 — Supply Risk & Resilience

**Data sources:** `scenario_comparison.csv`, `mc_shortfall_histogram.csv`, `scenario_monthly.csv`, `sku_month_risk.csv`, `risk_penalty_sensitivity.csv`, `expanded_assumptions.csv`.

### 3.1 Risk vs Cost Frontier (most important)

Trong `scenario_comparison`:

- Columns: `[deterministic_policy_cost_usd]` (continuous)
- Rows: `[mc_expected_on_time_accepted_pct]` (0–100)
- Detail + Label: `[scenario_id]`
- Color: `[mc_mean_risk_adjusted_total_usd]` (lower is better)
- Tooltip: `[mc_expected_at_risk_units]`, `[mc_p95_shortfall_units]`, `[mc_prob_on_time_accepted_ge_95pct]`, `[buffer_high_days]`.

Đánh dấu `RISK60_14D` bằng label nhưng không vẽ các con số Monte Carlo như historical OTD/OTIF. Nhãn trục y là **modeled on-time accepted supply (% of forecast)**.

### 3.2 Shortfall distribution

- Data source: `mc_shortfall_histogram.csv`.
- Filter 2–3 scenarios `BASE_GREEDY`, `BASE_GREEDY_14D`, `RISK60_14D`.
- Columns: `[shortfall_bin_mid_units]` (continuous), Rows: `SUM([simulation_count])`, Color: `[scenario_id]` (dùng separate pane nhỏ nếu overlap khó đọc).
- 55 bins × 3,000 draws mỗi policy. **Do not add bins of different policies together**.

### 3.3 Shortfall risk over the planning horizon

- Data source: `scenario_monthly.csv`.
- Columns: `[plan_month]`, Rows: `[expected_on_time_accepted_pct]`, Color: `[scenario_id]`.
- Alternative bars: `[expected_shortfall_units]` by month.
- `scenario_monthly` chứa EXPECTED shortfall; không phải actual receipts.

### 3.4 At-risk material / supplier coverage

- Data source: `sku_month_risk.csv`: Rows `[material_name]`, Columns `[plan_month]`, Color `AVG([expected_on_time_accepted_pct])` for selected scenario; tooltip `[p95_shortfall_units]` and `[prob_any_shortfall_pct]`.
- Data source: `scenario_supplier_exposure.csv`: supplier share across full horizon. This is total portfolio share and **not** share of an individual SKU/month.

### 3.5 Risk penalty sensitivity

- Data source: `risk_penalty_sensitivity.csv`.
- Columns: `[risk_penalty_multiplier]`; Rows `[expected_total_usd]` Color `[scenario_id]`; optionally `[is_winner]=1` filter. Rationale: portfolio preference changes when the material service-loss penalty changes. This is vital to an honest economic recommendation.

## Dashboard 4 — Executive Recommendation (1-page case story)

**Context:** 784 PO historical, 12 suppliers, 10 materials, 6 months forecast, 3,000 MC draws.

Suggested layout:

```text
┌────────────────────────── PROJECT B SOURCING EXECUTIVE REVIEW ────────────────────────┐
│  Planned Coverage 100%  |  Modeled Timely Accepted 98.37%  |  Expected Shortfall -93.3% │
├───────────────────────────────────┬────────────────────────────────────────────────────┤
│  Risk vs Cost Frontier            │  Recommended policy: RISK60_14D                    │
│  (11 policy dots)                 │  60% max share / ≥2 sources / 14-day lead buffer    │
├───────────────────────────────────┼────────────────────────────────────────────────────┤
│  Scenario cost waterfall          │  10 Materials × Awarded Supplier & Share           │
│  Procurement cost ↑ $71.3k       │  Action list by material/month                      │
│  Risk-adjusted cost ↓ 34.54%     │                                                    │
└───────────────────────────────────┴────────────────────────────────────────────────────┘
```

**Câu chuyện quản trị:**

1. Baseline: low quote-first greedy leaves 963 planned units unallocated and exposure to late delivery.
2. Early order placement (14-day buffer) explains most simulated service improvement.
3. Supplier optimization + 60% concentration cap improves service by a further ~0.91 percentage points vs the *same buffer with original allocation*.
4. Direct purchase/holding/setup cost goes **up**; assumed risk-adjusted total goes **down**. This is the economic trade-off, not a purchasing discount claim.

## Tránh lỗi khi dùng Tableau

- Không lấy `SUM([demand_units])` từ `allocation_all_policies`: lặp mỗi supplier row → demand bị nhân 3–4 lần. Dùng `fact_future_demand.csv` hay `scenario_comparison.csv` cho tổng demand, hoặc `FIXED [scenario_id],[plan_month],[material_id]: MIN([demand_units])` nếu rất cần LOD.
- Không cộng `scenario_comparison` sang bảng allocation qua physical join nếu chưa aggregate trước.
- Không dùng `AVG([po_otif_pct])` thay PO-weighted rate.
- Không gọi simulated on-time accepted **OTIF**. Historical PO OTIF strict: 48.72%.
- Không dùng `SUM([expected_shortfall_units])` across **multiple** scenarios trừ khi cố tình làm tổng kịch bản (thường sai).
- Không gọi risk-adjusted opportunity-cost savings là cash savings. Xem `expanded_assumptions.csv` trước khi trình bày.

**Bàn giao:** các CSV được xuất thực tế. Chưa có file Tableau native `.twb/.twbx`; bạn tạo worksheet theo guide này để học thực hành.
