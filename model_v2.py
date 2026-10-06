"""
Version 2 model: joint VAR shocks, fiscal reaction, scenarios and backtest.

Inputs (all real data, supplied by the user):
  data/monthly.csv      from build_monthly.py
  data/quarterly.csv    columns: date, real_gdp_growth_yoy
  data/annual.csv       columns: fy_end, debt, dom, ext, i_dom, i_ext, pb
                        fy_end = year in which the fiscal year ends (FY2013/14 -> 2014)
                        debt, dom, ext in % of GDP; i_dom, i_ext effective rates in %; pb % of GDP (+ = surplus)

Run:  python model_v2.py --monthly data/monthly.csv --gdp data/quarterly.csv --annual data/annual.csv \
                        --horizon 5 --threshold 75 --origins 2014 2019 2022
Outputs: fan_chart_data.csv, scenarios.csv, backtest.csv, backtest_summary.csv
No result is meaningful unless inputs are real, complete series.
"""
import argparse, json, os
from dataclasses import dataclass
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

VARS = ["d_oil", "infl", "d_fx", "d_tb", "growth"]


@dataclass
class Fiscal:
    debt0: float = 69.4
    dom_share0: float = 0.563
    i_dom: float = 11.0
    i_ext: float = 4.5
    pb: float = -0.5
    tb0: float = 9.0              # 91-day T-bill level at the start, %
    phi: float = 0.0              # primary balance response to debt (pp of GDP per pp of debt)
    yield_beta: float = 1.0       # pass-through of T-bill changes to the effective domestic rate
    dom_fin_share: float = 0.7
    consolidation: float = 0.0    # extra pb improvement per year, pp of GDP


def _qidx(s):
    s = s.copy()
    s.index = s.index.to_period("Q").to_timestamp(how="end").normalize()
    return s


def quarterly_panel(monthly_csv, gdp_csv):
    m = pd.read_csv(monthly_csv, parse_dates=["date"]).set_index("date").sort_index()
    q = pd.DataFrame({
        "oil": _qidx(m["brent_usd"].resample("QE").mean()),
        "cpi": _qidx(m["cpi_index"].resample("QE").mean()),
        "fx": _qidx(m["kes_per_usd"].resample("QE").mean()),
        "tb": _qidx(m["tbill91_pct"].resample("QE").mean()),
    })
    g = pd.read_csv(gdp_csv, parse_dates=["date"]).set_index("date").sort_index()["real_gdp_growth_yoy"]
    q["growth"] = _qidx(g)
    out = pd.DataFrame({
        "d_oil": np.log(q.oil).diff() * 100,
        "infl": np.log(q.cpi).diff() * 100,
        "d_fx": np.log(q.fx).diff() * 100,
        "d_tb": q.tb.diff(),
        "growth": q.growth,
        "tb_level": q.tb,
    })
    return out


def fit_var(panel, maxlags=4):
    p = panel[VARS].dropna()
    res = VAR(p).fit(maxlags=maxlags, ic="aic")
    if res.k_ar < 1:
        res = VAR(p).fit(1)
    return res, p


def simulate_var(res, p, nq, n, block=4, oil_shock_pct=0.0, seed=0):
    """Block-bootstrap joint residuals through the VAR. oil_shock_pct is an extra oil
    shock in quarter 1, propagated to other variables with the oil-first Cholesky column."""
    rng = np.random.default_rng(seed)
    resid = res.resid.values
    T, K = resid.shape
    k = res.k_ar
    coefs, const = res.coefs, res.intercept
    shocks = np.zeros((n, nq, K))
    for b in range(int(np.ceil(nq / block))):
        starts = rng.integers(0, T - block + 1, size=n)
        for j in range(block):
            i = b * block + j
            if i < nq:
                shocks[:, i, :] = resid[starts + j]
    if oil_shock_pct:
        L = np.linalg.cholesky(np.cov(resid.T))
        shocks[:, 0, :] += L[:, 0] / L[0, 0] * oil_shock_pct
    hist = np.repeat(p.values[-k:][None, :, :], n, axis=0)
    out = np.zeros((n, nq, K))
    for s in range(nq):
        y = np.tile(const, (n, 1))
        for l in range(k):
            y = y + hist[:, -1 - l, :] @ coefs[l].T
        y = y + shocks[:, s, :]
        out[:, s, :] = y
        hist = np.concatenate([hist[:, 1:, :], y[:, None, :]], axis=1)
    return out


def annualise(out):
    n, nq, K = out.shape
    H = nq // 4
    r = out[:, :H * 4, :].reshape(n, H, 4, K)
    return {"infl": r[..., 1].sum(2), "dep": r[..., 2].sum(2), "dtb": r[..., 3].sum(2),
            "g": r[..., 4].mean(2), "oil": r[..., 0].sum(2)}


def run_debt(ann, f: Fiscal):
    n, H = ann["infl"].shape
    dom = np.full(n, f.debt0 * f.dom_share0)
    ext = np.full(n, f.debt0 * (1 - f.dom_share0))
    tb_change = np.cumsum(ann["dtb"], axis=1)
    path = np.zeros((n, H + 1))
    path[:, 0] = f.debt0
    for t in range(H):
        gn = (1 + ann["g"][:, t] / 100) * (1 + ann["infl"][:, t] / 100) - 1
        i_d = f.i_dom + f.yield_beta * tb_change[:, t]
        pb = f.pb + f.phi * (dom + ext - f.debt0) + f.consolidation * (t + 1)
        dom = dom * (1 + i_d / 100) / (1 + gn) - f.dom_fin_share * pb
        ext = ext * (1 + f.i_ext / 100) * (1 + ann["dep"][:, t] / 100) / (1 + gn) - (1 - f.dom_fin_share) * pb
        path[:, t + 1] = dom + ext
    return path


def forecast(panel, f, horizon, n=5000, oil_shock_pct=0.0, seed=0):
    res, p = fit_var(panel)
    out = simulate_var(res, p, horizon * 4, n, oil_shock_pct=oil_shock_pct, seed=seed)
    return run_debt(annualise(out), f)


def backtest(panel, annual, origins, horizon=5, n=2000, base: Fiscal = None):
    base = base or Fiscal()
    rows = []
    for o in origins:
        cutoff = pd.Timestamp(f"{o}-06-30")
        pan = panel.loc[:cutoff]
        a = annual.loc[o]
        f = Fiscal(**{**base.__dict__, "debt0": a["debt"], "dom_share0": a["dom"] / a["debt"],
                      "i_dom": a["i_dom"], "i_ext": a["i_ext"], "pb": a["pb"],
                      "tb0": float(pan["tb_level"].dropna().iloc[-1])})
        sims = forecast(pan, f, horizon, n=n)
        for h in range(1, horizon + 1):
            if (o + h) not in annual.index:
                continue
            actual = annual.loc[o + h, "debt"]
            s = sims[:, h]
            q = np.percentile(s, [10, 25, 50, 75, 90])
            rows.append({"origin": o, "horizon": h, "actual": actual, "median": q[2],
                         "in_50": q[1] <= actual <= q[3], "in_80": q[0] <= actual <= q[4],
                         "pit": float((s <= actual).mean())})
    bt = pd.DataFrame(rows)
    summ = bt.groupby("horizon").agg(n=("actual", "size"), cover_50=("in_50", "mean"),
                                     cover_80=("in_80", "mean"), mean_pit=("pit", "mean")).reset_index()
    return bt, summ


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--monthly", required=True)
    ap.add_argument("--gdp", required=True)
    ap.add_argument("--annual", required=True)
    ap.add_argument("--fiscal", default="fiscal_inputs.json")
    ap.add_argument("--horizon", type=int, default=5)
    ap.add_argument("--threshold", type=float, default=75.0)
    ap.add_argument("--origins", type=int, nargs="*", default=[])
    ap.add_argument("--n", type=int, default=5000)
    a = ap.parse_args()

    panel = quarterly_panel(a.monthly, a.gdp)
    fj = {k: v for k, v in json.load(open(a.fiscal)).items() if v is not None and not k.startswith("_")} if os.path.exists(a.fiscal) else {}
    f = Fiscal(**{**Fiscal().__dict__, **fj})
    if "tb0" not in fj:
        f.tb0 = float(panel["tb_level"].dropna().iloc[-1])

    base = forecast(panel, f, a.horizon, n=a.n)
    q = np.percentile(base, [10, 25, 50, 75, 90], axis=0)
    pd.DataFrame(q.T, columns=["p10", "p25", "p50", "p75", "p90"]).to_csv("fan_chart_data.csv", index_label="year")

    rows = []
    for label, shock in [("Oil -20% shock", -20.0), ("Baseline (no extra shock)", 0.0), ("Oil +20% shock", 20.0), ("Oil +40% shock", 40.0)]:
        for cons in [0.0, 0.5, 1.0]:
            ff = Fiscal(**{**f.__dict__, "consolidation": cons})
            s = forecast(panel, ff, a.horizon, n=a.n, oil_shock_pct=shock)
            rows.append({"scenario": label, "extra_consolidation_pp": cons, "median_end": round(float(np.median(s[:, -1])), 1),
                         "p_above_end": round(float((s[:, -1] > a.threshold).mean()), 3),
                         "p_above_any": round(float((s[:, 1:].max(1) > a.threshold).mean()), 3)})
    pd.DataFrame(rows).to_csv("scenarios.csv", index=False)

    if a.origins:
        annual = pd.read_csv(a.annual).set_index("fy_end")
        bt, summ = backtest(panel, annual, a.origins, a.horizon, n=min(a.n, 2000), base=f)
        bt.to_csv("backtest.csv", index=False)
        summ.to_csv("backtest_summary.csv", index=False)
        print(summ.round(2).to_string(index=False))
    print("Wrote fan_chart_data.csv, scenarios.csv" + (", backtest.csv, backtest_summary.csv" if a.origins else ""))
