"""What two filters with hindsight in them did to the earlier results.

Found in round three, before its own data was read (docs/05_third_round.md,
section 3):

1. Round two chose its thin markets by FINAL volume (20,000 to 100,000
   shares). A market where the surprise happens draws a burst of trading and
   ends over the line, so that universe had shed many of its losers.
2. Every round required "a life of two days or more". 786 news markets
   resolved within two days although scheduled to run longer, mostly because
   the thing happened at once, and they were never downloaded.

This script reruns what depended on them, old universe beside corrected:

    the first round's rules in big markets, with the short-lived markets back
    round two's thin-market rules on markets thin AT THE TIME
    resting bids (TM) and bid-first-then-ask
    what the markets could take, and the accounts

The bars are the ones fixed at the time. Nothing here is a new test.

    python scripts/download_trades.py short_lived          (and _thin, _thinner)
    python scripts/run_corrections.py
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
import run_quiet_replication as rr  # noqa: E402
import run_thin_markets as tm  # noqa: E402

from kht.backtest.harvest import Rule, candidate_trades, prepare  # noqa: E402
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes  # noqa: E402
from kht.research.sports import build_trades_table  # noqa: E402
from kht.research.stats import mean_cluster  # noqa: E402
from kht.trading.universe import is_operational_tag  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 200)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
LO, HI = 20_000, 100_000
OLD_BIG = att.CACHE / "panel_non_sports.parquet"       # the first round's panel, as it was
OLD_THIN = att.CACHE / "panel_thin.parquet"            # round two's panel, as it was
SPLIT_TS = pd.Timestamp("2026-05-01", tz="UTC").timestamp()     # the first round's holdout: scheduled to end before this
SCHEDULED_BY = pd.Timestamp("2026-10-27").timestamp()
ROUND_TWO, AT_THE_TIME = "as round two had it (ended thin, lived two days)", "thin at the time, short-lived markets back"
UNIVERSES = (ROUND_TWO, "the thin part of markets that ended bigger", AT_THE_TIME)


def old_panel(path: Path, meta: pd.DataFrame, min_cum: int) -> pd.DataFrame:
    """A panel exactly as an earlier round built it: from the cache if it is there, else rebuilt."""
    if path.exists():
        return pd.read_parquet(path)
    p = add_taker_buy_pnl(by_side(period_quotes(build_trades_table(meta), min_cum=min_cum), meta))
    path.parent.mkdir(parents=True, exist_ok=True)
    p.to_parquet(path, index=False)
    return p


def thin_panel(universe: str) -> pd.DataFrame:
    if universe == ROUND_TWO:
        return old_panel(OLD_THIN, rr.thin_meta(), LO)
    return att.panel(LO, HI, ("big",) if universe != AT_THE_TIME else None)[2]


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
    for uni in UNIVERSES:
        p = thin_panel(uni)
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
        if uni == AT_THE_TIME:
            kept["panel"] = s
        del p
        gc.collect()
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "cor_thin_rules.csv", index=False)
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
    res.to_csv(OUT / "cor_bid_then_ask.csv", index=False)
    print(f"\nBid first, then the ask, thin at the time ({len(first):,} first signals; exploratory, as in round two)")
    print(res.round(2).to_string(index=False))


def trade_lists(meta: pd.DataFrame, tr: pd.DataFrame, s: pd.DataFrame, label: str, min_cum: int) -> dict[str, pd.DataFrame]:
    """The trade lists run_thin_markets.universe builds, for a universe from at_the_time."""
    m = masks(s)
    ask = s["ask"].to_numpy()
    tag_lists = meta.set_index("market_id")["tags"].fillna("").str.split("|")
    counts = tag_lists.explode().value_counts()
    theme_set = {x for x in counts[(counts >= 2) & (counts <= max(2, 0.10 * len(meta)))].index if x and not is_operational_tag(x)}
    themes_of = tag_lists.map(lambda tags: tuple(sorted(set(tags) & theme_set)))
    lists = {}
    for name, lo, hi, extra in (("tight", 0.95, 0.98, True), ("wide", 0.90, 0.98, True), ("wide, calm only", 0.90, 0.98, m["calm"])):
        t = candidate_trades(s, Rule(lo, hi, 3, 60), signal=(ask > lo) & (ask <= hi) & m["ok"] & m["single"] & extra)
        t = t.join(tm.band_flow(tr, t, lo, hi, min_cum), on="market_id")
        fee_rate = t["entry_fee"] / (t["entry_px"] * (1 - t["entry_px"]))
        t["cost_vwap"] = t["vwap"] + fee_rate * t["vwap"] * (1 - t["vwap"])
        t["ret_vwap"] = (t["proceeds"] - t["cost_vwap"]) / t["cost_vwap"]
        t["themes"] = t["market_id"].map(themes_of)
        t["universe"] = label
        lists[f"{label} {name}"] = t
    return lists


def accounts() -> None:
    meta, tr, p = att.panel(LO, HI)
    lists = trade_lists(meta, tr, ready(p), "thin", LO)
    del tr, p
    gc.collect()
    meta, tr, p = att.panel(100_000, att.TOP, ("big",))
    lists.update(trade_lists(meta, tr, ready(p), "big", 100_000))
    del tr, p
    gc.collect()
    summary = pd.DataFrame([tm.describe(k, v) for k, v in lists.items()])
    summary.to_csv(OUT / "cor_trades.csv", index=False)
    print("\nthe trade lists on the corrected universes (first print as in every backtest; 3-day average as a larger order would pay)\n")
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
    acc.to_csv(OUT / "cor_accounts.csv", index=False)
    print(f"\naccounts: positions at most {tm.PARTICIPATION:.0%} of the in-range flow, priced at the 3-day average, one position per event, "
          "four per story, at most 80% invested\n")
    print(acc.round(1).to_string(index=False))


def first_round() -> None:
    """The first round's rules in big markets: as they were, and with the short-lived markets put back."""
    rows = []
    new_meta, _, new_p = att.panel(100_000, att.TOP, ("big",))
    old_ids = set(tm.big_meta()["market_id"])
    back = new_meta[~new_meta["market_id"].isin(old_ids)]
    print(f"big markets: {len(old_ids):,} as the first round had them; {len(back):,} short-lived markets put back "
          f"(Yes won in {100 * float((back['winner'] == 0).mean()):.0f}% of those, against {100 * float((new_meta[new_meta['market_id'].isin(old_ids)]['winner'] == 0).mean()):.0f}% of the rest)")
    for uni, p, meta in (("as the first round had it", old_panel(OLD_BIG, tm.big_meta(), 100_000), tm.big_meta()), ("short-lived markets put back", new_p, new_meta)):
        s = ready(p)
        yn = ((meta.set_index("market_id")["outcome0"].str.strip().str.lower() == "yes") & (meta.set_index("market_id")["outcome1"].str.strip().str.lower() == "no"))
        yn = yn.reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
        m = masks(s)
        ask, dte, side, end = s["ask"].to_numpy(), s["days_to_end"].to_numpy(), s["side"].to_numpy(), s["end_ts"].to_numpy()
        hold = end < SPLIT_TS
        specs = [("R1d: 95-99c, legs included, holdout (the confirmed test)", 0.95, 0.99, m["ok"] & hold),
                 ("R1d: 95-99c, legs included, all three years", 0.95, 0.99, m["ok"]),
                 ("R1: 90-97c, legs included, holdout", 0.90, 0.97, m["ok"] & hold),
                 ("main rule: 95-98c, stand-alone, holdout", 0.95, 0.98, m["ok"] & m["single"] & hold),
                 ("main rule: 95-98c, stand-alone, all three years", 0.95, 0.98, m["ok"] & m["single"]),
                 ("90-98c, stand-alone, all three years", 0.90, 0.98, m["ok"] & m["single"]),
                 ("stand-alone No, 95-99c", 0.95, 0.99, m["ok"] & m["single"] & yn & (side == 1)),
                 ("stand-alone Yes, 95-99c", 0.95, 0.99, m["ok"] & m["single"] & yn & (side == 0)),
                 ("leader: leg Yes, 95-99c", 0.95, 0.99, m["ok"] & ~m["single"] & yn & (side == 0)),
                 ("stand-alone No, 50-90c", 0.50, 0.90, m["ok"] & m["single"] & yn & (side == 1)),
                 ("long-dated No: 90-98c, 60-180 days, scheduled end passed", 0.90, 0.98, (dte > 60) & (dte <= 180) & m["single"] & yn & (side == 1) & (end <= SCHEDULED_BY))]
        for name, lo, hi, mask in specs:
            t = candidate_trades(s, Rule(lo, hi, 3, 60), signal=(ask > lo) & (ask <= hi) & mask)
            row = line(t)
            row["of them in the markets put back"] = int((~t["market_id"].isin(old_ids)).sum())
            row["lost there"] = int(((t["won"] == 0) & ~t["market_id"].isin(old_ids)).sum())
            rows.append({"rule": name, "universe": uni, **row})
        del p, s
        gc.collect()
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "cor_first_round.csv", index=False)
    for name, g in res.groupby("rule", sort=False):
        print(f"\n{name}\n", g.drop(columns="rule").round(2).to_string(index=False))


def main() -> None:
    print("#" * 110 + "\n1. The first round's rules in big markets\n" + "#" * 110)
    first_round()
    print("\n" + "#" * 110 + "\n2. Round two's rules in thin markets\n" + "#" * 110)
    kept = rules_table()
    tm_verdict(kept)
    uni = AT_THE_TIME
    bid_then_ask(kept["panel"], kept[uni]["thin account: 90-98c, stand-alone, calm, at the ask"], kept[uni]["thin account's signals with a resting bid (TM)"])
    del kept
    gc.collect()
    print("\n" + "#" * 110 + "\n3. What the markets could take, and the accounts\n" + "#" * 110)
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
    with (OUT / "corrections_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
