"""Round two's thin-market results, redone on markets that were thin AT THE TIME.

Round two chose its thin markets by final volume, which sheds losers
(docs/05_third_round.md, section 3; scripts/at_the_time.py). This script
reruns everything that depended on that universe:

    the first round's rules and the thin account's band   (round two, section 9)
    resting bids, TM, with its bar                         (section 14)
    bid first, then the ask                                (section 14)
    what the markets could take, and the accounts          (section 10)

on three universes side by side:

    ended thin      markets that ended at 20,000 to 100,000 shares (as round two did)
    thin part       the 20,000-100,000 part of the life of markets that ended bigger
    thin at the time    both: what "thin" means to somebody placing a trade

The bars are the ones round two fixed. Nothing here is a new test.

    python scripts/run_thin_corrected.py
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
import run_quiet_favourites as rq  # noqa: E402
import run_thin_markets as tm  # noqa: E402

from kht.backtest.harvest import Rule, candidate_trades, prepare  # noqa: E402
from kht.research.stats import mean_cluster  # noqa: E402
from kht.trading.universe import is_operational_tag  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 200)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
LO, HI = 20_000, 100_000
UNIVERSES = {"ended thin (round two)": ("thin",), "thin part of markets that ended bigger": ("big",), "thin at the time": None}


def ready(p: pd.DataFrame) -> pd.DataFrame:
    p = prepare(p)
    p = p[p["won"].notna()].reset_index(drop=True)
    p["series"] = p.groupby(["market_id", "side"], sort=False).ngroup()
    return p


def line(t: pd.DataFrame) -> dict:
    if len(t) < 2:
        return {"trades": len(t)}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    w = mean_cluster(t["ret"].to_numpy(), (t["entry_period"] // 7).to_numpy())
    return {"trades": len(t), "events": int(t["cluster"].nunique()), "lost": int((t["won"] == 0).sum()),
            "lost %": 100 * float((t["won"] == 0).mean()), "avg cost": float(t["cost"].mean()),
            "return a trade %": 100 * r.mean, "t_event": r.t, "t_week": w.t, "median hold, days": float(t["hold"].median())}


def masks(s: pd.DataFrame) -> dict[str, np.ndarray]:
    single = ~s["neg_risk"].fillna(False).to_numpy(dtype=bool)
    dte = s["days_to_end"].to_numpy()
    rng14, seasoned14 = rq.trailing_range(s, 14)
    return {"ok": (dte > 3) & (dte <= 60), "single": single, "calm": ~(seasoned14 & (rng14 > 0.15))}


def rules_table() -> dict[str, dict[str, pd.DataFrame]]:
    """The rules on the three universes; returns the trade lists of each."""
    rows, kept = [], {}
    for uni, only in UNIVERSES.items():
        _, _, p = att.panel(LO, HI, only)
        s = ready(p)
        m = masks(s)
        ask = s["ask"].to_numpy()
        specs = [("R1d: 95-99c, legs included", 0.95, 0.99, m["ok"], "taker"),
                 ("main rule: 95-98c, stand-alone", 0.95, 0.98, m["ok"] & m["single"], "taker"),
                 ("thin band: 90-98c, stand-alone", 0.90, 0.98, m["ok"] & m["single"], "taker"),
                 ("90-95c, stand-alone", 0.90, 0.95, m["ok"] & m["single"], "taker"),
                 ("thin account: 90-98c, stand-alone, calm, at the ask", 0.90, 0.98, m["ok"] & m["single"] & m["calm"], "taker"),
                 ("thin account's signals with a resting bid (TM)", 0.90, 0.98, m["ok"] & m["single"] & m["calm"], "maker"),
                 ("95-98c, stand-alone, calm, at the ask", 0.95, 0.98, m["ok"] & m["single"] & m["calm"], "taker"),
                 ("95-98c, stand-alone, calm, with a resting bid", 0.95, 0.98, m["ok"] & m["single"] & m["calm"], "maker")]
        kept[uni] = {}
        for name, lo, hi, mask, how in specs:
            t = candidate_trades(s, Rule(lo, hi, 3, 60, entry=how), signal=(ask > lo) & (ask <= hi) & mask)
            kept[uni][name] = t
            rows.append({"rule": name, "universe": uni, **line(t)})
        if only is None:
            kept["panel"] = s
        del p
        gc.collect()
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "tc_rules.csv", index=False)
    for name, g in res.groupby("rule", sort=False):
        print(f"\n{name}\n", g.drop(columns="rule").round(2).to_string(index=False))
    return kept


def tm_verdict(kept: dict) -> None:
    print("\n" + "=" * 110)
    for uni in UNIVERSES:
        maker, taker = kept[uni]["thin account's signals with a resting bid (TM)"], kept[uni]["thin account: 90-98c, stand-alone, calm, at the ask"]
        r = mean_cluster(maker["ret"].to_numpy(), maker["cluster"].to_numpy())
        d, t_d = rq.gap(maker, taker)
        ok = r.mean > 0 and abs(r.t) >= 3 and d > 0 and abs(t_d) >= 2
        print(f"TM on '{uni}': {len(maker):,} filled of {len(taker):,} ({100 * len(maker) / len(taker):.0f}%); resting bid {100 * r.mean:+.2f}% (t = {r.t:.2f}); "
              f"bid minus ask {100 * d:+.2f} points (t = {t_d:.2f})  ->  {'PASSED' if ok else 'NOT PASSED'}")
    print("=" * 110)


def bid_then_ask(s: pd.DataFrame, taker: pd.DataFrame, maker: pd.DataFrame) -> None:
    """Round two's exploratory comparison, per first signal, on the corrected universe (see run_thin_maker.hybrid)."""
    m = masks(s)
    ask = s["ask"].to_numpy()
    lo, hi = 0.90, 0.98
    sig = (ask > lo) & (ask <= hi) & m["ok"] & m["single"] & m["calm"]
    first = s[sig].sort_values(["market_id", "period", "side"]).drop_duplicates("market_id")[["market_id", "side", "period"]]
    on_first = lambda t: t.merge(first, on=["market_id", "side"]).query("signal_period == period")  # noqa: E731
    bid, at_ask = on_first(maker), on_first(taker)
    rest = first[~first["market_id"].isin(bid["market_id"])]
    by_series = {key: g for key, g in s[s["market_id"].isin(rest["market_id"])].groupby(["market_id", "side"])}
    rows = []
    for r in rest.itertuples():
        g = by_series[(r.market_id, r.side)]
        g = g[(g["period"] > r.period + 3) & (g["period"] <= r.period + 7) & np.isfinite(g["ask_first"])]
        if not len(g):
            continue
        px = float(g["ask_first"].iloc[0])
        if not (lo < px <= hi + 0.005):
            continue
        fee = float(g["fee_rate"].iloc[0]) * px * (1 - px)
        won = float(g["won"].iloc[0])
        rows.append({"market_id": r.market_id, "cluster": int(g["cluster"].iloc[0]), "cost": px + fee, "won": won, "ret": (won - px - fee) / (px + fee)})
    late = pd.DataFrame(rows)
    both = pd.concat([bid[["market_id", "cluster", "ret", "won", "cost"]], late], ignore_index=True)
    out = []
    for name, t in (("bid filled on the first signal", bid), ("not filled: the ask, 4 to 7 days later, if still in the band", late),
                    ("bid first, then the ask (both together)", both), ("the ask straight away, for comparison", at_ask)):
        r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
        out.append({"entry": name, "trades": len(t), "share of first signals %": 100 * len(t) / len(first), "lost": int((t["won"] == 0).sum()),
                    "avg cost": float(t["cost"].mean()), "return a trade %": 100 * r.mean, "t_event": r.t,
                    "profit per first signal %": 100 * float(t["ret"].sum()) / len(first)})
    res = pd.DataFrame(out)
    res.to_csv(OUT / "tc_bid_then_ask.csv", index=False)
    print(f"\nBid first, then the ask, thin at the time ({len(first):,} first signals; exploratory, as in round two)")
    print(res.round(2).to_string(index=False))


def thin_lists(meta: pd.DataFrame, tr: pd.DataFrame, s: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """The trade lists run_thin_markets.universe builds, for markets thin at the time."""
    m = masks(s)
    ask = s["ask"].to_numpy()
    tag_lists = meta.set_index("market_id")["tags"].fillna("").str.split("|")
    counts = tag_lists.explode().value_counts()
    theme_set = {x for x in counts[(counts >= 2) & (counts <= max(2, 0.10 * len(meta)))].index if x and not is_operational_tag(x)}
    themes_of = tag_lists.map(lambda tags: tuple(sorted(set(tags) & theme_set)))
    lists = {}
    for name, lo, hi, extra in (("tight", 0.95, 0.98, True), ("wide", 0.90, 0.98, True), ("wide, calm only", 0.90, 0.98, m["calm"])):
        t = candidate_trades(s, Rule(lo, hi, 3, 60), signal=(ask > lo) & (ask <= hi) & m["ok"] & m["single"] & extra)
        t = t.join(tm.band_flow(tr, t, lo, hi, LO), on="market_id")
        fee_rate = t["entry_fee"] / (t["entry_px"] * (1 - t["entry_px"]))
        t["cost_vwap"] = t["vwap"] + fee_rate * t["vwap"] * (1 - t["vwap"])
        t["ret_vwap"] = (t["proceeds"] - t["cost_vwap"]) / t["cost_vwap"]
        t["themes"] = t["market_id"].map(themes_of)
        t["universe"] = "thin"
        lists[f"thin {name}"] = t
    return lists


def accounts() -> None:
    meta, tr, p = att.panel(LO, HI)
    lists = thin_lists(meta, tr, ready(p))
    del tr, p
    gc.collect()
    lists.update(tm.universe(tm.big_meta(), 100_000, "big"))
    summary = pd.DataFrame([tm.describe(k, v) for k, v in lists.items()])
    summary.to_csv(OUT / "tc_trades.csv", index=False)
    print("\nthe trade lists, with the thin ones thin at the time (first print as in every backtest; 3-day average as a larger order would pay)\n")
    print(summary.round(2).to_string(index=False))
    combos = {
        "A. big tight (the main paper account today)": ["big tight"],
        "B. A + thin tight": ["big tight", "thin tight"],
        "C. A + thin wide": ["big tight", "thin wide"],
        "D. A + thin wide, calm only": ["big tight", "thin wide, calm only"],
    }
    rows = []
    for name, keys in combos.items():
        for bankroll in (1_000, 5_000, 25_000):
            for frac in (0.02, 0.04):
                rows.append({"account": name, **tm.account([lists[k] for k in keys], bankroll, frac)})
    acc = pd.DataFrame(rows)
    acc.to_csv(OUT / "tc_accounts.csv", index=False)
    print(f"\naccounts: positions at most {tm.PARTICIPATION:.0%} of the in-range flow, priced at the 3-day average, one position per event, "
          "four per story, at most 80% invested\n")
    print(acc.round(1).to_string(index=False))


def main() -> None:
    kept = rules_table()
    tm_verdict(kept)
    uni = "thin at the time"
    bid_then_ask(kept["panel"], kept[uni]["thin account: 90-98c, stand-alone, calm, at the ask"], kept[uni]["thin account's signals with a resting bid (TM)"])
    del kept
    gc.collect()
    accounts()


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
    with (OUT / "thin_corrected_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
