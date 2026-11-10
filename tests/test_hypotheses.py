"""The thesis tests must find an effect that is there and report none that is not."""

import numpy as np
import pandas as pd
import pytest

from kht.research import hypotheses as H
from kht.research.dataset import META_COLS, make_dataset

DAY = 86_400


def synthetic(rho: float, n_markets: int = 400, n_days: int = 80, seed: int = 0):
    """Daily mids whose increments have first-order autocorrelation ``rho``."""
    rng = np.random.default_rng(seed)
    rows, metas = [], []
    for m in range(1, n_markets + 1):
        eps = rng.normal(0, 0.012, n_days)
        inc = np.empty(n_days)
        inc[0] = eps[0]
        for t in range(1, n_days):
            inc[t] = rho * inc[t - 1] + eps[t]
        p = np.clip(0.5 + np.cumsum(inc), 0.08, 0.92)
        for t in range(n_days):
            rows.append((m, (1000 + t) * DAY, p[t]))
        meta = {c: None for c in META_COLS}
        meta.update(market_id=m, event_id=m, category="politics", winner=float(rng.integers(0, 2)),
                    game_start_ts=np.nan, is_recurring=False, start_ts=0.0, end_ts=2000.0 * DAY,
                    closed_ts=2000.0 * DAY, volume=1e6, fee_rate=0.0, question="q", outcome0="Yes", outcome1="No")
        metas.append(meta)
    return pd.DataFrame(rows, columns=["market_id", "ts", "price"]), pd.DataFrame(metas)


def slope(df, past="1d", nxt="1d"):
    r = H.h1_momentum(df, by_category=False, skip=False)
    row = r[(r["past"] == past) & (r["next"] == nxt)].iloc[0]
    return row["beta"], row["t"]


def test_random_walk_shows_no_momentum():
    prices, meta = synthetic(rho=0.0)
    d, _ = make_dataset(prices, meta, "1d")
    beta, t = slope(d)
    assert abs(t) < 3.5 and abs(beta) < 0.03


def test_planted_momentum_is_detected_with_the_right_size():
    prices, meta = synthetic(rho=0.25)
    d, _ = make_dataset(prices, meta, "1d")
    beta, t = slope(d)
    assert t > 10
    assert beta == pytest.approx(0.25, abs=0.05)


def test_planted_reversal_is_detected():
    prices, meta = synthetic(rho=-0.25)
    d, _ = make_dataset(prices, meta, "1d")
    beta, t = slope(d)
    assert t < -10 and beta == pytest.approx(-0.25, abs=0.05)


def test_jump_response_sign_follows_the_planted_effect():
    prices, meta = synthetic(rho=0.25, seed=3)
    d, _ = make_dataset(prices, meta, "1d")
    j = H.h2_jump_response(d, "1d", ["1d"], skip=False)
    big = j[j["abs_move"].isin(["(0.02, 0.04]", "(0.04, 0.08]"])]
    assert (big["cont"] > 0).all() and (big["t"] > 3).all()      # moves continue
    prices, meta = synthetic(rho=-0.25, seed=3)
    d, _ = make_dataset(prices, meta, "1d")
    j = H.h2_jump_response(d, "1d", ["1d"], skip=False)
    big = j[j["abs_move"].isin(["(0.02, 0.04]", "(0.04, 0.08]"])]
    assert (big["cont"] < 0).all()                                # moves give back
