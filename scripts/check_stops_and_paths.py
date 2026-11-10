"""Two questions about holding near-certain contracts, on the first round's panel.

1. Would a stop-loss have helped? Each rule is rerun selling at the first
   taker-sell print after the bid closes at or below a level.
2. How does the price of a quiet favourite move as its deadline approaches?
   This is the one place where the project's original idea, that the crowd's
   price moves predictably, turns out to be true: when nothing happens, the
   price of "nothing will happen" drifts up on a schedule.

Exploratory; it chooses nothing.

    python scripts/check_stops_and_paths.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_quiet_favourites as rq  # noqa: E402

from kht.backtest.harvest import Rule, candidate_trades  # noqa: E402
from kht.research.stats import mean_cluster  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"


def stats(t: pd.DataFrame) -> dict:
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    return {"trades": len(t), "won %": 100 * float((t["proceeds"] > t["cost"]).mean()), "lost everything": int((t["proceeds"] == 0).sum()),
            "stopped out": int((t["exit_reason"] == "stop").sum()), "return a trade %": 100 * r.mean, "t_event": r.t,
            "spread of returns %": 100 * float(t["ret"].std())}


def main() -> None:
    meta, s = rq.load()
    single = ~meta.set_index("market_id")["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    ask, dte = s["ask"].to_numpy(), s["days_to_end"].to_numpy()
    dte_ok = (dte > 3) & (dte <= 60)
    rng7, seasoned7 = rq.trailing_range(s, 7)
    quiet = seasoned7 & (rng7 <= 0.03 + 1e-9)
    rules = {"main rule, 95-98c": ((0.95, 0.98), (ask > 0.95) & (ask <= 0.98) & dte_ok & single),
             "quiet rule Q, 90-98c": ((0.90, 0.98), (ask > 0.90) & (ask <= 0.98) & dte_ok & single & quiet),
             "90-95c, not quiet": ((0.90, 0.95), (ask > 0.90) & (ask <= 0.95) & dte_ok & single & ~quiet)}

    rows = []
    for name, ((lo, hi), sig) in rules.items():
        for stop in (None, 0.90, 0.85, 0.80, 0.70, 0.50):
            t = candidate_trades(s, Rule(lo, hi, 3, 60, stop_bid=stop), signal=sig)
            rows.append({"rule": name, "sell if the bid closes at or below": "never" if stop is None else f"{100 * stop:.0f}c", **stats(t)})
    stops = pd.DataFrame(rows)
    stops.to_csv(OUT / "q_stops.csv", index=False)
    print("1. Stop-losses\n", stops.round(2).to_string(index=False))

    # the path: quiet favourites bought with 30 or more days to run, followed to the end
    (lo, hi), sig = rules["quiet rule Q, 90-98c"]
    q = candidate_trades(s, Rule(lo, hi, 3, 60), signal=sig)
    q = q[q["dte_at_signal"] >= 30]
    by_series = {key: g for key, g in s[s["market_id"].isin(q["market_id"])].groupby(["market_id", "side"])}
    points = []
    for r in q.itertuples():
        g = by_series[(r.market_id, r.side)]
        g = g[g["period"] >= r.entry_period]
        for d in (45, 30, 21, 14, 10, 7, 5, 3, 1):
            at = g[g["days_to_end"] <= d]
            if len(at) and at["days_to_end"].iloc[0] > d - 4:         # a trade within a few days of that point
                points.append((r.market_id, d, float(at["last"].iloc[0]), float(at["bid"].iloc[0]), r.entry_px))
    path = pd.DataFrame(points, columns=["market_id", "days to the end", "last", "bid", "entry"])
    out = (path.groupby("days to the end").agg(markets=("market_id", "nunique"), bought_at=("entry", "mean"), last_price=("last", "mean"),
                                               at_98c_or_more=("last", lambda x: 100 * (x >= 0.98).mean()),
                                               bid_at_97c_or_more=("bid", lambda x: 100 * (x >= 0.97).mean()))
               .sort_index(ascending=False).round(3))
    out.to_csv(OUT / "q_price_path.csv")
    print(f"\n2. The price of quiet favourites bought with 30 or more days to run ({len(q):,} trades), as the end approaches")
    print(out.to_string())


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
    with (OUT / "stops_and_paths_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
