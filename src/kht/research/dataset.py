"""Assemble the analysis table used by every hypothesis test.

One row per (market, bar), with backward and forward price changes at several
horizons and the market attributes needed for conditioning. Prices are quoted
midpoints of outcome 0; changes are in probability points (0.01 = 1 cent per
share).

Two grains are available from the Data API (checked 2026-11-10):

* 12-hour bars for the whole history (points at 00:00 and 12:00 UTC);
* 3-hour bars only from early July 2026 onward.

So there are two panels: a long, coarse one and a short, fine one.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .panel import Panel, build_panel

BAR_12H = 43_200
BAR_3H = 10_800
HORIZONS_12H = {"12h": 1, "1d": 2, "2d": 4, "3d": 6, "7d": 14, "14d": 28}
HORIZONS_3H = {"3h": 1, "6h": 2, "12h": 4, "1d": 8, "2d": 16, "3d": 24, "7d": 56}

META_COLS = ["market_id", "event_id", "category", "winner", "start_ts", "end_ts", "closed_ts",
             "game_start_ts", "volume", "outcome0", "outcome1", "sports_type", "neg_risk",
             "fee_rate", "is_game", "is_recurring", "question"]


def game_cutoffs(meta: pd.DataFrame) -> dict[int, float]:
    """Sports game markets are cut at kickoff: before it, the price is opinion;
    after it, the price is the scoreboard."""
    g = meta.loc[meta["game_start_ts"].notna() & (meta["category"] == "sports"), ["market_id", "game_start_ts"]]
    return dict(zip(g["market_id"].astype(int), g["game_start_ts"].astype(float)))


def three_hour_era_start(prices: pd.DataFrame) -> int:
    """First day on which 3-hour points are the norm rather than the exception."""
    off_grid = prices.loc[prices["ts"] % BAR_12H != 0, "ts"]
    if off_grid.empty:
        raise ValueError("no 3-hour points in the price table")
    per_day = (off_grid // 86_400).value_counts().sort_index()
    busy = per_day[per_day >= 0.25 * per_day.max()]
    return int(busy.index[0]) * 86_400


def make_dataset(
    prices: pd.DataFrame, meta: pd.DataFrame, grain: str = "12h", min_bars: int = 6
) -> tuple[pd.DataFrame, Panel]:
    if grain == "12h":
        bar_seconds, horizons = BAR_12H, HORIZONS_12H
        prices = prices.loc[prices["ts"] % BAR_12H == 0]
    elif grain == "3h":
        bar_seconds, horizons = BAR_3H, HORIZONS_3H
        prices = prices.loc[prices["ts"] >= three_hour_era_start(prices)]
    else:
        raise ValueError(grain)

    cutoffs = game_cutoffs(meta)
    pan = build_panel(prices, bar_seconds, cutoff_ts=cutoffs, min_bars=min_bars)
    df = pd.DataFrame({"market_id": pan.market_id, "bar": pan.bar, "p": pan.p})
    df["ts"] = df["bar"] * bar_seconds
    df = df.merge(meta[META_COLS], on="market_id", how="left")
    # payoff of outcome 0 at resolution, and the change still to come
    df["payoff"] = np.where(df["winner"] == 0, 1.0, np.where(df["winner"] == 1, 0.0, np.nan))
    df["to_res"] = df["payoff"] - df["p"]

    # Forward prices. A market that resolves inside the look-ahead window has
    # no bar there, and simply dropping those rows would throw away exactly the
    # cases where the big move happened (survivorship). Holding through
    # resolution pays the payoff, so that is the forward price. Game markets
    # are different on purpose: they are cut at kickoff, a time known in
    # advance, and their forward changes stay strictly pre-game.
    payoff = df["payoff"].to_numpy()
    pad = ~df["market_id"].isin(list(cutoffs)).to_numpy() & np.isfinite(payoff)

    def lead(k: int) -> np.ndarray:
        v = pan.shift(pan.p, -k)
        return np.where(np.isnan(v) & pad, payoff, v)

    p_next = lead(1)
    for name, k in horizons.items():
        df[f"b_{name}"] = pan.p - pan.shift(pan.p, k)        # change over the past k bars
        df[f"f_{name}"] = lead(k) - pan.p                    # change over the next k bars
        # enter one bar after the signal is observed (guards against stale quotes)
        df[f"fs_{name}"] = lead(k + 1) - p_next
    mi = pan.row_market_index()
    rows = np.arange(pan.n_rows)
    df["age_bars"] = rows - pan.start[mi]
    df["bars_left"] = pan.stop[mi] - 1 - rows

    # markets without an event are their own cluster
    df["cluster"] = np.where(df["event_id"] >= 0, df["event_id"], -df["market_id"])
    df["day"] = df["ts"] // 86_400
    df["days_to_end"] = (df["end_ts"] - df["ts"]) / 86_400
    df["days_to_game"] = (df["game_start_ts"] - df["ts"]) / 86_400
    df["age_days"] = df["age_bars"] * bar_seconds / 86_400
    df.attrs["horizons"] = horizons
    df.attrs["bar_seconds"] = bar_seconds
    return df, pan


def tradable(df: pd.DataFrame, lo: float = 0.05, hi: float = 0.95) -> pd.Series:
    """Rows where the market is still genuinely uncertain."""
    return (df["p"] >= lo) & (df["p"] <= hi)
