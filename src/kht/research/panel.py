"""Build a regular bar panel from the sparse price history.

The Data API serves quoted *midpoints* on a fixed UTC grid but skips buckets in
which nothing changed, so each market's series is re-indexed onto the full grid
and forward-filled. The result is one long, sorted table:

    market_id | bar (int, grid index since epoch) | p (mid of outcome 0)

plus per-market arrays (first/last bar) that make it cheap to compute leads and
lags without ever crossing a market boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Panel:
    """Dense per-market bars stored as flat arrays (sorted by market, bar)."""

    bar_seconds: int
    market_id: np.ndarray  # int64, one entry per row
    bar: np.ndarray        # int64 grid index: ts // bar_seconds
    p: np.ndarray          # float64 midpoint of outcome 0
    start: np.ndarray      # row offset where each market begins (len = n_markets)
    stop: np.ndarray       # row offset one past each market's last row
    ids: np.ndarray        # market ids in panel order (len = n_markets)

    @property
    def n_rows(self) -> int:
        return len(self.p)

    @property
    def ts(self) -> np.ndarray:
        return self.bar * self.bar_seconds

    def row_market_index(self) -> np.ndarray:
        """Index (0..n_markets-1) of the market each row belongs to."""
        return np.repeat(np.arange(len(self.ids)), self.stop - self.start)

    def shift(self, values: np.ndarray, k: int) -> np.ndarray:
        """Per-market shift. ``k > 0`` looks back (lag), ``k < 0`` looks ahead (lead).

        Rows whose shifted position falls outside their own market get NaN.
        """
        out = np.full(len(values), np.nan)
        if k == 0:
            return values.astype(float).copy()
        idx = np.arange(len(values))
        src = idx - k
        mi = self.row_market_index()
        lo = self.start[mi]
        hi = self.stop[mi]
        ok = (src >= lo) & (src < hi)
        out[ok] = values[src[ok]]
        return out

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame({"market_id": self.market_id, "bar": self.bar, "p": self.p})


def build_panel(
    prices: pd.DataFrame,
    bar_seconds: int,
    cutoff_ts: dict[int, float] | pd.Series | None = None,
    min_bars: int = 8,
) -> Panel:
    """Regularise sparse ``(market_id, ts, price)`` rows into a dense panel.

    ``cutoff_ts`` optionally truncates each market at a timestamp (e.g. game
    start, so that a sports panel contains pre-game perception only).
    """
    prices = prices.sort_values(["market_id", "ts"])
    mids = prices["market_id"].to_numpy()
    bars = (prices["ts"].to_numpy() // bar_seconds).astype(np.int64)
    px = prices["price"].to_numpy(dtype=np.float64)
    # boundaries of each market in the sparse table
    change = np.flatnonzero(np.diff(mids)) + 1
    starts = np.concatenate(([0], change))
    stops = np.concatenate((change, [len(mids)]))
    if cutoff_ts is not None and not isinstance(cutoff_ts, dict):
        cutoff_ts = cutoff_ts.to_dict()

    out_mid: list[np.ndarray] = []
    out_bar: list[np.ndarray] = []
    out_p: list[np.ndarray] = []
    ids: list[int] = []
    lens: list[int] = []
    for s, e in zip(starts, stops):
        mid = int(mids[s])
        b = bars[s:e]
        v = px[s:e]
        # several ticks can share a bucket (the terminal tick); keep the last
        keep = np.concatenate((b[1:] != b[:-1], [True]))
        b, v = b[keep], v[keep]
        if cutoff_ts is not None:
            cut = cutoff_ts.get(mid)
            if cut is not None and cut == cut:  # not NaN
                sel = b * bar_seconds < cut
                b, v = b[sel], v[sel]
        if len(b) < 2:
            continue
        n = int(b[-1] - b[0] + 1)
        if n < min_bars:
            continue
        dense = np.full(n, np.nan)
        dense[b - b[0]] = v
        # forward fill
        last_valid = np.where(~np.isnan(dense), np.arange(n), 0)
        np.maximum.accumulate(last_valid, out=last_valid)
        dense = dense[last_valid]
        out_mid.append(np.full(n, mid, np.int64))
        out_bar.append(np.arange(b[0], b[0] + n, dtype=np.int64))
        out_p.append(dense)
        ids.append(mid)
        lens.append(n)
    lens_arr = np.asarray(lens, dtype=np.int64)
    stop = np.cumsum(lens_arr)
    start = stop - lens_arr
    return Panel(
        bar_seconds=bar_seconds,
        market_id=np.concatenate(out_mid) if out_mid else np.empty(0, np.int64),
        bar=np.concatenate(out_bar) if out_bar else np.empty(0, np.int64),
        p=np.concatenate(out_p) if out_p else np.empty(0),
        start=start,
        stop=stop,
        ids=np.asarray(ids, dtype=np.int64),
    )
