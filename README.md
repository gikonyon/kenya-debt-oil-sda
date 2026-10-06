# Kenya: oil shocks, domestic debt and fiscal space

Code companion to a working paper using a stochastic debt sustainability analysis.
Live app: https://kenya-debt-oil-sda-fadpeakie2aeberkbdnu2m.streamlit.app/

Status: the app runs on placeholder parameters until real estimates are loaded. Outputs are not forecasts.

## Files

| File | Purpose |
|---|---|
| `app.py`, `sim.py` | Streamlit app and its simple oil-shock simulation (needs only `requirements.txt`) |
| `build_monthly.py` | Merge downloaded series into `data/monthly.csv`, splice CPI base changes, run basic data checks |
| `estimate.py` | Pass-through estimates by local projections; writes `params.json` and `results_table.csv` (with confidence intervals) |
| `estimate_frf.py` | Fiscal reaction (primary balance response to debt); writes `frf_result.json` |
| `model_v2.py` | Full model: joint VAR shocks, fiscal reaction, oil scenarios, backtest |
| `fiscal_inputs.json` | Treasury/CBK inputs for the app and `model_v2.py` (leave `null` to keep defaults) |
| `tests/` | Automated checks. Run `python -m pytest -q tests` |

## Workflow

1. Download each series as a two-column CSV (date, value) into `raw/`.
2. `python build_monthly.py --brent raw/brent.csv --pump raw/pump.csv --fx raw/fx.csv --tbill raw/tbill.csv --cpi_old raw/cpi_old.csv --cpi_new raw/cpi_new.csv --out data/monthly.csv`
3. `pip install -r requirements-estimate.txt`, then `python estimate.py --monthly data/monthly.csv --quarterly data/quarterly.csv`
4. Era comparison: add `--start`, `--end`, `--tag` (for example `--start 2003-01 --end 2013-03 --tag kibaki`). The Ruto window is short, so read its estimates with care.
5. Prepare `data/annual.csv` (columns: fy_end, debt, dom, ext, i_dom, i_ext, pb; FY2013/14 is fy_end 2014). Run `python estimate_frf.py --annual data/annual.csv`.
6. Fill `fiscal_inputs.json` (including `phi` from step 5 if you accept it).
7. `python model_v2.py --monthly data/monthly.csv --gdp data/quarterly.csv --annual data/annual.csv --horizon 5 --threshold 75 --origins 2014 2019 2022`

## Cautions

- Do not commit `params.json` until it comes from real estimates. The app loads it automatically.
- The estimator reports the average response over 12 months, including later oil movements, not a one-off permanent shock.
- Backtests use final, revised data, and there are few independent origins.
- Check every input against the primary source. The tests use simulated data and prove the code runs, not that results are right.

## Development

    pip install -r requirements-dev.txt -r requirements-estimate.txt -r requirements.txt
    python -m pytest -q tests
