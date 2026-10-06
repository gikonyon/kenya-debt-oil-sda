import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import pytest
from sim import Params, simulate, summarise, scenario_table


def flat(**kw):
    """No oil shock and oil at the reference price, so the macro variables stay at baseline."""
    base = dict(oil_vol=0.0, oil0=70.0, oil_mean=70.0, oil_ref=70.0)
    base.update(kw)
    return Params(**base)


def test_zero_shock_matches_hand_calculation():
    p = flat(horizon=3, pb=-1.0, phi=0.0)
    r = simulate(p, n=10)
    dom, ext = p.debt0 * p.dom_share0, p.debt0 * (1 - p.dom_share0)
    gn = (1 + p.g_base / 100) * (1 + p.pi_base / 100) - 1
    for t in range(1, 4):
        dom = dom * (1 + p.i_dom / 100) / (1 + gn) - p.dom_fin_share * p.pb
        ext = ext * (1 + p.i_ext / 100) * (1 + p.dep_base / 100) / (1 + gn) - (1 - p.dom_fin_share) * p.pb
    assert np.allclose(r["total"][:, -1], dom + ext)


def test_same_seed_same_result():
    a = simulate(Params(), n=500, seed=1)["total"]
    b = simulate(Params(), n=500, seed=1)["total"]
    assert np.array_equal(a, b)


def test_bigger_surplus_lowers_debt():
    low = simulate(flat(pb=0.0), n=10)["total"][:, -1].mean()
    high = simulate(flat(pb=1.0), n=10)["total"][:, -1].mean()
    assert high < low


def test_fiscal_response_lowers_debt_when_debt_rises():
    none = simulate(flat(pb=-2.0, phi=0.0), n=10)["total"][:, -1].mean()
    resp = simulate(flat(pb=-2.0, phi=0.1), n=10)["total"][:, -1].mean()
    assert resp < none


def test_higher_oil_raises_exchange_rate_pressure_on_external_debt():
    p_low = flat(b_pi=0.0, b_g=0.0, b_yield=0.0, b_fx=1.0, oil0=70.0, oil_mean=70.0)
    p_high = flat(b_pi=0.0, b_g=0.0, b_yield=0.0, b_fx=1.0, oil0=110.0, oil_mean=110.0)
    assert simulate(p_high, n=10)["total"][:, -1].mean() > simulate(p_low, n=10)["total"][:, -1].mean()


def test_summary_probabilities_are_valid():
    s = summarise(simulate(Params(), n=500), 75.0)
    assert 0 <= s["p_exceed_end"] <= s["p_exceed_any"] <= 1
    assert s["quantiles"].shape == (5, Params().horizon + 1)


def test_scenario_table_has_three_rows():
    assert len(scenario_table(Params(), 75.0, n=200)) == 3


def test_bad_inputs_rejected():
    with pytest.raises(ValueError):
        simulate(Params(horizon=0))
    with pytest.raises(ValueError):
        simulate(Params(dom_share0=1.5))
