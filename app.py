import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from sim import Params, simulate, summarise, scenario_table

st.set_page_config(page_title="Kenya debt and oil shocks", layout="wide")

st.title("Kenya: oil shocks, domestic debt and fiscal space")
st.caption(
    "Stochastic debt-to-GDP simulation. Companion to a working paper by Gikonyo Ndugu. "
    "Parameters marked (placeholder) are illustrative and will be replaced by estimates from the paper."
)

with st.sidebar:
    st.header("Starting position")
    debt0 = st.number_input("Public debt, % of GDP", 40.0, 120.0, 69.4, 0.1)
    dom_share = st.slider("Domestic share of debt", 0.2, 0.9, 0.563, 0.01)
    horizon = st.slider("Years ahead (from FY2026/27)", 3, 10, 5)
    threshold = st.number_input("Debt threshold, % of GDP (placeholder)", 40.0, 120.0, 75.0, 0.5)

    st.header("Oil")
    oil0 = st.slider("Oil price today, USD/bbl", 40, 150, 90)
    oil_mean = st.slider("Long-run oil price, USD/bbl", 40, 150, 80)
    oil_vol = st.slider("Oil volatility (annual)", 0.05, 0.60, 0.25, 0.01)

    st.header("Macro baseline")
    g_base = st.slider("Real growth at reference oil, %", 2.0, 7.0, 4.5, 0.1)
    pi_base = st.slider("Inflation at reference oil, %", 2.0, 12.0, 5.0, 0.1)
    dep_base = st.slider("Shilling depreciation at reference oil, %", -2.0, 10.0, 3.0, 0.1)

    st.header("Pass-through per 10% oil rise (placeholder)")
    b_pi = st.slider("Inflation, pp", 0.0, 1.5, 0.4, 0.05)
    b_g = st.slider("Growth loss, pp", 0.0, 1.0, 0.2, 0.05)
    b_fx = st.slider("Depreciation, pp", 0.0, 2.0, 0.5, 0.05)
    b_yield = st.slider("Domestic rate response to extra inflation", 0.0, 1.5, 0.5, 0.05)

    st.header("Fiscal stance (placeholder)")
    i_dom = st.slider("Effective interest rate, domestic %", 5.0, 16.0, 11.0, 0.1)
    i_ext = st.slider("Effective interest rate, external %", 1.0, 10.0, 4.5, 0.1)
    pb = st.slider("Primary balance, % of GDP (+ = surplus)", -5.0, 3.0, -0.5, 0.1)
    cons = st.slider("Extra consolidation per year, pp of GDP", 0.0, 1.5, 0.0, 0.1)
    n = st.select_slider("Simulated paths", [1000, 2000, 5000, 10000], 5000)

p = Params(
    debt0=debt0, dom_share0=dom_share, horizon=horizon, oil0=float(oil0), oil_mean=float(oil_mean),
    oil_vol=oil_vol, g_base=g_base, pi_base=pi_base, dep_base=dep_base, b_pi=b_pi, b_g=b_g,
    b_fx=b_fx, b_yield=b_yield, i_dom=i_dom, i_ext=i_ext, pb=pb, consolidation=cons,
)

res = simulate(p, n=n)
s = summarise(res, threshold)
years = [f"FY{2025 + t}/{str(26 + t)[-2:]}" if t else "Jun 2026" for t in range(horizon + 1)]

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
    st.pyplot(fig)
    st.write(
        f"Domestic debt is on average {s['dom_share_end']:.0%} of the total at the end of the horizon "
        f"(it starts at {dom_share:.0%})."
    )

with tab2:
    st.write("Same settings, with oil fixed at three starting prices and long-run levels.")
    st.dataframe(pd.DataFrame(scenario_table(p, threshold, n=min(n, 3000))), hide_index=True)

with tab3:
    st.markdown(
        """
**What this does.** Oil follows a mean-reverting log process. Each year's oil gap moves inflation,
real growth, the exchange rate and the domestic interest rate. Those feed a standard debt equation,
run separately for domestic and external debt:

`d(t) = d(t-1) x (1 + i) / (1 + g_nominal) - primary balance` (external debt also grows with depreciation).

**What it does not do yet.** The pass-through coefficients, interest rates, primary balance and financing
split are placeholders. Inflation lowers the debt ratio through nominal growth and raises it through
interest rates, so the net sign depends on the estimates. Do not quote outputs as forecasts until
the parameters come from estimated models and Treasury data.

**Starting position.** Debt of about 69% of GDP and a domestic share of about 56% reflect figures
reported by the National Treasury and CBK in 2026. Check them against the latest bulletin.
"""
    )
