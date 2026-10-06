"""
Estimate the fiscal reaction: how the primary balance responds to lagged debt.

    pb(t) = a + phi * debt(t-1) [+ b * output_gap(t)] + e(t)

Usage: python estimate_frf.py --annual data/annual.csv
annual.csv needs columns fy_end, debt, pb; an optional output_gap column is used if present.
Writes frf_result.json with phi and its standard error. It does NOT edit fiscal_inputs.json:
review the result, then copy phi across yourself.
With about 20 annual observations the estimate is imprecise. Report it with its standard error.
"""
import argparse
import json
import warnings

import pandas as pd
import statsmodels.api as sm


def estimate(annual: pd.DataFrame):
    d = annual.sort_values("fy_end").copy()
    d["debt_lag"] = d["debt"].shift(1)
    cols = ["debt_lag"] + (["output_gap"] if "output_gap" in d.columns else [])
    d = d.dropna(subset=cols + ["pb"])
    if len(d) < 10:
        raise ValueError(f"Only {len(d)} usable years; too few to estimate a fiscal reaction.")
    if len(d) < 20:
        warnings.warn(f"{len(d)} annual observations: treat the estimate as indicative only.")
    m = sm.OLS(d["pb"], sm.add_constant(d[cols])).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
    return m, len(d)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--annual", required=True)
    a = ap.parse_args()
    m, n = estimate(pd.read_csv(a.annual))
    res = {"phi": float(m.params["debt_lag"]), "se": float(m.bse["debt_lag"]), "n": int(n)}
    with open("frf_result.json", "w") as f:
        json.dump(res, f, indent=2)
    print(m.summary().tables[1])
    print(f"\nphi = {res['phi']:.4f} (SE {res['se']:.4f}), N = {n}. Wrote frf_result.json")
