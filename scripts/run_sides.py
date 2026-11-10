"""Which side of the bet carries the edge? (docs/05_third_round.md, section 2)

Exploration on the corrected universes (scripts/at_the_time.py):

    big      news markets once they had traded 100,000 shares
    thin     news markets while they had traded 20,000 to 100,000
    thinner  news markets while they had traded 5,000 to 20,000

Big and thin had already been read when the third round began. Thinner was
read for the first time by scripts/run_thinner.py, with its tests fixed; it
is repeated here afterwards so the three sit in one table.

It splits the first round's rule by what was bought (stand-alone "No",
stand-alone "Yes", the leader of a multi-way event, an also-ran), looks at
the same contracts 60 to 180 days from their scheduled end, and runs each
side at every price. It chooses nothing: the tests it led to are fixed in
section 3 of the document and run by scripts/run_thinner.py on markets that
had not been read.

    python scripts/run_sides.py
"""

from __future__ import annotations

import gc
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import at_the_time as att  # noqa: E402

from kht.backtest.harvest import Rule, candidate_trades, prepare  # noqa: E402
from kht.research.stats import mean_cluster  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 300)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
SCHEDULED_BY = pd.Timestamp("2026-10-27").timestamp()
UNIVERSES = (("big: 100,000 shares or more at the time", 100_000, att.TOP, ("big",)), ("thin: 20,000 to 100,000 at the time", 20_000, 100_000, None),
             ("thinner: 5,000 to 20,000 at the time (read for the first time by run_thinner.py)", 5_000, 20_000, None))
BANDS = ((0.03, 0.10), (0.10, 0.20), (0.20, 0.35), (0.35, 0.50), (0.50, 0.65), (0.65, 0.80), (0.80, 0.90), (0.90, 0.95), (0.95, 0.98))


def ready(p: pd.DataFrame) -> pd.DataFrame:
    p = prepare(p)
    p = p[p["won"].notna()].reset_index(drop=True)
    p["series"] = p.groupby(["market_id", "side"], sort=False).ngroup()
    return p


def line(t: pd.DataFrame) -> dict:
    if len(t) < 10:
        return {"trades": len(t)}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    w = mean_cluster(t["ret"].to_numpy(), (t["entry_period"] // 7).to_numpy())
    c = mean_cluster((t["proceeds"] - t["cost"]).to_numpy(), t["cluster"].to_numpy())
    return {"trades": len(t), "events": int(t["cluster"].nunique()), "lost": int((t["won"] == 0).sum()), "won %": 100 * float(t["won"].mean()),
            "avg cost": float(t["cost"].mean()), "cents a share": 100 * c.mean, "t_cents": c.t, "return a trade %": 100 * r.mean,
            "t_event": r.t, "t_week": w.t, "median hold, days": float(t["hold"].median()),
            "per 30 days held %": 100 * float(t["ret"].sum()) / max(float(t["hold"].clip(lower=1).sum()), 1.0) * 30}


def main() -> None:
    groups, grid, house_rows, bid_or_ask = [], [], [], []
    for uni, lo_cum, hi_cum, only in UNIVERSES:
        meta, _, p = att.panel(lo_cum, hi_cum, only)
        s = ready(p)
        del p
        gc.collect()
        m = meta.set_index("market_id")
        yn = ((m["outcome0"].str.strip().str.lower() == "yes") & (m["outcome1"].str.strip().str.lower() == "no")).reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
        single = ~s["neg_risk"].fillna(False).to_numpy(dtype=bool)
        ask, dte, side, end = s["ask"].to_numpy(), s["days_to_end"].to_numpy(), s["side"].to_numpy(), s["end_ts"].to_numpy()
        short, far, sched = (dte > 3) & (dte <= 60), (dte > 60) & (dte <= 180), end <= SCHEDULED_BY

        def trades(lo: float, hi: float, mask: np.ndarray, d0: float = 3, d1: float = 60) -> pd.DataFrame:
            return candidate_trades(s, Rule(lo, hi, d0, d1), signal=(ask > lo) & (ask <= hi) & mask)

        specs = [("95-99c, 3-60 days", "stand-alone, No", trades(0.95, 0.99, short & single & yn & (side == 1))),
                 ("95-99c, 3-60 days", "stand-alone, Yes", trades(0.95, 0.99, short & single & yn & (side == 0))),
                 ("95-99c, 3-60 days", "leg, Yes (the leader)", trades(0.95, 0.99, short & ~single & yn & (side == 0))),
                 ("95-99c, 3-60 days", "leg, No (an also-ran)", trades(0.95, 0.99, short & ~single & yn & (side == 1))),
                 ("90-98c, 3-60 days", "stand-alone, No", trades(0.90, 0.98, short & single & yn & (side == 1))),
                 ("90-98c, 3-60 days", "stand-alone, Yes", trades(0.90, 0.98, short & single & yn & (side == 0))),
                 ("90-98c, 60-180 days, scheduled end passed", "stand-alone, No", trades(0.90, 0.98, far & single & yn & sched & (side == 1), 60, 180)),
                 ("90-98c, 60-180 days, scheduled end passed", "stand-alone, Yes", trades(0.90, 0.98, far & single & yn & sched & (side == 0), 60, 180)),
                 ("90-98c, 60-120 days, scheduled end passed", "stand-alone, No", trades(0.90, 0.98, (dte > 60) & (dte <= 120) & single & yn & sched & (side == 1), 60, 120)),
                 ("90-98c, 120-180 days, scheduled end passed", "stand-alone, No", trades(0.90, 0.98, (dte > 120) & (dte <= 180) & single & yn & sched & (side == 1), 120, 180)),
                 ("90-95c, 60-180 days, scheduled end passed", "stand-alone, No", trades(0.90, 0.95, far & single & yn & sched & (side == 1), 60, 180)),
                 ("95-98c, 60-180 days, scheduled end passed", "stand-alone, No", trades(0.95, 0.98, far & single & yn & sched & (side == 1), 60, 180)),
                 ("90-98c, 60-180 days, every market", "stand-alone, No", trades(0.90, 0.98, far & single & yn & (side == 1), 60, 180)),
                 ("90-98c, 3-60 days, scheduled end passed", "stand-alone, No", trades(0.90, 0.98, short & single & yn & sched & (side == 1)))]
        for rule, group, t in specs:
            groups.append({"universe": uni, "rule": rule, "bought": group, **line(t)})
        long_no = specs[6][2].assign(year=lambda d: pd.to_datetime(d["entry_period"], unit="D").dt.year)
        for y, g in long_no.groupby("year"):
            groups.append({"universe": uni, "rule": "90-98c, 60-180 days, scheduled end passed, by year of entry", "bought": f"stand-alone, No, {y}", **line(g)})

        for lo, hi in BANDS:
            for sd, sn in ((1, "No"), (0, "Yes")):
                grid.append({"universe": uni, "paid": f"{100 * lo:.0f}-{100 * hi:.0f}c", "side": sn, **line(trades(lo, hi, short & single & yn & (side == sd)))})

        # the same "No" signals bought at the ask, or with a bid left at the day's bid for three days
        for rule, lo, hi, d0, d1 in (("No, 95-98c, 3-60 days", 0.95, 0.98, 3, 60), ("No, 90-98c, 3-60 days", 0.90, 0.98, 3, 60),
                                     ("No, 90-98c, 60-180 days", 0.90, 0.98, 60, 180), ("No, 50-90c, 3-60 days", 0.50, 0.90, 3, 60),
                                     ("No, 50-90c, 20-60 days", 0.50, 0.90, 20, 60)):
            sig = (ask > lo) & (ask <= hi) & (dte > d0) & (dte <= d1) & single & yn & (side == 1)
            at_ask = candidate_trades(s, Rule(lo, hi, d0, d1), signal=sig)
            at_bid = candidate_trades(s, Rule(lo, hi, d0, d1, entry="maker"), signal=sig)
            bid_or_ask.append({"universe": uni, "rule": rule, "entry": "at the ask", **line(at_ask)})
            bid_or_ask.append({"universe": uni, "rule": rule, "entry": "resting bid", "filled %": 100 * len(at_bid) / max(len(at_ask), 1), **line(at_bid)})

        house = trades(0.50, 0.90, short & single & yn & (side == 1))
        fee = house["entry_fee"] > 0
        half = pd.to_datetime(house["entry_period"], unit="D")
        house = house.assign(half=half.dt.year.astype(str) + np.where(half.dt.month <= 6, " H1", " H2"))
        cuts = [("all", house), ("scheduled end passed", house[m["end_ts"].reindex(house["market_id"]).to_numpy() <= SCHEDULED_BY]),
                ("3-20 days left", house[house["dte_at_signal"] <= 20]), ("20-60 days left", house[house["dte_at_signal"] > 20]),
                ("paid 50-60c", house[house["entry_px"] <= 0.60]), ("paid 60-70c", house[(house["entry_px"] > 0.60) & (house["entry_px"] <= 0.70)]),
                ("paid 70-80c", house[(house["entry_px"] > 0.70) & (house["entry_px"] <= 0.80)]), ("paid 80-90c", house[house["entry_px"] > 0.80]),
                ("markets with a fee", house[fee]), ("fee-free markets", house[~fee])]
        cuts += [(f"category: {c}", g) for c, g in house.groupby("category")] + [(f"entered {h}", g) for h, g in house.groupby("half")]
        for name, g in cuts:
            house_rows.append({"universe": uni, "cut": name, **line(g)})
        house_rows.append({"universe": uni, "cut": "the other side: Yes at 10-50c", **line(trades(0.10, 0.50, short & single & yn & (side == 0)))})
        del s
        gc.collect()

    for frame, name, title in ((pd.DataFrame(groups), "s3_groups.csv", "What was bought"), (pd.DataFrame(grid), "s3_side_by_price.csv", "Every price, each side (stand-alone, 3-60 days)"),
                               (pd.DataFrame(house_rows), "s3_house.csv", '"No" at 50-90c, stand-alone, 3-60 days'),
                               (pd.DataFrame(bid_or_ask), "s3_bid_or_ask.csv", 'Paying the ask or leaving a bid, stand-alone "No"')):
        frame.to_csv(OUT / name, index=False)
        print("\n" + "=" * 110 + f"\n{title}\n" + "=" * 110)
        for uni, g in frame.groupby("universe", sort=False):
            print(f"\n{uni}\n", g.drop(columns="universe").round(2).to_string(index=False))


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
    with (OUT / "sides_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
