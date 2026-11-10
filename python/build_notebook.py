import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
cells=[]
def md(s):cells.append({'cell_type':'markdown','metadata':{},'source':s.splitlines(keepends=True)})
def code(s):cells.append({'cell_type':'code','metadata':{},'source':s.splitlines(keepends=True),'execution_count':None,'outputs':[]})
md('''# Project B — Supplier Selection, Performance & Procurement Risk

**Hướng tự học lại**: tất cả dữ liệu đều synthetic. Notebook chỉ đọc kết quả đã sinh; để chạy lại tối ưu và Monte Carlo, dùng `python/run_end_to_end.py`. Hãy đọc `docs/FINAL_REPORT_VI.md` trước.

Goal: hiểu khác nhau giữa historical supplier performance, planned sourcing coverage và simulated on-time accepted supply. Không gọi mức giảm *risk-adjusted cost* là cash savings.
''')
code('''from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
R = Path.cwd()
if not (R/'outputs').exists(): R = R.parent
D = R/'data'; O = R/'outputs'; T = R/'tableau'
score = pd.read_csv(D/'agg_supplier_scorecard.csv')
scenario = pd.read_csv(O/'scenario_comparison.csv')
alloc = pd.read_csv(T/'allocation_all_policies.csv')
risk = pd.read_csv(T/'risk_penalty_sensitivity.csv')
print('Working root:', R)
print('12 suppliers:', len(score),' | policy count:',len(scenario))
''')
md('''## 1. Historical supplier performance

Đọc 784 lịch sử purchase orders và scorecard. Vì một PO có nhiều shipments, phải tính PO OTIF ở cấp PO trước.
''')
code('''score[['supplier_name','purchase_orders','spent_usd','po_otif_pct','defect_ppm','weighted_score_100']].sort_values('weighted_score_100',ascending=False).head(12)
''')
md('''### Câu hỏi

Tại sao supplier có điểm scorecard tổng hợp cao nhất không nhất thiết có OTIF cao nhất? Nếu MAT004 là vật tư strategic, điểm supplier được ưu tiên theo mọi category có giống nhau không?
''')
md('''## 2. Phân biệt chi phí thực chi và risk-adjusted cost

Cash-policy (modeled): landed spend + incremental buffer carrying + supplier activation/setup. Risk-adjusted total = cash-policy + simulated service-loss opportunity cost. Hai loại không được trộn khi nói "cash saving".
''')
code('''cols=['scenario_id','planned_coverage_pct','deterministic_policy_cost_usd','mc_expected_on_time_accepted_pct','mc_expected_at_risk_units','mc_mean_risk_adjusted_total_usd','is_recommended']
scenario[cols].sort_values('mc_mean_risk_adjusted_total_usd')
''')
code('''fig, ax = plt.subplots(figsize=(9,4.5))
for _,r in scenario.iterrows():
    ax.scatter(r['deterministic_policy_cost_usd']/1e6,r['mc_expected_on_time_accepted_pct'])
    ax.annotate(r['scenario_id'],(r['deterministic_policy_cost_usd']/1e6,r['mc_expected_on_time_accepted_pct']),xytext=(3,5),textcoords='offset points',fontsize=8)
ax.set_xlabel('Modeled policy cash cost (USD million)')
ax.set_ylabel('Simulated on-time accepted quantity (%)')
ax.set_title('Cost versus simulated service — 11 policies')
plt.tight_layout()
plt.show()
''')
md('''## 3. Quantify effect of lead buffer separately from supplier allocation

Controlled comparisons:

- BASE_GREEDY (4 days) vs BASE_GREEDY_14D: **buffer effect**.
- BASE_GREEDY_14D vs RISK60_14D: **portfolio + full allocation** with buffer constant.
- COST_FULL_14D vs RISK60_14D: **risk-sensitive sourcing effect** with demand and buffer constant.
''')
code('''a=scenario.set_index('scenario_id')
for k in ['BASE_GREEDY','BASE_GREEDY_14D','COST_FULL_14D','RISK60_14D']:
    r=a.loc[k]
    print(f'{k:20s} | service {r.mc_expected_on_time_accepted_pct:6.3f}% | expected short {r.mc_expected_at_risk_units:9.1f} | risk adjusted ${r.mc_mean_risk_adjusted_total_usd:,.0f}')
''')
md('''## 4. Monthly recommended sourcing allocation

Các dòng sau mới là award quantities để tham khảo quyết định: phải lọc `RISK60_14D`. Thực hiện các bài toán kiểm tra MOQ, capacity, share cap theo mỗi supplier-material-month.
''')
code('''rec=alloc.query("scenario_id=='RISK60_14D'").copy()
rec[['plan_month','material_id','supplier_id','allocated_units','moq_units','normal_capacity_units','share_sku_month_pct','landed_cost_usd']].head(20)
''')
code('''assert (rec['allocated_units']>=rec['moq_units']).all()
assert (rec['allocated_units']<=rec['normal_capacity_units']).all()
assert (rec['share_sku_month_pct']<=60).all()
print('MOQ and capacity checks passed; max material-month source share:',rec['share_sku_month_pct'].max())
''')
md('''## 5. Monte Carlo interpretation

- `mc_expected_at_risk_units`: mean (short) on-time accepted quantity vs forecast, NOT permanent inventory loss.
- `mc_p95_shortfall_units`: in 95% draws total six-month shortfall is at most this value.
- `mc_prob_on_time_accepted_ge_95pct`: probability the six-month aggregate on-time accepted service reaches 95%, NOT historical PO OTIF.
''')
code('''u=pd.read_csv(T/'mc_shortfall_histogram.csv')
fig,ax=plt.subplots(figsize=(9,4))
for k in ['BASE_GREEDY','BASE_GREEDY_14D','RISK60_14D']:
    z=u.query('scenario_id==@k')
    ax.plot(z.shortfall_bin_mid_units,z.simulation_probability_pct,label=k)
ax.legend();ax.set_xlabel('Service shortfall over 6 months (units)')
ax.set_ylabel('Share of draws per bin (%)');ax.set_title('Monte Carlo distributions')
plt.tight_layout();plt.show()
''')
md('''## 6. Sensitivity to hypothetical line-stop opportunity cost

Nếu cost penalty giả định thấp, phương án được chọn thay đổi. Vì thế **34.5% modeled risk-adjusted cost improvement** không phải kết quả chắc chắn trong thực tế.
''')
code('''risk.query('is_winner==1')[['risk_penalty_multiplier','winner_at_multiplier','expected_total_usd']].sort_values('risk_penalty_multiplier')
''')
md('''## 7. Self-test questions

1. Vì sao một policy rẻ hơn trước rủi ro có thể đắt hơn sau risk-adjustment?
2. Hãy tự thay `risk_weight=0` hoặc 1 và cố giải thích thay đổi danh sách awarded suppliers.
3. Vì sao planning coverage 100% vẫn chưa đảm bảo OTIF 100%?
4. Bằng cách nào xác định thông số `penalty per critical service-unit` đáng tin cậy từ dữ liệu thật?
5. Nếu month-Nov order release date đã qua, phải replan những quyết định nào?
''')
nb={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}},'nbformat':4,'nbformat_minor':5}
(R/'notebooks'/'Project_B_Study_and_Review.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=2),encoding='utf-8')
print('Notebook cells',len(cells))
