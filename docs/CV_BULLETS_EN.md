# CV-ready description (English)

**Supplier Selection, Performance & Procurement Risk | Independent Portfolio Case Study | Synthetic Supplier Data | 2026**

- Analyzed **784 historical purchase orders across 12 suppliers** using SQL Server, evaluating on-time delivery, PO OTIF, quality PPM and landed-cost performance to develop a supplier scorecard and sourcing-risk framework.
- Built a **Python mixed-integer linear programming (MILP)** model for **126.7K units of six-month demand** across 10 materials, optimizing supplier awards and order allocation under MOQ, capacity and dual-sourcing constraints; achieved **100% modeled allocation coverage** versus **99.24%** in the synthetic greedy benchmark.
- Tested **11 sourcing policies using 3,000 Monte Carlo simulations** and recommended a **60% supplier concentration cap with a 14-day planning buffer**, improving modeled on-time accepted supply from **75.75% to 98.37%** and reducing expected service shortfall by **93.3%**, with **34.5% lower assumed risk-adjusted total cost** compared with the initial baseline.

**Evidence and precision notes (do not paste in CV unless needed):**
- All results are *simulated*, not realized company performance; every supplier, quote and PO is synthetic.
- The 34.5% metric includes high modeled late/quality risk penalties; the actual deterministic sourcing cost is about **$71,345 higher** than the baseline.
- To avoid attributing the whole improvement to supplier selection: adjusting buffer **alone** changes modeled service from **75.75% to 97.46%**; risk-adjusted allocation raises it further to **98.37%**.
- Alternative more conservative bullet 3: “Compared 11 sourcing scenarios through 3,000 Monte Carlo draws and selected a diversified 60%-capped portfolio, achieving **98.4% simulated on-time accepted supply** with **full planned demand coverage** while quantifying the cost–service trade-off.”
