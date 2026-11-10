"""Does it matter how long a contract has been in the band when it is bought?

The backtest buys each contract the first time it qualifies. A system that is
switched on today, or comes back after days without a cycle, finds a stock of
contracts that have been sitting in the band for days or weeks and buys
those. Its first purchases, and the first entries in the forward-test log,
are that stock. This compares the two on the same data, for the main
account's rule (95-98c, stand-alone markets, lift the ask, hold to
resolution):

  * bought the first time a contract qualifies (what the backtest does);
  * bought the first time it qualifies at least k days after that;
  * bought on "switch-on" dates a week apart, taking whatever is in the band.

Both late kinds hold contracts the first kind also bought and pay out the
same, so any difference comes from which contracts are still in the band
later, not from what happens to them afterwards. The same comparison is
repeated for the pre-registered rule R1d (95-99c, legs included).

Written after the test, so it is exploratory.

    python scripts/check_late_entry.py
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
from kht.research.stats import mean_cluster

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
SPLIT_TS = pd.Timestamp("2026-05-01", tz="UTC").timestamp()
SWITCH_ON_EVERY = 7           # days between simulated switch-on dates


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for s in self.streams:
            s.write(text)

    def flush(self):
        for s in self.streams:
            s.flush()


def stats(t: pd.DataFrame) -> dict:
    if len(t) < 20:
        return {"trades": len(t)}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    return {"trades": len(t), "events": int(t["cluster"].nunique()), "win%": 100 * float((t["proceeds"] > t["cost"]).mean()),
            "avg_cost": float(t["cost"].mean()), "avg_ret%": 100 * r.mean, "se%": 100 * r.se, "t_event": r.t,
            "med_dte": float(t["dte_at_signal"].median()), "med_days_in_band": float(t["age"].median())}


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    meta = load_meta("closed")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    meta = meta[(~meta["category"].isin(["sports", "crypto"])) & (life >= 2) & resolved].copy()
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(build_trades_table(meta)), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    return meta, s


def compare(meta: pd.DataFrame, s: pd.DataFrame, rule: Rule, single_only: bool, slug: str, title: str) -> None:
    print(f"\n{'=' * 100}\n{title}\n{'=' * 100}")
    sig = ((s["ask"] > rule.ask_lo) & (s["ask"] <= rule.ask_hi) & (s["days_to_end"] > rule.dte_lo)
           & (s["days_to_end"] <= rule.dte_hi)).to_numpy().copy()
    if single_only:
        sig &= ~meta.set_index("market_id")["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    # days since this outcome first qualified (price band and days-to-end window together)
    first = s["period"].where(sig).groupby(s["series"]).transform("min")
    age = (s["period"] - first).to_numpy()
    age_of = pd.Series(age, index=pd.MultiIndex.from_frame(s[["market_id", "side", "period"]]))
    hold_of = s.groupby("market_id")["end_ts"].first() < SPLIT_TS

    def trades(signal: np.ndarray, frame: pd.DataFrame = s) -> pd.DataFrame:
        t = candidate_trades(frame, rule, signal=signal)
        if t.empty:
            return t
        t["age"] = age_of.reindex(pd.MultiIndex.from_frame(t[["market_id", "side", "signal_period"]])).to_numpy()
        t["holdout"] = t["market_id"].map(hold_of).to_numpy()
        return t

    rows = []

    def report(label: str, t: pd.DataFrame) -> None:
        for name, mask in (("holdout", t["holdout"]), ("recent", ~t["holdout"]), ("all", np.ones(len(t), bool))):
            rows.append({"entry": label, "sample": name, **stats(t[mask])})

    base = trades(sig)
    report("first time it qualifies (the backtest)", base)
    report("  of those: 30 days or less to the scheduled end", base[base["dte_at_signal"] <= 30])
    late = {}
    for k in (2, 5, 10, 20, 30):
        late[k] = trades(sig & (age >= k))
        report(f"first time it qualifies {k}+ days later", late[k])
    report("  20+ days later: 30 days or less to the scheduled end", late[20][late[20]["dte_at_signal"] <= 30])

    # Switch-on dates: everything in the band that day, each date on its own.
    period = s["period"].to_numpy()
    dates = np.arange(int(period[sig].min()) + SWITCH_ON_EVERY, int(period[sig].max()), SWITCH_ON_EVERY)
    series = s["series"].to_numpy()
    snaps = []
    for d in dates:
        on = sig & (period == d)
        if not on.any():
            continue
        keep = np.isin(series, series[on])
        t = trades(on[keep], s[keep].reset_index(drop=True))
        if len(t):
            snaps.append(t.assign(switch_on=int(d)))
    snap = pd.concat(snaps, ignore_index=True)
    report(f"whatever qualifies on a switch-on date ({len(dates)} dates, a week apart)", snap)
    for label, lo, hi in (("  of those: first qualified 0-2 days before", 0, 2), ("  of those: 3-9 days before", 3, 9),
                          ("  of those: 10-19 days before", 10, 19), ("  of those: 20 days or more before", 20, 10_000)):
        report(label, snap[(snap["age"] >= lo) & (snap["age"] <= hi)])

    res = pd.DataFrame(rows)
    res.insert(0, "rule", slug)
    res.to_csv(OUT / f"c7_late_entry_{slug}.csv", index=False)
    for name in ("all", "holdout", "recent"):
        print(f"\n[{name}]\n", res[res["sample"] == name].drop(columns=["sample", "rule"]).round(2).to_string(index=False))

    # A contract in the band for weeks is bought on several switch-on dates, so
    # the pooled rows above repeat it. Each date on its own is one account's
    # first day, which is what the paper account's first purchases are.
    per = snap.groupby("switch_on").agg(trades=("ret", "size"), lost=("won", lambda w: int((w == 0).sum())),
                                        avg_ret_pct=("ret", lambda r: 100 * r.mean()))
    per.insert(0, "date", pd.to_datetime(per.index.to_numpy(), unit="D").strftime("%Y-%m-%d"))
    per.round(2).to_csv(OUT / f"c7_late_entry_{slug}_by_switch_on_date.csv", index=False)
    big = per[per["trades"] >= 10]
    q = big["avg_ret_pct"].quantile([0.1, 0.5, 0.9])
    print(f"\nswitch-on dates with 10 or more trades: {len(big)} of {len(per)}; no losing trade on {int((big['lost'] == 0).sum())}; "
          f"the day's purchases lost money overall on {int((big['avg_ret_pct'] < 0).sum())}")
    print(f"  return per trade of a day's purchases: median {q[0.5]:.2f}%, a tenth of dates below {q[0.1]:.2f}%, "
          f"a tenth above {q[0.9]:.2f}%, worst {big['avg_ret_pct'].min():.2f}%")
    print(f"  distinct markets across all switch-on dates: {snap['market_id'].nunique():,} "
          f"(the first-time rule trades {len(base):,})")
    lost = base[base["won"] == 0]
    print(f"\nlosing trades of the first-time rule: {len(lost)} of {len(base):,}")
    for k in (2, 5, 10, 20, 30):
        t = late[k]
        n_lost = int((t["won"] == 0).sum())
        print(f"  still qualifying {k:2d}+ days later: {len(t):5,} contracts, {n_lost:2d} of them lost ({n_lost / len(t):.2%})")


def main() -> None:
    meta, s = load()
    compare(meta, s, Rule(0.95, 0.98, 3, 60), True, "deployed",
            "The main account's rule: 95-98c, stand-alone markets, lift the ask, hold to resolution")
    compare(meta, s, Rule(0.95, 0.99, 3, 60), False, "r1d",
            "The pre-registered rule R1d: 95-99c, legs of multi-outcome events included")


if __name__ == "__main__":
    with (OUT / "late_entry_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
