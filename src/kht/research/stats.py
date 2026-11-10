"""Inference helpers for panel data where observations are not independent.

Markets inside one event move together, and every market moves on the same
calendar days, so naive standard errors are far too small. Everything here
uses cluster-robust (sandwich) covariance, optionally two-way (event x time)
following Cameron, Gelbach & Miller (2011).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def _codes(cluster: np.ndarray) -> tuple[np.ndarray, int]:
    codes, uniques = pd.factorize(cluster, sort=False)
    return codes, len(uniques)


def _meat(X: np.ndarray, resid: np.ndarray, cluster: np.ndarray) -> tuple[np.ndarray, int]:
    """Sum over clusters of (X_g' u_g)(X_g' u_g)'."""
    codes, g = _codes(cluster)
    scores = X * resid[:, None]
    k = X.shape[1]
    agg = np.zeros((g, k))
    for j in range(k):
        agg[:, j] = np.bincount(codes, weights=scores[:, j], minlength=g)
    return agg.T @ agg, g


@dataclass
class OlsResult:
    names: list[str]
    beta: np.ndarray
    se: np.ndarray
    n: int
    n_clusters: int
    r2: float

    @property
    def t(self) -> np.ndarray:
        return self.beta / self.se

    def table(self) -> pd.DataFrame:
        return pd.DataFrame({"beta": self.beta, "se": self.se, "t": self.t}, index=self.names)

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return f"OLS n={self.n} clusters={self.n_clusters} r2={self.r2:.5f}\n{self.table().round(5)}"


def ols_cluster(
    y: np.ndarray,
    X: np.ndarray,
    cluster: np.ndarray,
    cluster2: np.ndarray | None = None,
    names: list[str] | None = None,
    add_const: bool = True,
) -> OlsResult:
    """OLS with one-way or two-way cluster-robust standard errors."""
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    y, X, cluster = y[ok], X[ok], np.asarray(cluster)[ok]
    if cluster2 is not None:
        cluster2 = np.asarray(cluster2)[ok]
    if add_const:
        X = np.column_stack([np.ones(len(y)), X])
        names = ["const"] + (names or [f"x{i}" for i in range(X.shape[1] - 1)])
    else:
        names = names or [f"x{i}" for i in range(X.shape[1])]
    n, k = X.shape
    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    resid = y - X @ beta

    def cov(cl: np.ndarray) -> tuple[np.ndarray, int]:
        meat, g = _meat(X, resid, cl)
        adj = (g / max(g - 1, 1)) * ((n - 1) / max(n - k, 1))
        return adj * (xtx_inv @ meat @ xtx_inv), g

    v, g = cov(cluster)
    if cluster2 is not None:
        v2, g2 = cov(cluster2)
        inter = pd.factorize(pd.MultiIndex.from_arrays([cluster, cluster2]))[0]
        v12, _ = cov(inter)
        v = v + v2 - v12
        g = min(g, g2)
    se = np.sqrt(np.clip(np.diag(v), 0, None))
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float((resid**2).sum()) / tss if tss > 0 else float("nan")
    return OlsResult(names=names, beta=beta, se=se, n=n, n_clusters=g, r2=r2)


@dataclass
class MeanResult:
    mean: float
    se: float
    n: int
    n_clusters: int

    @property
    def t(self) -> float:
        return self.mean / self.se if self.se > 0 else float("nan")


def mean_cluster(x: np.ndarray, cluster: np.ndarray, cluster2: np.ndarray | None = None) -> MeanResult:
    """Mean with cluster-robust standard error (an intercept-only regression)."""
    x = np.asarray(x, dtype=float)
    ok = np.isfinite(x)
    if ok.sum() < 2:
        return MeanResult(float("nan"), float("nan"), int(ok.sum()), 0)
    res = ols_cluster(
        x[ok], np.empty((int(ok.sum()), 0)), np.asarray(cluster)[ok],
        None if cluster2 is None else np.asarray(cluster2)[ok],
    )
    return MeanResult(float(res.beta[0]), float(res.se[0]), res.n, res.n_clusters)


def binned_means(
    df: pd.DataFrame,
    by: str,
    value: str,
    cluster: str,
    bins: np.ndarray | list[float] | None = None,
    cluster2: str | None = None,
) -> pd.DataFrame:
    """Cluster-robust mean of ``value`` within bins of ``by``.

    If ``bins`` is None, ``by`` is treated as already categorical.
    """
    key = pd.cut(df[by], bins) if bins is not None else df[by]
    rows = []
    for level, sub in df.groupby(key, observed=True):
        r = mean_cluster(
            sub[value].to_numpy(), sub[cluster].to_numpy(),
            None if cluster2 is None else sub[cluster2].to_numpy(),
        )
        rows.append({by: level, "mean": r.mean, "se": r.se, "t": r.t, "n": r.n, "clusters": r.n_clusters})
    return pd.DataFrame(rows).set_index(by)


def calibration_slope(p: np.ndarray, won: np.ndarray, cluster: np.ndarray, iters: int = 50) -> tuple[float, float, float, float]:
    """Logistic recalibration ``logit(P(win)) = a + b * logit(p)``.

    Returns (a, b, se_a, se_b) with cluster-robust SEs. ``b > 1`` means prices
    are compressed toward 50% (favourites underpriced, longshots overpriced).
    """
    p = np.clip(np.asarray(p, dtype=float), 1e-4, 1 - 1e-4)
    y = np.asarray(won, dtype=float)
    ok = np.isfinite(p) & np.isfinite(y)
    p, y, cluster = p[ok], y[ok], np.asarray(cluster)[ok]
    X = np.column_stack([np.ones(len(p)), np.log(p / (1 - p))])
    beta = np.array([0.0, 1.0])
    for _ in range(iters):  # Newton-Raphson
        eta = X @ beta
        mu = 1.0 / (1.0 + np.exp(-eta))
        w = mu * (1 - mu)
        hess = X.T @ (X * w[:, None])
        step = np.linalg.solve(hess, X.T @ (y - mu))
        beta = beta + step
        if np.abs(step).max() < 1e-10:
            break
    mu = 1.0 / (1.0 + np.exp(-(X @ beta)))
    w = mu * (1 - mu)
    bread = np.linalg.inv(X.T @ (X * w[:, None]))
    meat, g = _meat(X, y - mu, cluster)
    v = (g / max(g - 1, 1)) * (bread @ meat @ bread)
    se = np.sqrt(np.diag(v))
    return float(beta[0]), float(beta[1]), float(se[0]), float(se[1])
