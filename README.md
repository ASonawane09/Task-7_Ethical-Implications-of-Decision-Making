# Task-7: Ethical Implications of Decision Making

This repository hosts the deliverables for **Task 7: Ethical Implications of Decision Making**. The goal is to convert analytical findings from Syracuse Men’s Basketball data into a stakeholder report that embeds strong ethical, reliability, and robustness reasoning.

---

## 📂 Repository Structure

- **stakeholder_report.md / stakeholder_report.pdf** — Final report for decision-makers, with:
  - Executive Summary  
  - Findings & Recommendations  
  - Ethical & Legal Analysis  
  - Uncertainty, Robustness & Bias Checks  
  - Appendices (raw LLM output excerpt, figures, code lineage)  

- **Ethics_Risk.md** — In-depth treatment of fairness, equity, reliability, and data limitations.

- **figures/**  
  - `points_by_player.png`  
  - `rebounds_by_player.png`  
  - `fg_percent_vs_points.png`  
  - `defense_contributions.png`  

- **validate_llm.py** — Validation script used in earlier phases (descriptive checks).

- **inject_uncertainty_bias_checks.py** — Tool to generate a structured Validation/Uncertainty plan and integrate a summary into the stakeholder report.

- **kpi_bootstrap_ci.py** — Script to compute bootstrap confidence intervals and append uncertainty summaries into the report.

---

## 🚀 How to Use & Reproduce

1. Ensure the **Syracuse MBB 2023–24 stats dataset** (CSV) is available in `data/` or an accessible path.  
2. Run:
   ```bash
   python inject_uncertainty_bias_checks.py
   python kpi_bootstrap_ci.py --csv path/to/your_dataset.csv --out .
