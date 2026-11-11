"""Thousands of rules of one fixed form, run fast and counted honestly.

A rule (docs/06_polymarket_us.md, section 3):

    In markets of family F, buy side S when its ask is in band B, with time T
    left, spread at most W and condition C on how it got there. Buy at the
    next observed ask if it is still in the band, pay the fee, hold to
    settlement. One purchase per market.

A venue is turned into a ``Table``: one row per outcome per day, sorted by
series and time, carrying what was known that day and what buying on the
next observation would have cost and paid. ``Table.run`` evaluates every
rule of a grid against it with array operations, so that tens of thousands of
rules take minutes. The same grid runs on polymarket.com and on Polymarket
US; only the table differs.

Nothing here chooses a rule. ``screen`` and ``family_threshold`` are the two
halves of the judge described in docs/06_polymarket_us.md, section 4.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterator

import numpy as np
import pandas as pd

BANDS = ((0.02, 0.05), (0.05, 0.10), (0.10, 0.20), (0.20, 0.35), (0.35, 0.50), (0.50, 0.65), (0.65, 0.80), (0.80, 0.90),
         (0.90, 0.95), (0.95, 0.98), (0.98, 0.995),
         (0.02, 0.10), (0.10, 0.35), (0.35, 0.65), (0.50, 0.90), (0.65, 0.90), (0.80, 0.95), (0.90, 0.98), (0.95, 0.99), (0.90, 0.99))
TIMES = ((1, 3), (3, 10), (10, 30), (30, 60), (60, 180), (3, 60), (3, 30), (10, 60))      # days to the scheduled end
SPREADS = (0.02, 0.05, None)                                                              # None: any spread
CONDITIONS = ("none", "quiet", "rose", "fell")
SHAPES = ("alone", "leg")
SIDES = ("yes", "no")
CATEGORIES = ("all", "politics", "geopolitics", "culture", "economy", "tech", "weather")
ENTRY_SLACK = 0.005          # the next ask may sit this far above the band and still be taken, as in every earlier round


@dataclass(frozen=True)
class RuleSpec:
    category: str
    shape: str
    side: str
    band: tuple[float, float]
    time: tuple[float, float]
    spread: float | None
    condition: str

    @property
    def name(self) -> str:
        w = "any" if self.spread is None else f"{100 * self.spread:g}c"
        return (f"{self.category}|{self.shape}|{self.side}|{100 * self.band[0]:g}-{100 * self.band[1]:g}c|"
                f"{self.time[0]:g}-{self.time[1]:g}d|spread {w}|{self.condition}")


def grid() -> Iterator[RuleSpec]:
    for c, sh, sd, b, t, w, k in product(CATEGORIES, SHAPES, SIDES, BANDS, TIMES, SPREADS, CONDITIONS):
        yield RuleSpec(c, sh, sd, b, t, w, k)


def grid_size() -> int:
    return len(CATEGORIES) * len(SHAPES) * len(SIDES) * len(BANDS) * len(TIMES) * len(SPREADS) * len(CONDITIONS)


def clustered(r: np.ndarray, cluster: np.ndarray) -> tuple[float, float]:
    """Mean of ``r`` and its t-statistic with observations in one cluster counted as one bet."""
    n = len(r)
    if n < 2:
        return (float(r.mean()) if n else float("nan")), float("nan")
    mean = float(r.mean())
    _, inv = np.unique(cluster, return_inverse=True)
    g = int(inv.max()) + 1
    if g < 2:
        return mean, float("nan")
    s = np.bincount(inv, weights=r - mean, minlength=g)
    var = g / (g - 1) * float(np.dot(s, s)) / n**2
    return mean, (mean / var**0.5 if var > 0 else float("nan"))


def floored(r: np.ndarray, cost: np.ndarray, cluster: np.ndarray) -> tuple[float, float]:
    """Mean of ``r`` and a z-statistic whose variance cannot be smaller than the prices paid imply.

    A rule that buys at 97c and happens not to lose in the sample has returns
    that barely vary, and an ordinary t-statistic for it is enormous and means
    nothing (round two learned this as test A1). If the contracts were fairly
    priced after costs, a purchase at cost c would have a return with variance
    (1 - c) / c. The variance of the mean used here is the larger of the
    sample's clustered variance and that null variance. How strongly bets in
    one event move together is not assumed here; it is handled by judging
    against placebo worlds that keep that dependence (``Table.placebo_outcomes``).
    """
    n = len(r)
    if n < 2:
        return (float(r.mean()) if n else float("nan")), float("nan")
    mean = float(r.mean())
    _, inv = np.unique(cluster, return_inverse=True)
    g = int(inv.max()) + 1
    sample = float("nan")
    if g >= 2:
        s = np.bincount(inv, weights=r - mean, minlength=g)
        sample = g / (g - 1) * float(np.dot(s, s)) / n**2
    c = np.clip(cost, 1e-6, 1 - 1e-6)
    null = float(((1.0 - c) / c).sum()) / n**2
    var = max(null, sample) if np.isfinite(sample) else null
    return mean, (mean / var**0.5 if var > 0 else float("nan"))


class Table:
    """One venue's decision table. Build it with ``from_frame``.

    The frame needs one row per outcome per observation, with columns

        market_id, side (0 = "Yes", 1 = "No"), period (integer time, days),
        ask, spread (NaN if unknown), dte (days to the scheduled end),
        category (one of CATEGORIES except "all", or anything else),
        leg (bool: one answer of a question with several), yes_no (bool),
        quiet, rose, fell (bool conditions known at the row),
        next_ask (the ask at the next observation, NaN if there was none in time),
        next_period, fee_theta (fee = theta * p * (1 - p) a share),
        won (what the outcome paid), fair (a fair chance of this outcome at the row, for placebo runs),
        cluster (event), split (0 discovery, 1 validation, -1 unused).
    """

    def __init__(self, f: pd.DataFrame):
        f = f.sort_values(["market_id", "side", "period"], kind="stable").reset_index(drop=True)
        self.n = len(f)
        self.market = f["market_id"].to_numpy()
        self.side = f["side"].to_numpy()
        key = self.market.astype(np.int64) * 2 + self.side
        self.new_series = np.concatenate(([True], key[1:] != key[:-1]))
        self.series = np.cumsum(self.new_series) - 1
        self.ask = f["ask"].to_numpy(dtype=np.float64)
        self.spread = f["spread"].to_numpy(dtype=np.float64)
        self.dte = f["dte"].to_numpy(dtype=np.float64)
        self.next_ask = f["next_ask"].to_numpy(dtype=np.float64)
        self.next_period = f["next_period"].to_numpy(dtype=np.float64)
        theta = f["fee_theta"].to_numpy(dtype=np.float64)
        self.cost = self.next_ask + theta * self.next_ask * (1.0 - self.next_ask)
        self.won = f["won"].to_numpy(dtype=np.float64)
        self.fair = f["fair"].to_numpy(dtype=np.float64)
        self.cluster = f["cluster"].to_numpy()
        self.split = f["split"].to_numpy()
        self.week = np.floor(self.next_period / 7.0)
        cat = f["category"].to_numpy()
        self.masks_cat = {c: (np.ones(self.n, bool) if c == "all" else cat == c) for c in CATEGORIES}
        leg = f["leg"].to_numpy(dtype=bool)
        yn = f["yes_no"].to_numpy(dtype=bool)
        self.masks_shape = {"alone": ~leg, "leg": leg}
        self.masks_side = {"yes": (self.side == 0) & yn, "no": (self.side == 1) & yn}
        self.masks_cond = {"none": np.ones(self.n, bool), "quiet": f["quiet"].to_numpy(dtype=bool),
                           "rose": f["rose"].to_numpy(dtype=bool), "fell": f["fell"].to_numpy(dtype=bool)}
        ok = np.isfinite(self.next_ask) & np.isfinite(self.won) & (self.split >= 0)
        self.masks_band = {b: ok & (self.ask > b[0]) & (self.ask <= b[1]) & (self.next_ask > b[0]) & (self.next_ask <= b[1] + ENTRY_SLACK)
                           for b in BANDS}

    # ------------------------------------------------------------------ run
    def trades(self, spec: RuleSpec) -> np.ndarray:
        """Row numbers of the rule's purchases: the first qualifying row of each market's series."""
        m = (self.masks_band[spec.band] & self.masks_cat[spec.category] & self.masks_shape[spec.shape] & self.masks_side[spec.side]
             & self.masks_cond[spec.condition] & (self.dte > spec.time[0]) & (self.dte <= spec.time[1]))
        if spec.spread is not None:
            m &= self.spread <= spec.spread + 1e-9
        idx = np.flatnonzero(m)
        if not len(idx):
            return idx
        s = self.series[idx]
        return idx[np.concatenate(([True], s[1:] != s[:-1]))]

    def run(self, specs: list[RuleSpec] | None = None, won: np.ndarray | None = None, min_trades: int = 30) -> pd.DataFrame:
        """Every rule's trades, return and t-statistics in each split. ``won`` replaces the outcomes (placebo runs)."""
        won = self.won if won is None else won
        ret_all = (won - self.cost) / self.cost
        rows = []
        specs = list(grid()) if specs is None else specs
        by_base: dict[tuple, list[RuleSpec]] = {}
        for sp in specs:
            by_base.setdefault((sp.category, sp.shape, sp.side, sp.band), []).append(sp)
        for (c, sh, sd, b), group in by_base.items():
            base = np.flatnonzero(self.masks_band[b] & self.masks_cat[c] & self.masks_shape[sh] & self.masks_side[sd])
            if len(base) < min_trades:
                continue
            dte, spr, ser = self.dte[base], self.spread[base], self.series[base]
            conds = {k: self.masks_cond[k][base] for k in CONDITIONS}
            for sp in group:
                m = conds[sp.condition] & (dte > sp.time[0]) & (dte <= sp.time[1])
                if sp.spread is not None:
                    m &= spr <= sp.spread + 1e-9
                loc = np.flatnonzero(m)
                if len(loc) < min_trades:
                    continue
                s = ser[loc]
                idx = base[loc[np.concatenate(([True], s[1:] != s[:-1]))]]
                if len(idx) < min_trades:
                    continue
                row = {"rule": sp.name}
                r, cl, wk, split, cost = ret_all[idx], self.cluster[idx], self.week[idx], self.split[idx], self.cost[idx]
                lost = won[idx] == 0
                for tag, code in (("d", 0), ("v", 1)):
                    k = split == code
                    n = int(k.sum())
                    row[f"n_{tag}"] = n
                    if n >= 2:
                        mean, t_ev = clustered(r[k], cl[k])
                        _, t_wk = clustered(r[k], wk[k])
                        _, z_ev = floored(r[k], cost[k], cl[k])
                        _, z_wk = floored(r[k], cost[k], wk[k])
                        row[f"ret_{tag}"], row[f"t_event_{tag}"], row[f"t_week_{tag}"] = mean, t_ev, t_wk
                        row[f"z_event_{tag}"], row[f"z_week_{tag}"] = z_ev, z_wk
                        row[f"lost_{tag}"] = int(lost[k].sum())
                        row[f"cost_{tag}"] = float(cost[k].mean())
                rows.append(row)
        return pd.DataFrame(rows)

    def placebo_outcomes(self, rng: np.random.Generator) -> np.ndarray:
        """Outcomes redrawn so that every price is right.

        Each EVENT gets one draw, and an outcome pays if the draw falls on its
        side of the fair chance at the row. Markets in one event therefore win
        and lose together as much as their prices allow: "by June" cannot
        happen without "by December" happening too. That is the strongest
        dependence consistent with the prices, so a rule that piles into one
        event gets no credit for it.
        """
        ids, inv = np.unique(self.cluster, return_inverse=True)
        u = rng.random(len(ids))[inv]
        yes_fair = np.where(self.side == 0, self.fair, 1.0 - self.fair)
        yes_wins = u < yes_fair
        return np.where(self.side == 0, yes_wins, ~yes_wins).astype(np.float64)


def validation_z(t: Table, rows: list[np.ndarray], won: np.ndarray, split: int = 1) -> np.ndarray:
    """The week-clustered floored z of each rule's purchases in one split, under the outcomes ``won``."""
    out = np.full(len(rows), np.nan)
    for i, idx in enumerate(rows):
        k = idx[t.split[idx] == split]
        if len(k) >= 2:
            out[i] = floored((won[k] - t.cost[k]) / t.cost[k], t.cost[k], t.week[k])[1]
    return out


def family_threshold(t: Table, rows: list[np.ndarray], worlds: int, rng: np.random.Generator, level: float = 0.95,
                     split: int = 1) -> tuple[float, np.ndarray]:
    """The score the luckiest of these rules reaches in ``level`` of placebo worlds.

    The rules' purchases are fixed (they do not depend on outcomes); only the
    outcomes are redrawn, with every price right. In each world the largest
    validation z among the rules is recorded. A real z above the ``level``
    quantile of those maxima is beyond what the best of that many worthless
    rules produces, whatever their overlap.
    """
    maxima = np.full(worlds, np.nan)
    for b in range(worlds):
        z = validation_z(t, rows, t.placebo_outcomes(rng), split)
        if np.isfinite(z).any():
            maxima[b] = np.nanmax(z)
    return float(np.nanquantile(maxima, level)), maxima


def screen(res: pd.DataFrame, min_discovery: int = 150, min_ret: float = 0.005, min_z: float = 3.0) -> pd.Series:
    """Candidates (docs/06, section 4): in discovery, at least ``min_discovery`` trades, a mean
    return of at least ``min_ret`` and an event-clustered floored z of at least ``min_z``."""
    for col in ("n_d", "ret_d", "z_event_d"):
        if col not in res:
            return pd.Series(False, index=res.index)
    return (res["n_d"] >= min_discovery) & (res["ret_d"] >= min_ret) & (res["z_event_d"] >= min_z)
