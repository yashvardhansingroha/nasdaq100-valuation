"""Unit tests for the meta-portfolio engine (offline fixtures)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from meta_portfolio.allocator import (
    compute_dynamic_weights,
    inverse_vol_weights,
    max_diversification_weights,
    minimum_variance_weights,
)
from meta_portfolio.backtest import portfolio_log_return, run_backtest
from meta_portfolio.costs import apply_transaction_costs, daily_turnover
from meta_portfolio.data_loader import load_fixture_returns, prices_to_log_returns
from meta_portfolio.export_excel import export_workbook
from meta_portfolio.metrics import historical_var
from meta_portfolio.risk_engine import rolling_covariance, rolling_volatility


@pytest.fixture
def returns() -> pd.DataFrame:
    return load_fixture_returns(n_days=250, seed=7)


def test_prices_to_log_returns():
    prices = pd.DataFrame(
        {"A": [100.0, 101.0, 100.0], "B": [50.0, 50.5, 51.0]},
        index=pd.bdate_range("2020-01-01", periods=3),
    )
    r = prices_to_log_returns(prices)
    assert len(r) == 2
    assert abs(r["A"].iloc[0] - np.log(1.01)) < 1e-12


def test_rolling_vol_warmup(returns):
    vol = rolling_volatility(returns, window=60)
    assert vol.iloc[:59].isna().all().all()
    assert vol.iloc[59:].notna().all().all()


def test_rolling_cov_shape(returns):
    cov = rolling_covariance(returns, window=60)
    assert cov.index.nlevels == 2
    last = returns.index[-1]
    block = cov.loc[last]
    assert block.shape == (3, 3)


def test_inverse_vol_shrinks_high_vol():
    w = inverse_vol_weights(np.array([0.30, 0.10, 0.20]))
    assert abs(w.sum() - 1.0) < 1e-10
    assert w[1] > w[0]  # lower vol → higher weight


def test_min_var_bounds():
    cov = np.array(
        [
            [0.04, 0.01, 0.0],
            [0.01, 0.01, 0.0],
            [0.0, 0.0, 0.09],
        ]
    )
    w = minimum_variance_weights(cov, weight_min=0.05, weight_max=0.60)
    assert abs(w.sum() - 1.0) < 1e-6
    assert (w >= 0.05 - 1e-8).all()
    assert (w <= 0.60 + 1e-8).all()


def test_max_div_runs():
    cov = np.eye(3) * 0.04
    vols = np.array([0.2, 0.2, 0.2])
    w = max_diversification_weights(cov, vols)
    assert abs(w.sum() - 1.0) < 1e-6


def test_dynamic_weights_no_lookahead_sum(returns):
    methods = compute_dynamic_weights(returns, window=60)
    for name, w in methods.items():
        valid = w.dropna(how="any")
        assert len(valid) > 0, name
        sums = valid.sum(axis=1)
        assert np.allclose(sums, 1.0, atol=1e-5), name


def test_turnover_and_costs_zero_when_flat():
    idx = pd.bdate_range("2020-01-01", periods=5)
    w = pd.DataFrame({"A": 0.5, "B": 0.5}, index=idx)
    t = daily_turnover(w)
    assert t.iloc[1:].sum() == 0.0
    gross = pd.Series(0.01, index=idx)
    net, turnover, costs = apply_transaction_costs(gross, w, cost_rate=0.001)
    assert costs.sum() == 0.0
    assert np.allclose(net, gross)


def test_known_turnover_cost():
    idx = pd.bdate_range("2020-01-01", periods=2)
    w = pd.DataFrame({"A": [1.0, 0.0], "B": [0.0, 1.0]}, index=idx)
    # turnover day 1 = |0-1| + |1-0| = 2
    gross = pd.Series([0.0, 0.05], index=idx)
    net, turnover, costs = apply_transaction_costs(gross, w, cost_rate=0.001)
    assert abs(turnover.iloc[1] - 2.0) < 1e-12
    assert abs(costs.iloc[1] - 0.002) < 1e-12
    assert abs(net.iloc[1] - 0.048) < 1e-12


def test_backtest_runs(returns):
    result = run_backtest(returns, window=60)
    assert set(result.portfolio_net) >= {
        "InvVol",
        "MinVar",
        "MaxDiv",
        "EqualWeight",
        "60/40",
    }
    assert result.metrics is not None
    assert not result.metrics.empty
    # weights sum ~1 after warm-up
    w = result.weights["InvVol"].dropna(how="any")
    assert np.allclose(w.sum(axis=1), 1.0, atol=1e-5)


def test_portfolio_return_equal_weight():
    idx = pd.bdate_range("2020-01-01", periods=3)
    assets = pd.DataFrame(
        {"A": [0.0, np.log(1.01), np.log(1.02)], "B": [0.0, np.log(1.01), 0.0]},
        index=idx,
    )
    w = pd.DataFrame({"A": 0.5, "B": 0.5}, index=idx)
    port = portfolio_log_return(w, assets)
    # day1: 0.5*0.01 + 0.5*0.01 = 0.01 simple → log1p
    assert abs(port.iloc[1] - np.log(1.01)) < 1e-10


def test_historical_var_percentile():
    r = pd.Series(np.linspace(-0.05, 0.05, 101))
    var = historical_var(r, confidence=0.95, log_input=False)
    # 5th percentile of linspace(-0.05, 0.05, 101) ≈ -0.05 + 0.05*(5/100) wait
    # quantile at 0.05 of 101 points
    expected = float(np.quantile(r, 0.05))
    assert abs(var - expected) < 1e-12
    assert var < 0


def test_excel_export(returns, tmp_path):
    result = run_backtest(returns, window=60)
    out = export_workbook(result, path=tmp_path / "test.xlsx")
    assert out.exists()
    xl = pd.ExcelFile(out)
    assert set(xl.sheet_names) >= {
        "Returns",
        "Weights",
        "Performance",
        "Regimes",
        "Attribution",
    }
    perf = pd.read_excel(out, sheet_name="Performance", index_col=0)
    assert "VaR 95% (1d)" in perf.columns
