import pandas as pd

CSV_PATH = "data/syracuse_mbb_2023_24_stats.csv"

def descriptive_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """Return totals by player for core stats."""
    keep = ["Player","PTS","OFF","DEF","TOT","AST","STL","BLK","FG%","3PT%","FT%"]
    cols = [c for c in keep if c in df.columns]
    return df.groupby("Player", as_index=False).sum(numeric_only=True)[cols].merge(
        df.groupby("Player", as_index=False).mean(numeric_only=True)[["Player","FG%","3PT%","FT%"]],
        on="Player",
        how="left",
        suffixes=("","_MEAN")
    )

def compute_def_composite(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Player", as_index=False).sum(numeric_only=True)[["Player","STL","BLK"]]
    g["DEF"] = g["STL"] + g["BLK"]
    return g.sort_values("DEF", ascending=False)

def leaders(summary: pd.DataFrame) -> dict:
    """Return simple leaders in PTS, TOT REB, AST, STL, BLK, FG% (mean)."""
    out = {}
    out["PTS_leader"] = summary.loc[summary["PTS"].idxmax(), "Player"]
    if "TOT" in summary.columns:
        out["REB_leader"] = summary.loc[summary["TOT"].idxmax(), "Player"]
    if "AST" in summary.columns:
        out["AST_leader"] = summary.loc[summary["AST"].idxmax(), "Player"]
    if "STL" in summary.columns:
        out["STL_leader"] = summary.loc[summary["STL"].idxmax(), "Player"]
    if "BLK" in summary.columns:
        out["BLK_leader"] = summary.loc[summary["BLK"].idxmax(), "Player"]
    # FG% from mean
    if "FG%_MEAN" in summary.columns:
        out["FG%_leader"] = summary.loc[summary["FG%_MEAN"].idxmax(), "Player"]
    return out

if __name__ == "__main__":
    df = pd.read_csv(CSV_PATH)
    summary = descriptive_profiles(df)
    comp = compute_def_composite(df)
    print("== Summary by Player (head) ==")
    print(summary.head(10).to_string(index=False))
    print("\n== Defensive Composite Leaders ==")
    print(comp.head(10).to_string(index=False))
    print("\n== Leaders ==")
    print(leaders(summary))
