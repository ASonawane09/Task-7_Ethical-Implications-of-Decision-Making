#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
kpi_bootstrap_ci.py
- Computes bootstrap confidence intervals for player-level metrics (PTS, TOT REB, FG%, STL+BLK).
- Attempts team-level KPIs if per-game grouping exists (Game/Date/Opponent/GameID).
- Writes results to analysis/ci_results.json and analysis/ci_summary.md
- Optionally appends a short summary to stakeholder_report.md.

Run:
  python kpi_bootstrap_ci.py --csv data/syracuse_mbb_2023_24_stats.csv --out analysis
"""

import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
import re

def find_game_col(df: pd.DataFrame):
    for col in ["Game", "GAME", "Date", "DATE", "Opponent", "OPPONENT", "GameID", "GAMEID"]:
        if col in df.columns:
            return col
    return None

def bootstrap_ci(arr, n_boot=5000, ci=0.95, agg=np.mean, random_state=42):
    rng = np.random.default_rng(random_state)
    arr = np.asarray(arr)
    arr = arr[~np.isnan(arr)]
    if arr.size == 0:
        return (np.nan, np.nan, np.nan)
    boots = []
    n = len(arr)
    for _ in range(n_boot):
        sample = rng.choice(arr, size=n, replace=True)
        boots.append(agg(sample))
    boots = np.sort(boots)
    lower = (1-ci)/2
    upper = 1 - lower
    return float(np.mean(arr)), float(np.quantile(boots, lower)), float(np.quantile(boots, upper))

def summarize_players(df: pd.DataFrame):
    # If multiple rows per player exist, treat as per-game; else use single-row aggregates.
    counts = df["Player"].value_counts()
    multi = counts.max() > 1
    results = {}
    for player, sub in df.groupby("Player"):
        stats = {}
        if multi:
            stats["PTS_mean_CI"] = bootstrap_ci(sub["PTS"].values, agg=np.mean)
            if "TOT" in sub.columns:
                stats["REB_tot_CI"] = bootstrap_ci(sub["TOT"].values, agg=np.sum)
            if "FG%" in sub.columns:
                stats["FG%_mean_CI"] = bootstrap_ci(sub["FG%"].values, agg=np.mean)
            stl = sub["STL"].values if "STL" in sub.columns else np.zeros(len(sub))
            blk = sub["BLK"].values if "BLK" in sub.columns else np.zeros(len(sub))
            stats["STL+BLK_tot_CI"] = bootstrap_ci(stl+blk, agg=np.sum)
        else:
            # Only one row per player -> cannot bootstrap; fallback to values
            row = sub.iloc[0]
            stats["PTS_mean_CI"] = (float(row.get("PTS", np.nan)), np.nan, np.nan)
            stats["REB_tot_CI"] = (float(row.get("TOT", np.nan)), np.nan, np.nan)
            stats["FG%_mean_CI"] = (float(row.get("FG%", np.nan)), np.nan, np.nan)
            stats["STL+BLK_tot_CI"] = (float(row.get("STL",0)+row.get("BLK",0)), np.nan, np.nan)
        results[player] = stats
    return results

def team_kpis(df: pd.DataFrame):
    # Try to compute per-game team totals if a game column exists.
    game_col = find_game_col(df)
    if not game_col:
        return {"note": "No game identifier column detected; team KPI CIs skipped."}
    by_game = df.groupby(game_col, as_index=False).sum(numeric_only=True)
    # Team TO% proxy: TO / (FGA - OFF + TO + 0.44*FTA)
    if set(["TO","FGA","OFF","FTA"]).issubset(by_game.columns):
        poss = by_game["FGA"] - by_game["OFF"] + by_game["TO"] + 0.44*by_game["FTA"]
        to_pct = by_game["TO"] / np.where(poss==0, np.nan, poss)
        to_ci = bootstrap_ci(to_pct.values, agg=np.mean)
        out = {"Team_TO%_CI": to_ci}
    else:
        out = {"note": "Insufficient columns (need TO, FGA, OFF, FTA) for Team TO%."}
    return out

def write_outputs(results, team_results, out_dir: Path, report_path: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "ci_results.json", "w") as f:
        json.dump({"players": results, "team": team_results}, f, indent=2)
    # Summarize a few headlines
    lines = ["# Bootstrap CI Summary\n"]
    # Top 3 by points mean
    pts = [(p, v["PTS_mean_CI"][0]) for p, v in results.items() if not np.isnan(v["PTS_mean_CI"][0])]
    pts = sorted(pts, key=lambda x: x[1], reverse=True)[:3]
    lines.append("**Top scorers (mean PPG, bootstrap point estimate):** " + ", ".join(f"{p}: {v:.1f}" for p,v in pts))
    # Top 3 by defensive composite
    dcomp = [(p, v["STL+BLK_tot_CI"][0]) for p, v in results.items() if not np.isnan(v["STL+BLK_tot_CI"][0])]
    dcomp = sorted(dcomp, key=lambda x: x[1], reverse=True)[:3]
    lines.append("**Defensive composite leaders (STL+BLK totals):** " + ", ".join(f"{p}: {v:.0f}" for p,v in dcomp))
    if "Team_TO%_CI" in team_results:
        m, lo, hi = team_results["Team_TO%_CI"]
        lines.append(f"**Team TO% (mean, 95% CI):** {m:.3f} [{lo:.3f}, {hi:.3f}]")
    elif "note" in team_results:
        lines.append(f"_Team KPI note: {team_results['note']}_")
    summary_md = "\n\n".join(lines) + "\n"
    with open(out_dir / "ci_summary.md", "w") as f:
        f.write(summary_md)

    # Append into stakeholder_report.md
    if report_path.exists():
        txt = report_path.read_text(encoding="utf-8")
        txt += "\n\n---\n\n## Uncertainty Results (Auto-generated)\n\n" + summary_md
        report_path.write_text(txt, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/syracuse_mbb_2023_24_stats.csv")
    ap.add_argument("--out", default="analysis")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    out_dir = Path(args.out)
    report_path = Path("stakeholder_report.md")

    if not csv_path.exists():
        raise SystemExit(f"CSV not found at {csv_path}. Place your file there or pass --csv path.")

    df = pd.read_csv(csv_path)
    if "Player" not in df.columns:
        raise SystemExit("CSV must contain a 'Player' column.")

    res_players = summarize_players(df)
    res_team = team_kpis(df)
    write_outputs(res_players, res_team, out_dir, report_path)
    print(f"✓ Wrote {out_dir/'ci_results.json'} and {out_dir/'ci_summary.md'}")
    print("✓ Appended 'Uncertainty Results (Auto-generated)' to stakeholder_report.md")

if __name__ == "__main__":
    main()
