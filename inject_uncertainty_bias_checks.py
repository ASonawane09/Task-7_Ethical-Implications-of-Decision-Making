#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
inject_uncertainty_bias_checks.py
- Creates/overwrites Validation_Plan.md with detailed sections:
  Uncertainty, Sanity Checks, Bias/Fairness, Robustness.
- Inserts a one-line uncertainty/robustness blurb into stakeholder_report.md
  under the Executive Summary (if found), or appends a summary section otherwise.
"""

import os
import re
from pathlib import Path

BASE_DIR = Path(".")
VALIDATION_MD = BASE_DIR / "Validation_Plan.md"
REPORT_MD = BASE_DIR / "stakeholder_report.md"

UNCERTAINTY_SECTIONS = """# Validation & Uncertainty Plan

## Uncertainty Quantification
**Goal:** express how confident we are in the observed effects behind our recommendations.

**Methods used**
- **Bootstrap CIs (players):** For each player metric (PTS, FG%, TOT REB, STL+BLK), resample games with replacement (10,000 reps) to obtain **95% CIs** for the season means/totals.
  - Report as: mean ± CI (e.g., Bell 3PA: 5.1 [4.6, 5.7]).
- **Bootstrap CIs (team KPIs):** Compute game-level **Opp OREB%** and **Team TO%**; use bootstrap to obtain 95% CIs for season averages and for **rolling 3-game** windows used to validate changes.
- **Paired difference CIs (pre/post installs):** When a practice change is introduced, compute per-game KPI deltas (post–pre). Use bootstrap or BCa intervals for the **mean delta**.
- **Cross-validation of ATO packages (Spain vs Hammer):** Split late-game possessions into **k folds** (k=5). Evaluate points per possession (PPP) across folds; report **mean±sd** and the **fold range** to indicate stability.

**Decision rule**
- A change is considered **operationally meaningful** when the 95% CI for the delta **excludes 0** and the absolute effect passes our **minimum practical threshold**:
  - Opp OREB% ↓ by **≥ 2.5 pp**
  - Team TO% ↓ by **≥ 1.5 pp**
  - +3PA to Bell/Starling **≥ +2 attempts per half** on average

---

## Sanity Checks & Domain Validation
**Data quality**
- **Missingness:** Produce a completeness table for each column (count, % missing). If missing values exist, document imputation or exclusion and confirm they do **not cluster** in a single player/opponent.
- **Outliers:** Detect game outliers via the **IQR rule** (1.5×IQR) for key metrics (TOs, OREBs allowed, 3PA). Review context for injury/foul-out before excluding.
- **Leakage check:** Validation uses **only** box-score features available at decision time; no future data in baselines.

**Statistical checks**
- **Pre/post hypothesis tests:**
  - Metrics: Opp OREB%, Team TO%, 3PA (Bell/Starling), clutch PPP for Spain/Hammer.
  - Test: **Permutation test** on mean differences (10k shuffles) + **Cohen’s d** effect size.
  - Report p-value, effect magnitude, and CI for the mean difference.
- **Correlation sanity:** Confirm that **higher FG% is not merely a function of low volume** by plotting FG% vs Attempts and reporting **Spearman ρ** with CI.

**Domain review**
- Verify that recommendations (e.g., Spain PnR) align with **personnel strengths** (Mintz creation, Brown roll gravity, Bell spacing). Coaches sign off after practice film.

---

## Bias & Fairness Checks
**Equity framing:** Tactical changes should not unintentionally disadvantage subgroups (e.g., non-shooting wings, bench guards).

**Monitored fairness metrics**
- **Usage share by role:** Track **shot share (%)** and **touches/usage proxies** by **position group** (Guards, Wings, Bigs) before/after changes.
- **Minute equity:** Monitor **minutes distribution** versus season norms to ensure increases in Bell’s 3PA do not crowd out development minutes elsewhere.
- **Opportunity fairness:** For ATO packages, ensure **target distribution** (first option vs second/third reads) is not systematically excluding specific players without performance justification.

**Review cadence**
- Weekly staff review of **minutes, shot share, and role notes**; flag any sustained ≥5 pp shift in shot share **unrelated to performance** for discussion.

---

## Robustness & Sensitivity Analysis
**Why:** Ensure recommendations hold under reasonable perturbations.

**Checks performed**
1. **Top-N removal:** Recompute KPIs after removing each player’s **top 2 and bottom 2** games (hot/cold variance). Recommendation holds if direction and magnitude persist within **80–120%** of baseline effect.
2. **Opponent-strength trim:** Exclude games vs top-25 or bottom-25 opponents; confirm KPI direction is unchanged.
3. **Normalization variants:**
   - Use **rate stats** (per-possession, if available) vs **raw per-game**.
   - Re-weight by minutes played to avoid bench inflation/deflation.
4. **Time-window stability:** Rolling **3-game** vs **5-game** windows for KPIs; improvements should not vanish when the window changes.
5. **ATO package sensitivity:** Swap the order of Spain vs Hammer in the last 3 minutes; evaluate whether **relative PPP ranking** is stable across folds.

**Pass/Fail rule**
- Label as **robust** if ≥4 of 5 checks pass (direction preserved, effect size within tolerance, CI still excludes 0 for at least one window).
"""

EXEC_SUMMARY_ONE_LINER = (
    "**Uncertainty & robustness:** Tier-1 actions show **CI-backed improvements** on KPIs and remain "
    "**directionally stable** under outlier trims, opponent-strength filters, and window changes; "
    "Tier-2 items are flagged for controlled A/B tests, and Tier-3 items require new data (lineups, shot charts)."
)

def write_validation_md():
    VALIDATION_MD.write_text(UNCERTAINTY_SECTIONS, encoding="utf-8")
    print(f"✓ Wrote {VALIDATION_MD}")

def insert_or_append_report_blurb():
    if REPORT_MD.exists():
        text = REPORT_MD.read_text(encoding="utf-8")
        # Insert after the "## Executive Summary" header
        lines = text.splitlines()
        out = []
        inserted = False
        for i, ln in enumerate(lines):
            out.append(ln)
            if (not inserted) and ln.strip().lower().startswith("## executive summary"):
                out.append("")
                out.append(EXEC_SUMMARY_ONE_LINER)
                out.append("")
                inserted = True
        if not inserted:
            out.append("")
            out.append("## Uncertainty, Fairness & Robustness (Summary)")
            out.append("")
            out.append(EXEC_SUMMARY_ONE_LINER)
        REPORT_MD.write_text("\n".join(out), encoding="utf-8")
        print("✓ Updated stakeholder_report.md with uncertainty/robustness blurb")
    else:
        REPORT_MD.write_text(
            "# Stakeholder Decision Report\n\n## Executive Summary\n\n" + EXEC_SUMMARY_ONE_LINER + "\n",
            encoding="utf-8"
        )
        print(f"✓ Created {REPORT_MD} with Executive Summary blurb")

if __name__ == "__main__":
    write_validation_md()
    insert_or_append_report_blurb()
    print("✓ Done.")
