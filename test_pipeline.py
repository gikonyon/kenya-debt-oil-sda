import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import pandas as pd
import pytest

pytest.importorskip("statsmodels")
from estimate import estimate_monthly
from estimate_frf import estimate as frf
import model_v2 as m2


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    d = tmp_path_factory.mktemp("data")
    rng = np.random.default_rng(5)
    idx = pd.date_range("2003-01-31", "2026-06-30", freq="ME")
    n = len(idx)
    lnp = np.zeros(n); lnp[0] = np.log(30)
    for t in range(1, n):
        lnp[t] = lnp[t - 1] + 0.03 * (np.log(70) - lnp[t - 1]) + 0.07 * rng.standard_normal()
    dl = np.r_[0, np.diff(lnp)]
    pd.DataFrame(dict(
        date=idx, brent_usd=np.exp(lnp), pump_price_kes=np.nan,
        cpi_index=100 * np.exp(np.cumsum(0.005 + 0.02 * dl + 0.003 * rng.standard_normal(n))),
        kes_per_usd=70 * np.exp(np.cumsum(0.003 + 0.03 * dl + 0.004 * rng.standard_normal(n))),
        tbill91_pct=8 + np.cumsum(0.06 * dl + 0.03 * rng.standard_normal(n)),
    )).to_csv(d / "monthly.csv", index=False)
    q = pd.date_range("2003-03-31", "2026-06-30", freq="QE")
    pd.DataFrame(dict(date=q, real_gdp_growth_yoy=5 + rng.standard_normal(len(q)))).to_csv(d / "q.csv", index=False)
    yrs = np.arange(2004, 2027)
    debt = 40 + np.cumsum(rng.normal(1.2, 1.0, len(yrs)))
    pd.DataFrame(dict(fy_end=yrs, debt=debt, dom=debt / 2, ext=debt / 2, i_dom=10.0, i_ext=4.0,
                      pb=-1 + rng.normal(0, 1, len(yrs)))).to_csv(d / "annual.csv", index=False)
    return d


def test_estimate_runs_and_skips_empty_pump(synth):
    params, table = estimate_monthly(str(synth / "monthly.csv"))
    assert "Pump price (%)" not in set(table["Channel"])
    assert {"b_pi", "b_fx", "oil_vol", "oil_reversion"} <= set(params)
    assert (table["CI low"] <= table["CI high"]).all()


def test_frf_runs(synth):
    model, n = frf(pd.read_csv(synth / "annual.csv"))
    assert n >= 10 and "debt_lag" in model.params


def test_model_v2_forecast_and_backtest(synth):
    panel = m2.quarterly_panel(str(synth / "monthly.csv"), str(synth / "q.csv"))
    f = m2.Fiscal()
    sims = m2.forecast(panel, f, 3, n=300)
    assert sims.shape == (300, 4) and np.isfinite(sims).all()
    annual = pd.read_csv(synth / "annual.csv").set_index("fy_end")
    bt, summ = m2.backtest(panel, annual, [2014, 2019], horizon=3, n=300, base=f)
    assert {"cover_50", "cover_80", "mean_pit"} <= set(summ.columns)
