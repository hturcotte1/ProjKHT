"""The pre-registered tests H1-H8 from docs/01_thinking_session.md.

Every function takes the analysis table from ``dataset.make_dataset`` and
returns a tidy DataFrame of estimates with cluster-robust t-statistics.
All price changes are in probability points; the reports multiply by 100 to
show cents per share.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .dataset import tradable
from .stats import calibration_slope, mean_cluster, ols_cluster

JUMP_BINS = [0.0, 0.005, 0.01, 0.02, 0.04, 0.08, 0.15, 1.0]
PRICE_BINS = [0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]


def _split_half(df: pd.DataFrame) -> tuple[pd.Series, float]:
    """Boolean mask for the earlier half of the sample (by calendar time)."""
    cut = float(df["ts"].median())
    return df["ts"] <= cut, cut


# --------------------------------------------------------------------- H1
def h1_momentum(df: pd.DataFrame, by_category: bool = True, skip: bool = True) -> pd.DataFrame:
    """Slope of the next-k change on the past-j change, for every (j, k)."""
    horizons = df.attrs["horizons"]
    base = df[tradable(df)]
    groups: list[tuple[str, pd.DataFrame]] = [("all", base)]
    if by_category:
        groups += [(str(c), g) for c, g in base.groupby("category") if len(g) > 5_000]
    fwd = "fs_" if skip else "f_"
    rows = []
    for gname, g in groups:
        for j in horizons:
            for k in horizons:
                x = g[f"b_{j}"].to_numpy()
                y = g[f"{fwd}{k}"].to_numpy()
                ok = np.isfinite(x) & np.isfinite(y)
                if ok.sum() < 2_000:
                    continue
                r = ols_cluster(y[ok], x[ok], g["cluster"].to_numpy()[ok], g["day"].to_numpy()[ok], names=["past"])
                rows.append({"group": gname, "past": j, "next": k, "beta": r.beta[1], "se": r.se[1],
                             "t": r.t[1], "n": r.n, "clusters": r.n_clusters, "r2": r.r2})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- H2
def h2_jump_response(df: pd.DataFrame, past: str, nexts: list[str], skip: bool = True,
                     group_col: str | None = None) -> pd.DataFrame:
    """Continuation after a move, by the size of the move.

    ``cont`` is the next change measured *in the direction of the past move*:
    positive = the move kept going (momentum), negative = it gave some back.
    """
    base = df[tradable(df)].copy()
    move = base[f"b_{past}"].to_numpy()
    base["abs_move"] = np.abs(move)
    base = base[base["abs_move"] > 0]
    sign = np.sign(base[f"b_{past}"].to_numpy())
    fwd = "fs_" if skip else "f_"
    rows = []
    groups = [("all", base)] if group_col is None else [(str(k), g) for k, g in base.groupby(group_col)]
    for gname, g in groups:
        s = np.sign(g[f"b_{past}"].to_numpy())
        bins = pd.cut(g["abs_move"], JUMP_BINS)
        for k in nexts:
            cont = s * g[f"{fwd}{k}"].to_numpy()
            for level in bins.cat.categories:
                sel = (bins == level).to_numpy()
                if sel.sum() < 300:
                    continue
                r = mean_cluster(cont[sel], g["cluster"].to_numpy()[sel], g["day"].to_numpy()[sel])
                rows.append({"group": gname, "past": past, "next": k, "abs_move": str(level),
                             "cont": r.mean, "se": r.se, "t": r.t, "n": r.n, "clusters": r.n_clusters})
    del sign
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- H3
def snapshots(df: pd.DataFrame, days_before: list[float], anchor: str = "closed_ts") -> pd.DataFrame:
    """One row per market per snapshot: the last bar at least ``d`` days before the anchor."""
    out = []
    lead = (df[anchor] - df["ts"]) / 86_400
    for d in days_before:
        sub = df[(lead >= d) & df["payoff"].notna()]
        if sub.empty:
            continue
        last = sub.groupby("market_id")["bar"].idxmax()
        snap = df.loc[last].copy()
        # keep only snapshots that are actually near the requested lead
        gap = (snap[anchor] - snap["ts"]) / 86_400 - d
        snap = snap[gap <= max(1.0, 0.5 * d)]
        snap["lead_days"] = d
        out.append(snap)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def h3_calibration(snap: pd.DataFrame, group_col: str = "category", lo: float = 0.02, hi: float = 0.98) -> pd.DataFrame:
    rows = []
    snap = snap[(snap["p"] >= lo) & (snap["p"] <= hi)]
    for lead, s_lead in snap.groupby("lead_days"):
        groups = [("all", s_lead)] + [(str(k), g) for k, g in s_lead.groupby(group_col)]
        for gname, g in groups:
            if len(g) < 300:
                continue
            a, b, se_a, se_b = calibration_slope(g["p"].to_numpy(), g["payoff"].to_numpy(), g["cluster"].to_numpy())
            rows.append({"lead_days": lead, "group": gname, "slope": b, "se": se_b, "t_vs_1": (b - 1) / se_b,
                         "intercept": a, "se_a": se_a, "n": len(g), "clusters": g["cluster"].nunique()})
    return pd.DataFrame(rows)


def h3_price_bins(snap: pd.DataFrame, value: str = "to_res") -> pd.DataFrame:
    """Mean of ``value`` by price bin of the *favoured side* view: each market is
    looked at from both sides, so the table is symmetric by construction and
    answers 'what does a contract quoted at x cents go on to do?'."""
    a = snap[["p", value, "cluster", "day", "lead_days", "category"]].copy()
    b = a.copy()
    b["p"] = 1 - b["p"]
    b[value] = -b[value]
    both = pd.concat([a, b], ignore_index=True)
    rows = []
    for lead, s in both.groupby("lead_days"):
        bins = pd.cut(s["p"], PRICE_BINS, include_lowest=True)
        for level in bins.cat.categories:
            sel = (bins == level).to_numpy()
            if sel.sum() < 200:
                continue
            r = mean_cluster(s[value].to_numpy()[sel], s["cluster"].to_numpy()[sel], s["day"].to_numpy()[sel])
            rows.append({"lead_days": lead, "price_bin": str(level), "mean": r.mean, "se": r.se, "t": r.t,
                         "n": r.n, "avg_price": float(s["p"].to_numpy()[sel].mean())})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- H4
def h4_yes_drift(df: pd.DataFrame, nexts: list[str]) -> pd.DataFrame:
    """Unconditional drift of the 'Yes' token in Yes/No markets."""
    base = df[(df["outcome0"] == "Yes") & tradable(df)]
    rows = []
    groups = [("all", base)] + [(str(c), g) for c, g in base.groupby("category") if len(g) > 5_000]
    for gname, g in groups:
        for k in nexts + ["to_res"]:
            col = k if k == "to_res" else f"f_{k}"
            r = mean_cluster(g[col].to_numpy(), g["cluster"].to_numpy(), g["day"].to_numpy())
            rows.append({"group": gname, "horizon": k, "mean": r.mean, "se": r.se, "t": r.t, "n": r.n,
                         "clusters": r.n_clusters, "avg_price": float(g["p"].mean())})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- H5
def pregame_table(df: pd.DataFrame, leads_hours: list[int]) -> pd.DataFrame:
    """One row per sports game market: price of outcome 0 at fixed leads before kickoff."""
    bar_h = df.attrs["bar_seconds"] / 3600
    g = df[(df["category"] == "sports") & df["game_start_ts"].notna() & df["payoff"].notna()].copy()
    g["lead_h"] = (g["game_start_ts"] - g["ts"]) / 3600
    g = g[g["lead_h"] > 0]
    rows = {}
    close = g.loc[g.groupby("market_id")["bar"].idxmax()].set_index("market_id")
    out = close[["cluster", "payoff", "category", "sports_type", "game_start_ts", "volume", "fee_rate", "question"]].copy()
    out["p_close"] = close["p"]
    out["close_lead_h"] = close["lead_h"]
    for h in leads_hours:
        sub = g[g["lead_h"] >= h]
        idx = sub.groupby("market_id")["bar"].idxmax()
        snap = sub.loc[idx].set_index("market_id")
        ok = snap["lead_h"] - h < bar_h + 1e-9          # a bar really near that lead
        rows[h] = snap.loc[ok, "p"]
        out[f"p_{h}h"] = rows[h]
    out["day"] = (out["game_start_ts"] // 86_400).astype(int)
    return out.reset_index()


def h5_pregame(tab: pd.DataFrame, ref_h: int, early_h: int) -> dict[str, pd.DataFrame]:
    """Pre-game drift of the favourite, momentum into kickoff, and whether the
    pre-game move is confirmed by results."""
    t = tab.dropna(subset=[f"p_{ref_h}h", "p_close"]).copy()
    fav = np.where(t[f"p_{ref_h}h"] >= 0.5, 1.0, -1.0)      # which side is favoured at the reference time
    t["fav_p_ref"] = np.where(fav > 0, t[f"p_{ref_h}h"], 1 - t[f"p_{ref_h}h"])
    t["fav_move_late"] = fav * (t["p_close"] - t[f"p_{ref_h}h"])
    t["fav_won"] = np.where(fav > 0, t["payoff"], 1 - t["payoff"])
    t["fav_p_close"] = np.where(fav > 0, t["p_close"], 1 - t["p_close"])
    t = t[(t["fav_p_ref"] < 0.95)]
    res: dict[str, pd.DataFrame] = {}

    rows = []
    for name, g in [("all", t)] + [(str(k), v) for k, v in t.groupby(pd.cut(t["fav_p_ref"], [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]), observed=True)]:
        r = mean_cluster(g["fav_move_late"].to_numpy(), g["cluster"].to_numpy(), g["day"].to_numpy())
        rows.append({"fav_price": name, "window": f"T-{ref_h}h..close", "mean_move": r.mean, "se": r.se, "t": r.t, "n": r.n})
    res["favourite_drift"] = pd.DataFrame(rows)

    e = t.dropna(subset=[f"p_{early_h}h"]).copy()
    e["early_move"] = e[f"p_{ref_h}h"] - e[f"p_{early_h}h"]
    e["late_move"] = e["p_close"] - e[f"p_{ref_h}h"]
    e["total_move"] = e["p_close"] - e[f"p_{early_h}h"]
    e["surprise"] = e["payoff"] - e["p_close"]
    rows = []
    r = ols_cluster(e["late_move"].to_numpy(), e["early_move"].to_numpy(), e["cluster"].to_numpy(), e["day"].to_numpy(), names=["early"])
    rows.append({"test": f"late move (T-{ref_h}h..close) on early move (T-{early_h}h..T-{ref_h}h)",
                 "beta": r.beta[1], "se": r.se[1], "t": r.t[1], "n": r.n})
    r = ols_cluster(e["surprise"].to_numpy(), e["total_move"].to_numpy(), e["cluster"].to_numpy(), e["day"].to_numpy(), names=["move"])
    rows.append({"test": f"result minus close on total pre-game move (T-{early_h}h..close)",
                 "beta": r.beta[1], "se": r.se[1], "t": r.t[1], "n": r.n})
    e["surprise_ref"] = e["payoff"] - e[f"p_{ref_h}h"]
    r = ols_cluster(e["surprise_ref"].to_numpy(), e["early_move"].to_numpy(), e["cluster"].to_numpy(), e["day"].to_numpy(), names=["move"])
    rows.append({"test": f"result minus T-{ref_h}h price on early move (T-{early_h}h..T-{ref_h}h)",
                 "beta": r.beta[1], "se": r.se[1], "t": r.t[1], "n": r.n})
    res["momentum_and_confirmation"] = pd.DataFrame(rows)

    rows = []
    for label, col in [("close", "p_close"), (f"T-{ref_h}h", f"p_{ref_h}h"), (f"T-{early_h}h", f"p_{early_h}h")]:
        s = tab.dropna(subset=[col, "payoff"])
        s = s[(s[col] > 0.02) & (s[col] < 0.98)]
        a, b, se_a, se_b = calibration_slope(s[col].to_numpy(), s["payoff"].to_numpy(), s["cluster"].to_numpy())
        rows.append({"snapshot": label, "slope": b, "se": se_b, "t_vs_1": (b - 1) / se_b, "n": len(s)})
    res["calibration"] = pd.DataFrame(rows)
    return res


# --------------------------------------------------------------------- H6
def h6_calendar(df: pd.DataFrame, horizon: str) -> pd.DataFrame:
    """Mean change of the favoured side by weekday and by hour of day (UTC),
    reported separately for the two halves of the sample."""
    base = df[tradable(df)].copy()
    base["fav_change"] = np.sign(base["p"] - 0.5) * base[f"f_{horizon}"]
    when = pd.to_datetime(base["ts"], unit="s")
    base["weekday"] = when.dt.dayofweek
    base["hour"] = when.dt.hour
    first, _ = _split_half(base)
    rows = []
    for dim in ("weekday", "hour"):
        for level, g in base.groupby(dim):
            row = {"dim": dim, "level": int(level)}
            for half, mask in (("h1", first.loc[g.index]), ("h2", ~first.loc[g.index])):
                s = g[mask.to_numpy()]
                r = mean_cluster(s["fav_change"].to_numpy(), s["cluster"].to_numpy(), s["day"].to_numpy())
                row[f"mean_{half}"] = r.mean
                row[f"t_{half}"] = r.t
                row[f"n_{half}"] = r.n
            rows.append(row)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- H7
DEADLINE_RE = r"\b(?:by|before)\b"


def h7_deadline(df: pd.DataFrame, nexts: list[str]) -> pd.DataFrame:
    """Drift of 'will X happen by/before <date>' markets versus other Yes/No markets."""
    base = df[(df["outcome0"] == "Yes") & tradable(df) & (df["category"] != "sports") & (df["category"] != "crypto")].copy()
    base["deadline"] = base["question"].str.contains(DEADLINE_RE, case=False, regex=True, na=False)
    rows = []
    for flag, g in base.groupby("deadline"):
        for k in nexts + ["to_res"]:
            col = k if k == "to_res" else f"f_{k}"
            r = mean_cluster(g[col].to_numpy(), g["cluster"].to_numpy(), g["day"].to_numpy())
            rows.append({"deadline_market": bool(flag), "horizon": k, "mean": r.mean, "se": r.se, "t": r.t,
                         "n": r.n, "clusters": r.n_clusters, "avg_price": float(g["p"].mean())})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- H8
def h8_new_market(df: pd.DataFrame, horizon: str) -> pd.DataFrame:
    """Does the favoured side drift up more when the market is young?"""
    base = df[tradable(df)].copy()
    base["fav_change"] = np.sign(base["p"] - 0.5) * base[f"f_{horizon}"]
    base["fav_to_res"] = np.sign(base["p"] - 0.5) * base["to_res"]
    rows = []
    for level, g in base.groupby(pd.cut(base["age_days"], [-0.01, 1, 3, 7, 14, 30, 90, 10_000]), observed=True):
        r = mean_cluster(g["fav_change"].to_numpy(), g["cluster"].to_numpy(), g["day"].to_numpy())
        r2 = mean_cluster(g["fav_to_res"].to_numpy(), g["cluster"].to_numpy(), g["day"].to_numpy())
        rows.append({"age_days": str(level), f"fav_change_{horizon}": r.mean, "t": r.t,
                     "fav_to_res": r2.mean, "t_to_res": r2.t, "n": r.n,
                     "avg_fav_price": float(np.where(g["p"] >= 0.5, g["p"], 1 - g["p"]).mean())})
    return pd.DataFrame(rows)
