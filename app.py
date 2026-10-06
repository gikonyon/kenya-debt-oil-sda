import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from sim import Params, simulate, summarise, scenario_table

st.set_page_config(page_title="Kenya debt and oil shocks", layout="wide")


def _load(path):
    """Read a JSON file of overrides; ignore nulls and notes. Missing or broken files give {}."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return {k: v for k, v in json.load(f).items() if v is not None and not k.startswith("_")}
    except (OSError, ValueError):
        return {}


ESTIMATED = _load("params.json")
FISCAL = _load("fiscal_inputs.json")
LOADED = {**ESTIMATED, **FISCAL}


def D(key, lo, hi, default):
    """Default for a control: loaded value if present, clipped to the slider range."""
    return float(min(max(LOADED.get(key, default), lo), hi))


@st.cache_data(show_spinner=False)
def run(params: dict, n: int, threshold: float):
    p = Params(**params)
    res = simulate(p, n=n)
    s = summarise(res, threshold)
    return s, scenario_table(p, threshold, n=min(n, 3000))


st.title("Kenya: oil shocks, domestic debt and fiscal space")
if ESTIMATED:
    st.caption("Companion to a working paper by Gikonyo Ndugu. Oil-block parameters were loaded from the paper's "
               "estimates (params.json). Anything not in fiscal_inputs.json is still a placeholder.")
else:
    st.caption("Companion to a working paper by Gikonyo Ndugu. No estimates are loaded yet, so pass-through "
               "coefficients, interest rates and the primary balance are illustrative placeholders. "
               "Do not quote the results as forecasts.")

with st.sidebar:
    st.header("Starting position")
    debt0 = st.number_input("Public debt, % of GDP", 40.0, 120.0, D("debt0", 40, 120, 69.4), 0.1)
    dom_share = st.slider("Domestic share of debt", 0.2, 0.9, D("dom_share0", 0.2, 0.9, 0.563), 0.01)
    horizon = st.slider("Years ahead (from FY2026/27)", 3, 10, 5)
    threshold = st.number_input("Debt threshold, % of GDP (placeholder)", 40.0, 120.0, 75.0, 0.5)

    st.header("Oil")
    oil0 = st.slider("Oil price today, USD/bbl", 40, 150, 90)
    oil_mean = st.slider("Long-run oil price, USD/bbl", 40, 150, int(D("oil_mean", 40, 150, 80)))
    oil_vol = st.slider("Oil volatility (annual)", 0.05, 0.60, D("oil_vol", 0.05, 0.60, 0.25), 0.01)

    st.header("Macro baseline")
    g_base = st.slider("Real growth at reference oil, %", 2.0, 7.0, 4.5, 0.1)
    pi_base = st.slider("Inflation at reference oil, %", 2.0, 12.0, 5.0, 0.1)
    dep_base = st.slider("Shilling depreciation at reference oil, %", -2.0, 10.0, 3.0, 0.1)

    st.header("Pass-through per 10% oil rise")
    b_pi = st.slider("Inflation, pp", 0.0, 1.5, D("b_pi", 0, 1.5, 0.4), 0.05)
    b_g = st.slider("Growth loss, pp", 0.0, 1.0, D("b_g", 0, 1.0, 0.2), 0.05)
    b_fx = st.slider("Depreciation, pp", 0.0, 2.0, D("b_fx", 0, 2.0, 0.5), 0.05)
    b_yield = st.slider("Domestic rate response to extra inflation", 0.0, 1.5, D("b_yield", 0, 1.5, 0.5), 0.05)

    st.header("Fiscal stance")
    i_dom = st.slider("Effective interest rate, domestic %", 5.0, 16.0, D("i_dom", 5, 16, 11.0), 0.1)
    i_ext = st.slider("Effective interest rate, external %", 1.0, 10.0, D("i_ext", 1, 10, 4.5), 0.1)
    pb = st.slider("Primary balance, % of GDP (+ = surplus)", -5.0, 3.0, D("pb", -5, 3, -0.5), 0.1)
    phi = st.slider("Fiscal response to debt (pp of GDP per pp of debt)", 0.0, 0.2, D("phi", 0, 0.2, 0.0), 0.01)
    cons = st.slider("Extra consolidation per year, pp of GDP", 0.0, 1.5, 0.0, 0.1)
    n = st.select_slider("Simulated paths", [1000, 2000, 5000, 10000], 5000)

params = dict(
    debt0=debt0, dom_share0=dom_share, horizon=horizon, oil0=float(oil0), oil_mean=float(oil_mean),
    oil_vol=oil_vol, g_base=g_base, pi_base=pi_base, dep_base=dep_base, b_pi=b_pi, b_g=b_g, b_fx=b_fx,
    b_yield=b_yield, i_dom=i_dom, i_ext=i_ext, pb=pb, phi=phi, consolidation=cons,
    oil_reversion=float(LOADED.get("oil_reversion", 0.5)), oil_ref=float(LOADED.get("oil_ref", 70.0)),
    dom_fin_share=float(LOADED.get("dom_fin_share", 0.7)),
)

if threshold <= debt0:
    st.warning("The threshold is at or below today's debt ratio, so threshold probabilities will be close to 100%.")

s, scen = run(params, n, threshold)
years = ["Jun 2026"] + [f"FY{2025 + t}/{str(26 + t)[-2:]}" for t in range(1, horizon + 1)]

c1, c2, c3 = st.columns(3)
c1.metric("Median debt/GDP at end", f"{s['median_end']:.1f}%")
c2.metric("Chance above threshold at end", f"{s['p_exceed_end']:.0%}")
c3.metric("Chance above threshold at any point", f"{s['p_exceed_any']:.0%}")

tab1, tab2, tab3 = st.tabs(["Debt fan chart", "Oil scenarios", "Method and limits"])

with tab1:
    q = s["quantiles"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.fill_between(years, q[0], q[4], alpha=0.2, label="10th to 90th percentile")
    ax.fill_between(years, q[1], q[3], alpha=0.4, label="25th to 75th percentile")
    ax.plot(years, q[2], linewidth=2, label="Median")
    ax.axhline(threshold, linestyle="--", linewidth=1, label=f"Threshold {threshold:.0f}%")
    ax.set_ylabel("Public debt, % of GDP")
    ax.legend(loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    plt.setp(ax.get_xticklabels(), rotation=0)
    st.pyplot(fig)
    plt.close(fig)
    st.write(f"Domestic debt is on average {s['dom_share_end']:.0%} of the total at the end of the horizon "
             f"(it starts at {dom_share:.0%}).")
    table = pd.DataFrame(q.T, columns=["p10", "p25", "p50", "p75", "p90"], index=years).round(2)
    st.download_button("Download fan chart data (CSV)", table.to_csv(index_label="period"),
                       file_name="fan_chart_data.csv", mime="text/csv")

with tab2:
    st.write("Same settings, with oil fixed at three starting prices and long-run levels.")
    st.dataframe(pd.DataFrame(scen), hide_index=True)

with tab3:
    st.markdown(
        """
**What this does.** Oil follows a mean-reverting log process. Each year's oil gap moves inflation,
real growth, the exchange rate and the domestic interest rate. Those feed a standard debt equation,
run separately for domestic and external debt:

`d(t) = d(t-1) x (1 + i) / (1 + g_nominal) - primary balance` (external debt also grows with depreciation).

The primary balance can respond to debt through the fiscal response setting. At zero the government
does nothing as debt climbs.

**What it does not do yet.** Unless estimates have been loaded (see the subtitle), the pass-through
coefficients, interest rates, primary balance and financing split are placeholders. Inflation lowers the
debt ratio through nominal growth and raises it through interest rates, so the net sign depends on
the estimates. Only oil shocks are random here. The full version adds joint shocks to growth, inflation,
the exchange rate and yields. Do not quote outputs as forecasts.

**Starting position.** Debt of about 69% of GDP and a domestic share of about 56% reflect figures
reported by the National Treasury and CBK in 2026. Check them against the latest bulletin.
"""
    )
