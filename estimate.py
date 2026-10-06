"""
Estimate the oil block of the debt model from real data and write params.json.

Usage:
    python estimate.py --monthly data/monthly.csv [--quarterly data/quarterly.csv]
                       [--start 2003-01 --end 2013-03 --tag kibaki]

monthly.csv columns (one row per month):
    date, brent_usd, pump_price_kes, cpi_index, kes_per_usd, tbill91_pct
    (pump_price_kes may be empty; that channel is then skipped)
quarterly.csv columns (optional, growth channel): date, brent_usd, real_gdp_growth_yoy

Method: local projections (Jorda 2005) with Newey-West standard errors. For each channel,
regress the h-step cumulative change on the 3-period change in log oil, controlling for the
lagged change in the dependent variable. Responses are reported per 10% oil rise, in the
units the simulation uses. The estimate is the average response over h periods and includes
the usual later movement in oil prices.
No result is meaningful unless the input data are real, complete series.
"""
import argparse
import json
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

REQUIRED_MONTHLY = ["date", "brent_usd", "cpi_index", "kes_per_usd", "tbill91_pct"]
MIN_OBS = 30


def local_projection(df, y, x, h, k_x=3, k_y=1):
    d = pd.DataFrame(index=df.index)
    d["dx"] = df[x].diff(k_x)
    d["y_fwd"] = df[y].shift(-h) - df[y].shift(k_x)
    d["y_lag"] = df[y].diff(k_y).shift(k_x)
    d = d.dropna()
    if len(d) < MIN_OBS:
        warnings.warn(f"{y}: only {len(d)} usable observations; estimate will be imprecise.")
    if len(d) < 10:
        raise ValueError(f"{y}: too few usable observations ({len(d)}). Check the sample window and gaps.")
    X = sm.add_constant(d[["dx", "y_lag"]])
    m = sm.OLS(d["y_fwd"], X).fit(cov_type="HAC", cov_kwds={"maxlags": h})
    return m, len(d)


def _row(label, b, se, n, scale):
    return {"Channel": label, "Response per 10% oil rise": b * scale, "SE": se * scale,
            "CI low": (b - 1.96 * se) * scale, "CI high": (b + 1.96 * se) * scale, "N": n}


def _read_monthly(path, start, end):
    df = pd.read_csv(path, parse_dates=["date"])
    missing = [c for c in REQUIRED_MONTHLY if c not in df.columns]
    if missing:
        raise ValueError(f"monthly file is missing columns: {missing}")
    df = df.sort_values("date").set_index("date")
    if start:
        df = df.loc[start:]
    if end:
        df = df.loc[:end]
    for c in ["brent_usd", "cpi_index", "kes_per_usd"]:
        if (df[c].dropna() <= 0).any():
            raise ValueError(f"{c} has zero or negative values; logs cannot be taken.")
    return df


def estimate_monthly(path, h=12, start=None, end=None):
    df = _read_monthly(path, start, end)
    for c in ["brent_usd", "pump_price_kes", "cpi_index", "kes_per_usd"]:
        if c in df.columns and df[c].notna().any():
            df["ln_" + c] = np.log(df[c])
    out, rows = {}, []
    scale = np.log(1.10) * 100

    channels = [("CPI, 12m (pp inflation)", "ln_cpi_index", "b_pi"),
                ("KES per USD (pp depreciation)", "ln_kes_per_usd", "b_fx")]
    if "ln_pump_price_kes" in df.columns:
        channels.insert(0, ("Pump price (%)", "ln_pump_price_kes", None))
    for label, y, key in channels:
        m, n = local_projection(df, y, "ln_brent_usd", h)
        b, se = m.params["dx"], m.bse["dx"]
        rows.append(_row(label, b, se, n, scale))
        if key:
            out[key] = float(b * scale)

    m, n = local_projection(df, "tbill91_pct", "ln_brent_usd", h)
    s10 = np.log(1.10)
    rows.append(_row("91-day T-bill (pp)", m.params["dx"], m.bse["dx"], n, s10))
    infl_resp = out.get("b_pi")
    if infl_resp and abs(infl_resp) > 1e-6:
        out["b_yield"] = float(m.params["dx"] * s10 / infl_resp)
    else:
        warnings.warn("Inflation response is ~0, so b_yield could not be computed.")

    ln_p = df["ln_brent_usd"].dropna()
    ar = sm.OLS(ln_p.iloc[1:].values, sm.add_constant(ln_p.iloc[:-1].values)).fit()
    c, phi = ar.params
    if not 0 < phi < 1:
        warnings.warn(f"AR(1) coefficient on log oil is {phi:.3f}; reversion estimates are unreliable.")
        phi = min(max(phi, 0.01), 0.999)
    sig_m = float(np.std(ar.resid, ddof=2))
    out["oil_reversion"] = float(1 - phi ** 12)
    out["oil_vol"] = float(sig_m * np.sqrt((1 - phi ** 24) / (1 - phi ** 2)))
    out["oil_mean"] = float(np.exp(c / (1 - phi)))
    out["oil_ref"] = float(np.exp(ln_p.mean()))
    return out, pd.DataFrame(rows)


def estimate_quarterly(path, h=4):
    df = pd.read_csv(path, parse_dates=["date"]).sort_values("date").set_index("date")
    df["ln_brent_usd"] = np.log(df["brent_usd"])
    d = pd.DataFrame(index=df.index)
    d["dx"] = df["ln_brent_usd"].diff(4)
    d["g_fwd"] = df["real_gdp_growth_yoy"].shift(-h)
    d["g_now"] = df["real_gdp_growth_yoy"]
    d = d.dropna()
    if len(d) < MIN_OBS:
        warnings.warn(f"growth channel: only {len(d)} usable observations.")
    m = sm.OLS(d["g_fwd"], sm.add_constant(d[["dx", "g_now"]])).fit(cov_type="HAC", cov_kwds={"maxlags": h})
    b, se, s = m.params["dx"], m.bse["dx"], np.log(1.10)
    row = _row("Real GDP growth, 4q ahead (pp)", b, se, len(d), s)
    return {"b_g": float(-b * s)}, pd.DataFrame([row])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--monthly", required=True)
    ap.add_argument("--quarterly")
    ap.add_argument("--start", help="first month, e.g. 2003-01")
    ap.add_argument("--end", help="last month, e.g. 2013-03")
    ap.add_argument("--tag", default="", help="suffix for output files, e.g. kibaki")
    a = ap.parse_args()
    params, table = estimate_monthly(a.monthly, start=a.start, end=a.end)
    if a.quarterly and not (a.start or a.end):
        p2, t2 = estimate_quarterly(a.quarterly)
        params.update(p2)
        table = pd.concat([table, t2], ignore_index=True)
    sfx = f"_{a.tag}" if a.tag else ""
    with open(f"params{sfx}.json", "w") as f:
        json.dump(params, f, indent=2)
    table.round(3).to_csv(f"results_table{sfx}.csv", index=False)
    print(table.round(3).to_string(index=False))
    print(f"\nWrote params{sfx}.json and results_table{sfx}.csv")


if __name__ == "__main__":
    main()
