"""TM: resting bids in the thinner markets (docs/04_second_round.md, section 13).

Fixed before it was run. On resolved news markets that traded 20,000 to
100,000 shares, the thin-market account's signals (ask above 90c and at most
98c, stand-alone, 3 to 60 days to the scheduled end, skipping outcomes that
ranged more than 15c in the last 14 days) are entered two ways:

    at the ask    the next taker-buy print within 3 days, with today's fee;
    resting bid   a bid left at the signal day's bid, filled only if a later
                  sale prints strictly below it within 3 days, no fee (the
                  first round's fill rule, unchanged).

Bar: the resting-bid version is positive with |t| >= 3 and returns more per
trade than the same signals bought at the ask, with |t| >= 2 on the gap.

    python scripts/run_thin_maker.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_quiet_favourites as rq  # noqa: E402
import run_quiet_replication as rr  # noqa: E402

from kht.backtest.harvest import Rule, candidate_trades, prepare  # noqa: E402
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes  # noqa: E402
from kht.research.sports import build_trades_table  # noqa: E402
from kht.research.stats import mean_cluster  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"


def stats(t: pd.DataFrame) -> dict:
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    return {"trades": len(t), "events": int(t["cluster"].nunique()), "lost": int((t["won"] == 0).sum()),
            "lost %": 100 * float((t["won"] == 0).mean()), "avg cost": float(t["cost"].mean()), "return a trade %": 100 * r.mean,
            "t_event": r.t, "median hold, days": float(t["hold"].median())}


def main() -> None:
    meta = rr.thin_meta()
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(build_trades_table(meta), min_cum=20_000), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    single = ~meta.set_index("market_id")["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    ask, dte = s["ask"].to_numpy(), s["days_to_end"].to_numpy()
    rng14, seasoned14 = rq.trailing_range(s, 14)
    calm = ~(seasoned14 & (rng14 > 0.15))
    ok = (dte > 3) & (dte <= 60) & single & calm

    rows = []
    kept = {}
    for label, lo, hi in (("90-98c (the thin account's band)", 0.90, 0.98), ("95-98c", 0.95, 0.98), ("90-95c", 0.90, 0.95)):
        sig = (ask > lo) & (ask <= hi) & ok
        for how in ("taker", "maker"):
            t = candidate_trades(s, Rule(lo, hi, 3, 60, entry=how), signal=sig)
            kept[(label, how)] = t
            rows.append({"band": label, "entry": "at the ask" if how == "taker" else "resting bid", **stats(t)})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "tm_thin_maker.csv", index=False)
    print(res.round(2).to_string(index=False))

    label = "90-98c (the thin account's band)"
    maker, taker = kept[(label, "maker")], kept[(label, "taker")]
    r = mean_cluster(maker["ret"].to_numpy(), maker["cluster"].to_numpy())
    d, t_d = rq.gap(maker, taker)
    passed = r.mean > 0 and abs(r.t) >= 3 and d > 0 and abs(t_d) >= 2
    print("=" * 110)
    print(f"TM, resting bids on {label}: {len(maker):,} filled of {len(taker):,} signals bought at the ask "
          f"({100 * len(maker) / len(taker):.0f}%); return per trade {100 * r.mean:+.2f}% (t = {r.t:.2f})")
    print(f"  resting bid minus at the ask: {100 * d:+.2f} points (t = {t_d:.2f})")
    print(f"  bar (positive with |t| >= 3; above the ask version with |t| >= 2)  ->  {'PASSED' if passed else 'NOT PASSED'}")
    # the same markets both ways: what did a resting bid do in markets where the ask was also taken?
    both = maker.merge(taker[["market_id", "ret", "cost"]], on="market_id", suffixes=("_bid", "_ask"))
    if len(both) >= 20:
        diff = mean_cluster((both["ret_bid"] - both["ret_ask"]).to_numpy(), both["cluster"].to_numpy())
        print(f"  in the {len(both):,} markets entered both ways: the bid paid {100 * (both['cost_ask'] - both['cost_bid']).mean():.2f}c less a share "
              f"and returned {100 * diff.mean:+.2f} points more (t = {diff.t:.2f})")
    missed = taker[~taker["market_id"].isin(maker["market_id"])]
    if len(missed) >= 20:
        m = mean_cluster(missed["ret"].to_numpy(), missed["cluster"].to_numpy())
        print(f"  the {len(missed):,} signals a resting bid never filled returned {100 * m.mean:+.2f}% bought at the ask "
              f"({int((missed['won'] == 0).sum())} lost): the trades a patient buyer misses")
    print("=" * 110)


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for st in self.streams:
            st.write(text)

    def flush(self):
        for st in self.streams:
            st.flush()


if __name__ == "__main__":
    with (OUT / "thin_maker_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
