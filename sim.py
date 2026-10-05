"""
Stochastic debt simulation for Kenya: oil shocks, domestic debt and fiscal space.

IMPORTANT: Pass-through coefficients, interest rates, the primary balance and the
financing split below are ILLUSTRATIVE PLACEHOLDERS. They must be replaced with
estimates from the paper's VAR / pass-through regressions and Treasury data before
any result is quoted.
"""
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class Params:
    # Starting position (end-June 2026, Treasury/CBK figures reported in the paper)
    debt0: float = 69.4          # public debt, % of GDP
    dom_share0: float = 0.563    # domestic share of total debt
    horizon: int = 5             # years: FY2026/27 ... FY2030/31

    # Oil process (USD/bbl): mean-reverting log price with shocks
    oil0: float = 90.0
    oil_mean: float = 80.0
    oil_ref: float = 70.0        # reference price for "no shock" macro baseline
    oil_vol: float = 0.25        # annual std dev of log price shocks
    oil_reversion: float = 0.5   # speed of reversion to oil_mean

    # Macro baseline when oil == oil_ref (percent per year)
    g_base: float = 4.5
    pi_base: float = 5.0
    dep_base: float = 3.0

    # Pass-through per 10% oil price rise above oil_ref (PLACEHOLDERS)
    b_pi: float = 0.4            # pp added to inflation
    b_g: float = 0.2             # pp removed from real growth
    b_fx: float = 0.5            # pp added to depreciation
    b_yield: float = 0.5         # pp added to domestic rate per 1pp extra inflation

    # Effective interest rates, percent (PLACEHOLDERS: compute as interest / prior stock)
    i_dom: float = 11.0
    i_ext: float = 4.5

    # Fiscal stance, % of GDP; positive = surplus (PLACEHOLDER)
    pb: float = -0.5
    consolidation: float = 0.0   # extra primary balance improvement per year, pp of GDP
    dom_fin_share: float = 0.7   # share of primary deficit financed domestically


def simulate(p: Params, n: int = 5000, seed: int = 0):
    rng = np.random.default_rng(seed)
    H = p.horizon
    ln_p = np.full(n, np.log(p.oil0))
    ln_mean = np.log(p.oil_mean)
    dom = np.full(n, p.debt0 * p.dom_share0)
    ext = np.full(n, p.debt0 * (1 - p.dom_share0))

    total = np.zeros((n, H + 1))
    dom_path = np.zeros((n, H + 1))
    oil = np.zeros((n, H + 1))
    total[:, 0] = dom + ext
    dom_path[:, 0] = dom
    oil[:, 0] = p.oil0

    for t in range(1, H + 1):
        ln_p = ln_p + p.oil_reversion * (ln_mean - ln_p) + p.oil_vol * rng.standard_normal(n)
        price = np.exp(ln_p)
        x = np.log(price / p.oil_ref) / 0.10          # oil gap in units of 10%
        pi = p.pi_base + p.b_pi * x
        g = p.g_base - p.b_g * x
        dep = p.dep_base + p.b_fx * x
        i_d = p.i_dom + p.b_yield * (pi - p.pi_base)
        g_nom = (1 + g / 100) * (1 + pi / 100) - 1
        pb = p.pb + p.consolidation * t

        dom = dom * (1 + i_d / 100) / (1 + g_nom) - p.dom_fin_share * pb
        ext = ext * (1 + p.i_ext / 100) * (1 + dep / 100) / (1 + g_nom) - (1 - p.dom_fin_share) * pb

        total[:, t] = dom + ext
        dom_path[:, t] = dom
        oil[:, t] = price

    return {"total": total, "dom": dom_path, "oil": oil}


def summarise(res, threshold: float):
    total = res["total"]
    q = np.percentile(total, [10, 25, 50, 75, 90], axis=0)
    return {
        "quantiles": q,
        "p_exceed_end": float((total[:, -1] > threshold).mean()),
        "p_exceed_any": float((total[:, 1:].max(axis=1) > threshold).mean()),
        "median_end": float(q[2, -1]),
        "dom_share_end": float((res["dom"][:, -1] / total[:, -1]).mean()),
    }


def scenario_table(p: Params, threshold: float, n: int = 5000):
    rows = []
    for label, price in [("Low oil (USD 70)", 70.0), ("Central oil (USD 90)", 90.0), ("High oil (USD 110)", 110.0)]:
        q = Params(**{**asdict(p), "oil0": price, "oil_mean": price})
        s = summarise(simulate(q, n=n), threshold)
        rows.append({
            "Scenario": label,
            "Median debt/GDP at end (%)": round(s["median_end"], 1),
            "P(above threshold at end)": f"{s['p_exceed_end']:.0%}",
            "P(above threshold at any point)": f"{s['p_exceed_any']:.0%}",
        })
    return rows
