"""Track A of the second round: are quiet favourites cheaper than busy ones?

The rule, its control and the bar were fixed in docs/04_second_round.md
(section 4) before this script was run.

    A1  stand-alone markets; ask above 90c and at most 95c; scheduled end more
        than 3 and at most 60 days away; the outcome's traded range over the
        last 14 days is 3c or less and the market was already in the panel 14
        days ago. Buy at the next taker-buy print within 3 days, pay today's
        fee, hold to resolution. One trade per market.
    Control: the same on the first day an outcome is in the band and not quiet.
    Bar: A1 positive with |t| >= 3 (clustered by event) and above its control
         with |t| >= 2.

Everything else printed here (other bands, legs, resting bids, other ranges
and windows, splits) is reported alongside and chooses nothing.

    python scripts/run_quiet_favourites.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kht.backtest.harvest import Rule, candidate_trades, prepare
from kht.data.download import load_meta
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes
from kht.research.sports import build_trades_table
from kht.research.stats import mean_cluster, ols_cluster

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
SPLIT_TS = pd.Timestamp("2026-05-01", tz="UTC").timestamp()     # the first round's holdout: scheduled end before this


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for s in self.streams:
            s.write(text)

    def flush(self):
        for s in self.streams:
            s.flush()


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    meta = load_meta("closed")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    meta = meta[(~meta["category"].isin(["sports", "crypto"])) & (life >= 2) & resolved].copy()
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(build_trades_table(meta)), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    return meta, s


def trailing_range(s: pd.DataFrame, window: int) -> tuple[np.ndarray, np.ndarray]:
    """For every row: (highest - lowest traded price of this outcome over the
    ``window`` days ending on the row's day, whether the series was already in
    the panel on the first of those days)."""
    series = s["series"].to_numpy()
    period = s["period"].to_numpy()
    hi = np.fmax(s["ask_hi"].to_numpy(), s["bid_hi"].to_numpy())
    lo = np.fmin(s["ask_lo"].to_numpy(), s["bid_lo"].to_numpy())
    rng = np.full(len(s), np.nan)
    seasoned = np.zeros(len(s), dtype=bool)
    change = np.flatnonzero(np.diff(series)) + 1
    for a, b in zip(np.concatenate(([0], change)), np.concatenate((change, [len(series)]))):
        per = period[a:b]
        start = np.searchsorted(per, per - (window - 1), side="left")
        h, l = hi[a:b], lo[a:b]
        for i in range(b - a):
            j = start[i]
            rng[a + i] = np.nanmax(h[j:i + 1]) - np.nanmin(l[j:i + 1])
        seasoned[a:b] = per[0] <= per - (window - 1)
    return rng, seasoned


def stats(t: pd.DataFrame) -> dict:
    if len(t) < 20:
        return {"trades": len(t)}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    return {"trades": len(t), "events": int(t["cluster"].nunique()),
            "win%": 100 * float((t["proceeds"] > t["cost"]).mean()), "lost": int((t["won"] == 0).sum()),
            "avg_cost": float(t["cost"].mean()), "avg_ret%": 100 * r.mean, "se%": 100 * r.se, "t_event": r.t,
            "med_dte": float(t["dte_at_signal"].median()), "med_hold_d": float(t["hold"].median())}


def gap(a: pd.DataFrame, b: pd.DataFrame) -> tuple[float, float]:
    """Mean return of ``a`` minus mean return of ``b`` and its event-clustered t."""
    both = pd.concat([a.assign(flag=1.0), b.assign(flag=0.0)], ignore_index=True)
    res = ols_cluster(both["ret"].to_numpy(), both[["flag"]].to_numpy(), both["cluster"].to_numpy())
    return float(res.beta[1]), float(res.beta[1] / res.se[1])


def main() -> None:
    meta, s = load()
    single = ~meta.set_index("market_id")["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    ask = s["ask"].to_numpy()
    dte = s["days_to_end"].to_numpy()
    dte_ok = (dte > 3) & (dte <= 60)
    hold_of = s.groupby("market_id")["end_ts"].first() < SPLIT_TS
    rng14, seasoned14 = trailing_range(s, 14)
    s["range14"] = rng14

    def band(lo: float, hi: float) -> np.ndarray:
        return (ask > lo) & (ask <= hi) & dte_ok

    def trades(rule: Rule, signal: np.ndarray) -> pd.DataFrame:
        t = candidate_trades(s, rule, signal=signal)
        if t.empty:
            return t
        key = pd.MultiIndex.from_frame(t[["market_id", "side", "signal_period"]])
        t["range14"] = pd.Series(rng14, index=pd.MultiIndex.from_frame(s[["market_id", "side", "period"]])).reindex(key).to_numpy()
        t["holdout"] = t["market_id"].map(hold_of).to_numpy()
        t["year"] = pd.to_datetime(t["entry_period"], unit="D").dt.year
        return t

    quiet = seasoned14 & (rng14 <= 0.03 + 1e-9)
    rows = []

    def report(label: str, t: pd.DataFrame, samples: bool = True) -> None:
        parts = [("all", np.ones(len(t), bool))]
        if samples and len(t):
            parts += [("first-round holdout", t["holdout"].to_numpy()), ("newer sample", ~t["holdout"].to_numpy())]
        for name, mask in parts:
            rows.append({"rule": label, "sample": name, **stats(t[mask])})

    # ------------------------------------------------------------ the test
    r9095 = Rule(0.90, 0.95, 3, 60)
    a1 = trades(r9095, band(0.90, 0.95) & single & quiet)
    ctl = trades(r9095, band(0.90, 0.95) & single & ~quiet)
    report("A1: quiet, 90-95c, stand-alone", a1)
    report("control: not quiet, 90-95c, stand-alone", ctl)
    d, t_d = gap(a1, ctl)
    r = mean_cluster(a1["ret"].to_numpy(), a1["cluster"].to_numpy())
    print("=" * 110)
    print("THE PRE-REGISTERED TEST")
    print(f"A1: {len(a1):,} trades in {a1['cluster'].nunique():,} events, {int((a1['won'] == 0).sum())} lost; "
          f"return per trade {100 * r.mean:+.2f}% (t = {r.t:.2f})")
    rc = mean_cluster(ctl["ret"].to_numpy(), ctl["cluster"].to_numpy())
    print(f"control: {len(ctl):,} trades, {int((ctl['won'] == 0).sum())} lost; return per trade {100 * rc.mean:+.2f}% (t = {rc.t:.2f})")
    print(f"A1 minus control: {100 * d:+.2f} points (t = {t_d:.2f})")
    passed = r.mean > 0 and abs(r.t) >= 3 and d > 0 and abs(t_d) >= 2
    print(f"bar: A1 positive with |t| >= 3 and above its control with |t| >= 2  ->  {'PASSED' if passed else 'NOT PASSED'}")
    print("=" * 110)
    a1.to_csv(OUT / "q_trades_A1.csv", index=False)
    ctl.to_csv(OUT / "q_trades_A1_control.csv", index=False)

    # ------------------------------------------------- reported alongside
    r9598 = Rule(0.95, 0.98, 3, 60)
    a2 = trades(r9598, band(0.95, 0.98) & single & quiet)
    a2c = trades(r9598, band(0.95, 0.98) & single & ~quiet)
    report("A2: quiet, 95-98c, stand-alone (partly seen before)", a2)
    report("    not quiet, 95-98c, stand-alone", a2c)
    report("A3: quiet, 90-95c, legs of multi-outcome events", trades(r9095, band(0.90, 0.95) & ~single & quiet))
    report("    not quiet, 90-95c, legs", trades(r9095, band(0.90, 0.95) & ~single & ~quiet))
    report("A4: A1 entered with a resting bid", trades(Rule(0.90, 0.95, 3, 60, entry="maker"), band(0.90, 0.95) & single & quiet))
    report("    control entered with a resting bid", trades(Rule(0.90, 0.95, 3, 60, entry="maker"), band(0.90, 0.95) & single & ~quiet))
    r9098 = Rule(0.90, 0.98, 3, 60)
    wide = trades(r9098, band(0.90, 0.98) & single & quiet)
    report("quiet, 90-98c, stand-alone (both bands together)", wide)
    report("not quiet, 90-98c, stand-alone", trades(r9098, band(0.90, 0.98) & single & ~quiet))
    wide.to_csv(OUT / "q_trades_quiet_9098.csv", index=False)

    for cents in (0.02, 0.05):
        q = seasoned14 & (rng14 <= cents + 1e-9)
        report(f"sensitivity: range <= {cents * 100:.0f}c over 14 days, 90-95c", trades(r9095, band(0.90, 0.95) & single & q), samples=False)
    for window in (7, 28):
        rng_w, seasoned_w = trailing_range(s, window)
        q = seasoned_w & (rng_w <= 0.03 + 1e-9)
        report(f"sensitivity: range <= 3c over {window} days, 90-95c", trades(r9095, band(0.90, 0.95) & single & q), samples=False)
    # how the control splits by how much it had moved
    for label, lo, hi in (("control with range 3-6c", 0.03, 0.06), ("control with range 6-12c", 0.06, 0.12),
                          ("control with range above 12c", 0.12, 9.9)):
        report(f"  {label}", ctl[(ctl["range14"] > lo) & (ctl["range14"] <= hi)], samples=False)
    report("  control without two weeks of history", ctl[ctl["range14"].isna() | (ctl["range14"] <= 0.03)], samples=False)

    res = pd.DataFrame(rows)
    res.to_csv(OUT / "q_quiet_favourites.csv", index=False)
    print(res.round(2).to_string(index=False))

    print("\nA1 by year of entry:")
    for year, g in a1.groupby("year"):
        print(f"  {year}: {stats(g) if len(g) >= 20 else {'trades': len(g)}}")
    print("\nA1 by category:")
    for cat, g in a1.groupby("category"):
        st = stats(g)
        print(f"  {cat:12s} {st}")
    print("\nA1 without its 20 largest events (by number of trades):")
    top = a1["cluster"].value_counts().head(20).index
    print("  ", stats(a1[~a1["cluster"].isin(top)]))
    print("\nA1, one trade per event (the first):")
    print("  ", stats(a1.sort_values("entry_period").drop_duplicates("cluster")))
    print("\nA1 losing trades:")
    cols = ["market_id", "category", "entry_period", "entry_px", "dte_at_signal", "range14"]
    lost = a1[a1["won"] == 0][cols].copy()
    lost["entry_date"] = pd.to_datetime(lost["entry_period"], unit="D").dt.date
    q_of = meta.set_index("market_id")["question"]
    lost["question"] = lost["market_id"].map(q_of).str.slice(0, 80)
    print(lost.drop(columns="entry_period").to_string(index=False))


if __name__ == "__main__":
    with (OUT / "quiet_favourites_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
