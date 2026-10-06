"""
Merge separately downloaded series into data/monthly.csv for estimate.py.

Each input is a CSV with two columns: date, value (any parseable date; monthly or daily).
Daily series are averaged to months. All dates are mapped to month-end.

Usage:
    python build_monthly.py \
        --brent raw/brent.csv --pump raw/pump.csv --fx raw/fx.csv --tbill raw/tbill.csv \
        --cpi_new raw/cpi_2019base.csv [--cpi_old raw/cpi_2009base.csv ...] \
        --out data/monthly.csv

CPI rebasing: KNBS has changed the CPI base year more than once. Give the series oldest to
newest as repeated --cpi_old files followed by --cpi_new. Each older series is rescaled to the
next one using the average ratio over their overlapping months, so the index is continuous.
Pump prices may start later than the other series (leave early months empty); estimate.py
drops months with gaps.
"""
import argparse
import numpy as np
import pandas as pd


def load(path):
    d = pd.read_csv(path)
    d.columns = ["date", "value"]
    d["date"] = pd.to_datetime(d["date"])
    s = d.set_index("date")["value"].astype(float).sort_index()
    s = s.groupby(s.index.to_period("M")).mean()      # average within month
    s.index = s.index.to_timestamp(how="end").normalize()
    return s


def splice(older, newer):
    overlap = older.index.intersection(newer.index)
    if len(overlap) < 3:
        raise SystemExit("CPI series need at least 3 overlapping months to be spliced.")
    ratio = (newer.loc[overlap] / older.loc[overlap]).mean()
    older_scaled = older * ratio
    return pd.concat([older_scaled.loc[: newer.index.min() - pd.Timedelta(days=1)], newer])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--brent", required=True)
    ap.add_argument("--pump")
    ap.add_argument("--fx", required=True)
    ap.add_argument("--tbill", required=True)
    ap.add_argument("--cpi_old", action="append", default=[])
    ap.add_argument("--cpi_new", required=True)
    ap.add_argument("--out", default="data/monthly.csv")
    a = ap.parse_args()

    cpi = load(a.cpi_new)
    for p in reversed(a.cpi_old):
        cpi = splice(load(p), cpi)

    df = pd.DataFrame({
        "brent_usd": load(a.brent),
        "pump_price_kes": load(a.pump) if a.pump else np.nan,
        "cpi_index": cpi,
        "kes_per_usd": load(a.fx),
        "tbill91_pct": load(a.tbill),
    }).sort_index()
    df.index.name = "date"
    full = pd.date_range(df.index.min(), df.index.max(), freq="ME")
    df = df.reindex(full)
    df.index.name = "date"
    core = ["brent_usd", "cpi_index", "kes_per_usd", "tbill91_pct"]
    gaps = df[core].isna().sum()
    print("Months:", len(df), "| first:", df.index.min().date(), "| last:", df.index.max().date())
    print("Missing values per core series:\n", gaps.to_string())
    problems = []
    for c in ["brent_usd", "cpi_index", "kes_per_usd", "pump_price_kes"]:
        v = df[c].dropna()
        if (v <= 0).any():
            problems.append(f"{c}: zero or negative values")
        jumps = v.pct_change().abs()
        if (jumps > 0.5).any():
            problems.append(f"{c}: month-to-month change above 50% at {[str(d.date()) for d in jumps[jumps > 0.5].index[:5]]} (check units, rebasing or typos)")
    if not df.index.is_unique:
        problems.append("duplicate dates after merging")
    for p_ in problems:
        print("WARNING:", p_)
    if not problems:
        print("Basic checks passed (this does not prove the data are right).")
    df.to_csv(a.out)
    print("Wrote", a.out)
