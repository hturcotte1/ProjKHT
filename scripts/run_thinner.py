"""T5: does the edge keep growing as markets get thinner? (docs/04_second_round.md, section 13)

Fixed before any of these markets was downloaded. Resolved news markets
(outside sports and crypto, a life of two days or more) that traded 5,000 to
20,000 shares, used once they have traded 5,000. The first round's rules
exactly as before, and the thin account's band:

    R1d          ask above 95c and at most 99c, legs included
    main rule    95-98c, stand-alone
    thin band    90-98c, stand-alone

each bought at the next taker-buy print within 3 days and held, with today's
fee, 3 to 60 days to the scheduled end, one trade per market.

Bar: R1d positive with |t| >= 3 (clustered by event). Prediction, not a bar:
a return at least as large as in the 20,000-100,000 markets. Reported with
it: how many dollars traded in range, because below some size there is
nothing to buy.

    python scripts/run_thinner.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_thin_markets as tm  # noqa: E402

from kht.backtest.harvest import Rule, candidate_trades, prepare  # noqa: E402
from kht.data.download import load_meta  # noqa: E402
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes  # noqa: E402
from kht.research.sports import build_trades_table  # noqa: E402
from kht.research.stats import mean_cluster  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
MIN_CUM = 5_000
# the same rules on the 20,000-100,000 markets, from qt_quiet_replication.csv and t_thin_trades.csv
THIN = {"R1d: 95-99c, legs included": (1.69, 9.01, 3135), "main rule: 95-98c, stand-alone": (1.96, 5.96, 1393),
        "thin band: 90-98c, stand-alone": (2.40, 5.47, 1744)}


def thinner_meta() -> pd.DataFrame:
    meta = load_meta("closed_thinner")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    meta = meta[(meta["category"] != "sports") & (meta["category"] != "crypto") & (life >= 2) & resolved].copy()
    meta["closed_ts"] = meta["closed_ts"].fillna(meta["end_ts"])
    return meta[meta["closed_ts"].notna()]


def main() -> None:
    meta = thinner_meta()
    have = {p.stem for p in (ROOT / "data" / "trades").glob("*.parquet")}
    print(f"news markets that traded 5,000 to 20,000 shares: {len(meta):,}; tapes on disk: {int(meta['condition_id'].isin(have).sum()):,}")
    tr = build_trades_table(meta)
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(tr, min_cum=MIN_CUM), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    print(f"panel: {len(s):,} outcome-days in {s['market_id'].nunique():,} markets, {s['cluster'].nunique():,} events, "
          f"{pd.to_datetime(s.ts.min(), unit='s').date()} to {pd.to_datetime(s.ts.max(), unit='s').date()}")
    single = ~meta.set_index("market_id")["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    ask, dte = s["ask"].to_numpy(), s["days_to_end"].to_numpy()
    ok = (dte > 3) & (dte <= 60)

    rules = [("R1d: 95-99c, legs included", 0.95, 0.99, np.ones(len(s), bool)),
             ("main rule: 95-98c, stand-alone", 0.95, 0.98, single),
             ("thin band: 90-98c, stand-alone", 0.90, 0.98, single),
             ("90-95c, stand-alone", 0.90, 0.95, single),
             ("control: long shots 3-10c", 0.03, 0.10, np.ones(len(s), bool))]
    rows = []
    kept = {}
    for name, lo, hi, mask in rules:
        t = candidate_trades(s, Rule(lo, hi, 3, 60), signal=(ask > lo) & (ask <= hi) & ok & mask)
        t = t.join(tm.band_flow(tr, t, lo, hi, MIN_CUM), on="market_id")
        fee_rate = t["entry_fee"] / (t["entry_px"] * (1 - t["entry_px"]))
        t["cost_vwap"] = t["vwap"] + fee_rate * t["vwap"] * (1 - t["vwap"])
        t["ret_vwap"] = (t["proceeds"] - t["cost_vwap"]) / t["cost_vwap"]
        kept[name] = t
        a = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
        b = mean_cluster(t["ret_vwap"].to_numpy(), t["cluster"].to_numpy())
        q = t["usd_window"].quantile([0.10, 0.50, 0.90])
        rows.append({"rule": name, "trades": len(t), "events": int(t["cluster"].nunique()), "lost": int((t["won"] == 0).sum()),
                     "lost %": 100 * float((t["won"] == 0).mean()), "return a trade %": 100 * a.mean, "t_event": a.t,
                     "at the 3-day average %": 100 * b.mean, "t ": b.t, "in the 20-100k markets %": THIN.get(name, (np.nan,))[0],
                     "in-range $: 10th pct": q[0.10], "median": q[0.50], "90th pct": q[0.90],
                     "under $100 in range %": 100 * float((t["usd_window"] < 100).mean())})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "t5_thinner.csv", index=False)
    print("\n", res.round(2).to_string(index=False))
    r1d = kept["R1d: 95-99c, legs included"]
    r = mean_cluster(r1d["ret"].to_numpy(), r1d["cluster"].to_numpy())
    print("=" * 110)
    print(f"T5: R1d on markets with 5,000 to 20,000 shares: {len(r1d):,} trades in {r1d['cluster'].nunique():,} events, "
          f"{int((r1d['won'] == 0).sum())} lost; return per trade {100 * r.mean:+.2f}% (t = {r.t:.2f})")
    print(f"  bar (positive with |t| >= 3)  ->  {'PASSED' if r.mean > 0 and abs(r.t) >= 3 else 'NOT PASSED'}")
    print(f"  prediction (at least the +1.69% of the 20,000-100,000 markets)  ->  {'held' if 100 * r.mean >= 1.69 else 'did not hold'}")
    print("=" * 110)
    for name in ("main rule: 95-98c, stand-alone", "thin band: 90-98c, stand-alone"):
        t = kept[name]
        t["year"] = pd.to_datetime(t["entry_period"], unit="D").dt.year
        print(f"\n{name} by year of entry:")
        print(t.groupby("year").agg(trades=("won", "size"), lost=("won", lambda w: int((w == 0).sum())),
                                    avg_ret_pct=("ret", lambda x: 100 * x.mean())).round(2).to_string())


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
    with (OUT / "thinner_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
