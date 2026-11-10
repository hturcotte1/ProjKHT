"""The inference code is the foundation of every claim in the research notes,
so it is checked against statsmodels and against simulated ground truth."""

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from kht.research.stats import binned_means, calibration_slope, mean_cluster, ols_cluster


def _clustered_data(seed=0, n_clusters=200, per=15):
    rng = np.random.default_rng(seed)
    cl = np.repeat(np.arange(n_clusters), per)
    shock = rng.normal(size=n_clusters)[cl]          # common within-cluster shock
    x = rng.normal(size=len(cl)) + 0.5 * shock
    y = 0.3 * x + shock + rng.normal(size=len(cl))
    return y, x, cl


def test_ols_cluster_matches_statsmodels():
    y, x, cl = _clustered_data()
    ours = ols_cluster(y, x, cl, names=["x"])
    ref = sm.OLS(y, sm.add_constant(x)).fit(cov_type="cluster", cov_kwds={"groups": cl})
    assert np.allclose(ours.beta, ref.params, atol=1e-10)
    assert np.allclose(ours.se, ref.bse, rtol=1e-6)


def test_two_way_cluster_matches_statsmodels():
    y, x, cl = _clustered_data(seed=1)
    rng = np.random.default_rng(2)
    cl2 = rng.integers(0, 40, size=len(y))
    ours = ols_cluster(y, x, cl, cluster2=cl2, names=["x"])
    ref = sm.OLS(y, sm.add_constant(x)).fit(
        cov_type="cluster", cov_kwds={"groups": np.column_stack([cl, cl2])}
    )
    assert np.allclose(ours.beta, ref.params, atol=1e-10)
    # statsmodels applies a slightly different small-sample factor for two-way
    assert np.allclose(ours.se, ref.bse, rtol=0.02)


def test_cluster_se_is_larger_than_naive_when_clusters_matter():
    y, x, cl = _clustered_data(seed=3)
    clustered = ols_cluster(y, x, cl)
    naive = ols_cluster(y, x, np.arange(len(y)))  # every row its own cluster
    assert clustered.se[1] > 1.3 * naive.se[1]


def test_mean_cluster_has_correct_coverage():
    """A nominal 95% interval should cover the true mean ~95% of the time."""
    rng = np.random.default_rng(4)
    hits = 0
    trials = 400
    for _ in range(trials):
        cl = np.repeat(np.arange(60), 10)
        x = rng.normal(size=60)[cl] + 0.5 * rng.normal(size=600)  # true mean 0
        r = mean_cluster(x, cl)
        hits += abs(r.mean) <= 1.96 * r.se
    assert 0.90 <= hits / trials <= 0.985


def test_mean_cluster_ignores_nan():
    x = np.array([1.0, np.nan, 3.0, 5.0])
    r = mean_cluster(x, np.array([0, 0, 1, 2]))
    assert r.n == 3
    assert r.mean == pytest.approx(3.0)


def test_binned_means_recovers_group_means():
    df = pd.DataFrame({"g": ["a"] * 50 + ["b"] * 50, "v": [1.0] * 50 + [2.0] * 50, "c": list(range(100))})
    out = binned_means(df, "g", "v", "c")
    assert out.loc["a", "mean"] == pytest.approx(1.0)
    assert out.loc["b", "mean"] == pytest.approx(2.0)


def test_calibration_slope_recovers_compression():
    """Simulate prices compressed toward 50% and check the slope is recovered."""
    rng = np.random.default_rng(5)
    true_logit = rng.normal(0, 1.5, size=60_000)
    true_p = 1 / (1 + np.exp(-true_logit))
    quoted = 1 / (1 + np.exp(-true_logit / 1.25))   # market understates conviction
    won = (rng.random(len(true_p)) < true_p).astype(float)
    a, b, se_a, se_b = calibration_slope(quoted, won, np.arange(len(won)))
    assert b == pytest.approx(1.25, abs=4 * se_b)
    assert abs(a) < 4 * se_a


def test_calibration_slope_is_one_for_fair_prices():
    rng = np.random.default_rng(6)
    p = rng.uniform(0.05, 0.95, size=60_000)
    won = (rng.random(len(p)) < p).astype(float)
    _, b, _, se_b = calibration_slope(p, won, np.arange(len(p)))
    assert b == pytest.approx(1.0, abs=4 * se_b)
