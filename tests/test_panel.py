import numpy as np
import pandas as pd

from kht.research.panel import build_panel


def _prices():
    # market 1: bars 10, 11, 14 (gap -> forward fill); market 2: bars 5..9
    return pd.DataFrame(
        {
            "market_id": [1, 1, 1, 2, 2, 2, 2, 2],
            "ts": [1000, 1100, 1400, 500, 600, 700, 800, 900],
            "price": [0.50, 0.55, 0.70, 0.20, 0.21, 0.22, 0.23, 0.24],
        }
    )


def test_forward_fill_and_grid():
    pan = build_panel(_prices(), bar_seconds=100, min_bars=2)
    m1 = pan.p[pan.market_id == 1]
    assert np.allclose(m1, [0.50, 0.55, 0.55, 0.55, 0.70])
    assert list(pan.bar[pan.market_id == 1]) == [10, 11, 12, 13, 14]


def test_shift_never_crosses_markets():
    pan = build_panel(_prices(), bar_seconds=100, min_bars=2)
    lag1 = pan.shift(pan.p, 1)
    lead1 = pan.shift(pan.p, -1)
    for mid in (1, 2):
        rows = np.flatnonzero(pan.market_id == mid)
        assert np.isnan(lag1[rows[0]])           # nothing before a market's first bar
        assert np.isnan(lead1[rows[-1]])         # nothing after its last bar
        assert np.allclose(lag1[rows[1:]], pan.p[rows[:-1]])
        assert np.allclose(lead1[rows[:-1]], pan.p[rows[1:]])


def test_cutoff_truncates_at_timestamp():
    pan = build_panel(_prices(), bar_seconds=100, cutoff_ts={2: 800.0}, min_bars=2)
    m2 = pan.p[pan.market_id == 2]
    assert np.allclose(m2, [0.20, 0.21, 0.22])   # bars at ts 500, 600, 700 only


def test_duplicate_bucket_keeps_last_tick():
    df = pd.DataFrame({"market_id": [7, 7, 7], "ts": [100, 150, 200], "price": [0.1, 0.9, 0.3]})
    pan = build_panel(df, bar_seconds=100, min_bars=2)
    assert np.allclose(pan.p, [0.9, 0.3])


def test_forward_changes_pay_out_at_resolution_instead_of_vanishing():
    """A market that resolves inside the look-ahead window must not be dropped:
    the forward price is the payoff. Dropping it is survivorship bias."""
    from kht.research.dataset import META_COLS, make_dataset

    ts = [43_200 * i for i in range(1, 9)]
    prices = pd.DataFrame({"market_id": [1] * 8, "ts": ts, "price": [0.30] * 7 + [0.35]})
    meta = pd.DataFrame([{c: None for c in META_COLS}])
    meta["market_id"] = 1
    meta["event_id"] = 10
    meta["category"] = "politics"
    meta["winner"] = 0.0            # outcome 0 won -> payoff 1.0
    meta["game_start_ts"] = np.nan
    meta["is_recurring"] = False
    for c in ("start_ts", "end_ts", "closed_ts", "volume", "fee_rate"):
        meta[c] = 0.0
    df, _ = make_dataset(prices, meta, "12h")
    last = df.iloc[-1]
    assert last["f_1d"] == 1.0 - 0.35          # beyond the last bar -> payoff
    assert last["to_res"] == 1.0 - 0.35
    first = df.iloc[0]
    assert first["f_12h"] == 0.0               # inside the series -> next bar


def test_game_markets_stay_pre_game():
    from kht.research.dataset import META_COLS, make_dataset

    ts = [43_200 * i for i in range(1, 11)]
    prices = pd.DataFrame({"market_id": [2] * 10, "ts": ts, "price": [0.6] * 8 + [0.9, 1.0]})
    meta = pd.DataFrame([{c: None for c in META_COLS}])
    meta["market_id"] = 2
    meta["event_id"] = 20
    meta["category"] = "sports"
    meta["winner"] = 0.0
    meta["game_start_ts"] = float(43_200 * 8 + 100)   # kickoff just after bar 8
    meta["is_recurring"] = False
    for c in ("start_ts", "end_ts", "closed_ts", "volume", "fee_rate"):
        meta[c] = 0.0
    df, _ = make_dataset(prices, meta, "12h")
    assert df["p"].max() == 0.6                      # in-game bars are cut off
    assert np.isnan(df.iloc[-1]["f_12h"])            # no look past kickoff
    assert df.iloc[-1]["to_res"] == 1.0 - 0.6        # but resolution is still known
