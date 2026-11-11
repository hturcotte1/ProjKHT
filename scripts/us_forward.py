"""Score the forward tests on Polymarket US from what the recorder has written down.

    python scripts/us_forward.py [--state state/us] [--settle]

It needs nothing but the committed files under state/us and, with --settle,
the public settlement prices. It reports:

  A. the recorder itself: cycles, the gaps between them, books per cycle;
  B. rewards for resting orders (docs/08_rewards.md): how often each
     programme paid nobody, and how crowded the paid sides are;
  C. F1, the two-exchange test fixed in docs/07_two_venues.md, section 3;
  D. F2, the stand-alone "No" rule fixed in docs/06_polymarket_us.md, section 8;
  E. how many dollars of new gaps between the two exchanges appear each day.

Everything is written to reports/research/usf_*.csv and us_forward_output.txt.
The tests themselves are not chosen here: C and D apply rules that were
committed before the recorder had any data.
"""

from __future__ import annotations

import argparse
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kht.api.polymarket_us import PolymarketUS, taker_fee_per_share
from kht.research import factory as fx

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 200)
pd.set_option("display.max_colwidth", 70)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
DAY = 86_400
STAKE = 50.0                         # dollars per paper purchase, at most
GAP = 0.03                           # F1: the gap after the fee that triggers a purchase
MAX_INTL_SPREAD = 0.10               # F1: the polymarket.com book must be two-sided and no wider than this
HORIZONS = (1, 3, 7)                 # days after purchase at which F1 is marked
DEADLINE = re.compile(r"^(?:by |before |on or before |prior to )?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.? \d{1,2}(?:st|nd|rd|th)?(?:, \d{4})?$|^(?:by|before) ")


def load(state: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    snaps = pd.concat([pd.read_csv(p) for p in sorted((state / "snapshots").glob("*/*.csv.gz"))], ignore_index=True)
    markets = pd.read_csv(state / "markets.csv").drop_duplicates("slug")
    log = pd.read_csv(state / "log.csv")
    rewards = pd.read_csv(state / "rewards.csv") if (state / "rewards.csv").exists() else pd.DataFrame()
    return snaps, markets, log, rewards


def section_recorder(log: pd.DataFrame) -> list[str]:
    t = pd.to_datetime(log["ts"], unit="s")
    gaps = t.diff().dt.total_seconds().dropna() / 3600
    out = ["A. The recorder", f"   cycles: {len(log)}, from {t.min():%d %b %H:%M} to {t.max():%d %b %H:%M} UTC",
           f"   books per cycle: median {log['books_read'].median():,.0f}; two-sided: {log['two_sided'].median():,.0f}; with a twin: {log['twins'].median():,.0f}"]
    if len(gaps):
        out.append(f"   hours between cycles: median {gaps.median():.1f}, longest {gaps.max():.1f}; errors in all: {int(log['errors'].sum())}")
    return out


def section_rewards(rewards: pd.DataFrame) -> tuple[list[str], pd.DataFrame]:
    if rewards.empty:
        return ["B. Rewards: no cycle has recorded the schedule yet"], pd.DataFrame()
    r = rewards.copy()
    r["sides"] = 2 * r["markets"]
    r["paid"] = r["bid_sides_paid"] + r["ask_sides_paid"]
    g = r.groupby("program").agg(cycles=("ts", "nunique"), pool=("pool", "last"), target=("target", "last"), max_spread=("max_spread", "last"), markets=("markets", "last"),
                                 sides_paid_mean=("paid", "mean"), sides_paid_min=("paid", "min"), sides_paid_max=("paid", "max"),
                                 cycles_nobody_paid=("paid", lambda x: int((x == 0).sum())), first_seen=("ts", "min")).reset_index().sort_values("pool", ascending=False)
    g["first_seen"] = pd.to_datetime(g["first_seen"], unit="s").dt.strftime("%d %b %H:%M")
    n = r["ts"].nunique()
    empty = g[g["cycles_nobody_paid"] == g["cycles"]]
    out = [f"B. Rewards for resting orders, over {n} cycle(s)",
           f"   programmes followed: {len(g)}; paid to nobody in every cycle so far: {len(empty)} ({', '.join(empty['program']) or 'none'})"]
    return out, g


def first_gaps(snaps: pd.DataFrame, gap: float = GAP) -> pd.DataFrame:
    """F1 purchases: the first snapshot at which a market's US quote is beyond a tradable polymarket.com quote by ``gap`` after the fee."""
    s = snaps[snaps["intl_bid"].notna() & snaps["intl_ask"].notna() & ((snaps["intl_ask"] - snaps["intl_bid"]) <= MAX_INTL_SPREAD + 1e-9)].copy()
    s["gap_yes"] = s["intl_bid"] - s["ask1"] - taker_fee_per_share(s["ask1"])
    s["gap_no"] = s["bid1"] - s["intl_ask"] - taker_fee_per_share(s["bid1"])
    s["gap"] = s[["gap_yes", "gap_no"]].max(axis=1)
    k = s[s["gap"] >= gap].sort_values("ts").drop_duplicates("slug", keep="first").copy()
    yes = k["gap_yes"].fillna(-1) >= k["gap_no"].fillna(-1)
    k["side"] = np.where(yes, "yes", "no")
    k["price"] = np.where(yes, k["ask1"], 1.0 - k["bid1"])
    k["cost"] = np.where(yes, k["ask1"] + taker_fee_per_share(k["ask1"]), 1.0 - k["bid1"] + taker_fee_per_share(k["bid1"]))
    on_offer = np.where(yes, k["ask_qty1"], k["bid_qty1"])
    k["contracts"] = np.minimum(on_offer, STAKE / k["price"])
    k["intl_value"] = np.where(yes, (k["intl_bid"] + k["intl_ask"]) / 2, 1.0 - (k["intl_bid"] + k["intl_ask"]) / 2)
    return k[["ts", "slug", "side", "price", "cost", "contracts", "gap", "intl_value", "bid1", "ask1", "intl_bid", "intl_ask"]]


def mark(k: pd.DataFrame, snaps: pd.DataFrame, days: float) -> pd.DataFrame:
    """Each purchase marked at the first snapshot at least ``days`` later (and no more than a day after that)."""
    later = snaps[["ts", "slug", "bid1", "ask1", "intl_bid", "intl_ask"]].rename(columns={"ts": "ts2", "bid1": "bid2", "ask1": "ask2", "intl_bid": "ib2", "intl_ask": "ia2"})
    m = k.merge(later, on="slug")
    m = m[(m["ts2"] >= m["ts"] + days * DAY) & (m["ts2"] <= m["ts"] + (days + 1) * DAY)].sort_values("ts2").drop_duplicates("slug", keep="first").copy()
    yes = m["side"] == "yes"
    # what the position could be sold for on Polymarket US: "Yes" to the bid; "No" by buying "Yes" at the ask
    m["us_exit"] = np.where(yes, m["bid2"] - taker_fee_per_share(m["bid2"]), 1.0 - m["ask2"] - taker_fee_per_share(m["ask2"]))
    m["intl_mark"] = np.where(yes, (m["ib2"] + m["ia2"]) / 2, 1.0 - (m["ib2"] + m["ia2"]) / 2)
    m["pnl_us"] = m["us_exit"] - m["cost"]
    m["pnl_intl"] = m["intl_mark"] - m["cost"]
    return m


def section_f1(snaps: pd.DataFrame, markets: pd.DataFrame, settle: bool) -> tuple[list[str], pd.DataFrame]:
    k = first_gaps(snaps).merge(markets[["slug", "event_id", "event_title", "label", "category", "end_date"]], on="slug", how="left")
    out = [f"C. F1, two exchanges forward: purchases so far {len(k)} in {k['event_id'].nunique()} events; "
           f"${(k['price'] * k['contracts']).sum():,.0f} spent at ${STAKE:.0f} or the size on offer; average gap {100 * k['gap'].mean() if len(k) else float('nan'):.1f}c"]
    for d in HORIZONS:
        m = mark(k, snaps, d)
        for col, what in (("pnl_us", "sold on Polymarket US"), ("pnl_intl", "at the polymarket.com middle")):
            x = m[m[col].notna()]
            if len(x) >= 2:
                mean, t = fx.clustered(x[col].to_numpy(), x["event_id"].fillna(-1).to_numpy())
                out.append(f"   after {d} day(s), {what}: {len(x)} purchases, {100 * mean:+.2f}c a contract (t {t:.2f} by event), {100 * (x[col] > 0).mean():.0f}% ahead")
            else:
                out.append(f"   after {d} day(s), {what}: {len(x)} purchases marked so far")
        k = k.merge(m[["slug", "pnl_us", "pnl_intl"]].rename(columns={"pnl_us": f"pnl_us_{d}d", "pnl_intl": f"pnl_intl_{d}d"}), on="slug", how="left")
    if settle and len(k):
        pm = PolymarketUS()
        k["yes_settle"] = [pm.settlement(s) for s in k["slug"]]
        done = k[k["yes_settle"].notna()].copy()
        if len(done) >= 2:
            done["paid"] = np.where(done["side"] == "yes", done["yes_settle"], 1.0 - done["yes_settle"])
            r = (done["paid"] - done["cost"]) / done["cost"]
            mean, z = fx.floored(r.to_numpy(), done["cost"].to_numpy(), done["event_id"].fillna(-1).to_numpy())
            out.append(f"   at settlement: {len(done)} settled, mean return {100 * mean:+.1f}% (z {z:.2f} by event)")
        else:
            out.append(f"   at settlement: {len(done)} settled so far")
    out.append("   confirmed if, at 7 days sold on Polymarket US, the mean is positive with t >= 2.58 on at least 100 purchases (docs/07, section 3)")
    return out, k


def shapes(snaps: pd.DataFrame, markets: pd.DataFrame) -> pd.Series:
    """Stand-alone or not, by slug, from what the recorder knows: the US analogue of ``us_shape`` in scripts/factory.py."""
    m = markets.set_index("slug")
    n_event = m.groupby("event_id")["market_id"].transform("size").fillna(1)
    s = snaps[snaps["bid1"].notna() & snaps["ask1"].notna()].copy()
    s["mid"] = (s["bid1"] + s["ask1"]) / 2
    s["event_id"] = m["event_id"].reindex(s["slug"]).to_numpy()
    day = s.groupby(["event_id", "ts"])["mid"].agg(["sum", "size"]).reset_index()
    size = m.groupby("event_id")["market_id"].size()
    day = day[day["size"] >= np.maximum(2, 0.5 * size.reindex(day["event_id"]).to_numpy())]
    med = day.groupby("event_id")["sum"].median().reindex(m["event_id"]).to_numpy()
    label = m["label"].fillna("").str.strip().str.lower()
    shape = np.where(n_event.to_numpy() <= 1, "single", np.where(label.str.match(DEADLINE).to_numpy(), "deadline",
                     np.where((med >= 0.8) & (med <= 1.2), "exclusive", np.where((med < 0.7) | (med > 1.3), "collection", "unknown"))))
    return pd.Series(shape, index=m.index)


def section_f2(snaps: pd.DataFrame, markets: pd.DataFrame, settle: bool) -> tuple[list[str], pd.DataFrame]:
    shape = shapes(snaps, markets)
    end = pd.to_datetime(markets.set_index("slug")["end_date"], errors="coerce", utc=True)
    s = snaps[snaps["bid1"].notna() & snaps["ask1"].notna()].copy()
    s["no_ask"] = 1.0 - s["bid1"]
    s["dte"] = (end.reindex(s["slug"]).to_numpy() - pd.to_datetime(s["ts"], unit="s", utc=True).to_numpy()) / np.timedelta64(1, "D")
    s["shape"] = shape.reindex(s["slug"]).to_numpy()
    ok = (s["shape"].isin(["single", "deadline", "collection"]) & (s["no_ask"] > 0.90) & (s["no_ask"] <= 0.98) & ((s["ask1"] - s["bid1"]) <= 0.05 + 1e-9)
          & (s["dte"] > 3) & (s["dte"] <= 60))
    sig = s[ok].sort_values("ts").drop_duplicates("slug", keep="first")[["ts", "slug", "shape", "dte"]]
    # bought at the next snapshot, if "No" is still on offer between 90c and 98c there
    nxt = s[["ts", "slug", "no_ask", "bid_qty1"]].rename(columns={"ts": "ts2"})
    k = sig.merge(nxt, on="slug")
    k = k[(k["ts2"] > k["ts"]) & (k["ts2"] <= k["ts"] + 3 * DAY)].sort_values("ts2").drop_duplicates("slug", keep="first")
    k = k[(k["no_ask"] > 0.90) & (k["no_ask"] <= 0.985)].copy()
    k["cost"] = k["no_ask"] + taker_fee_per_share(k["no_ask"])
    k["contracts"] = np.minimum(k["bid_qty1"], STAKE / k["no_ask"])
    k = k.merge(markets[["slug", "event_id", "event_title", "label", "category"]], on="slug", how="left")
    out = [f"D. F2, \"No\" on a stand-alone question at 90-98c: signals {len(sig)}, purchases {len(k)} in {k['event_id'].nunique()} events; "
           f"median on offer at the best price: {k['bid_qty1'].median() if len(k) else float('nan'):,.0f} contracts"]
    if settle and len(k):
        pm = PolymarketUS()
        k["yes_settle"] = [pm.settlement(s_) for s_ in k["slug"]]
        done = k[k["yes_settle"].notna()]
        if len(done) >= 2:
            r = ((1.0 - done["yes_settle"]) - done["cost"]) / done["cost"]
            mean, z = fx.floored(r.to_numpy(), done["cost"].to_numpy(), done["event_id"].fillna(-1).to_numpy())
            out.append(f"   settled: {len(done)}, lost {int((done['yes_settle'] == 1).sum())}, mean return {100 * mean:+.2f}% (z {z:.2f} by event)")
        else:
            out.append(f"   settled so far: {len(done)}")
    out.append("   confirmed if the mean return is positive with z >= 2.58 by event on at least 300 purchases (docs/06, section 8)")
    return out, k


def section_flow(snaps: pd.DataFrame) -> list[str]:
    k = first_gaps(snaps)
    if k.empty:
        return ["E. New gaps of 3c or more: none yet"]
    first = snaps["ts"].min()
    fresh = k[k["ts"] > first]                               # gaps present at the first snapshot are a stock, not a flow
    days = max((snaps["ts"].max() - first) / DAY, 1e-9)
    worth = (fresh["gap"] * fresh["contracts"]).sum()
    return [f"E. Gaps of 3c or more: {int((k['ts'] == first).sum())} were there at the first snapshot; {len(fresh)} new ones in {days:.1f} days since "
            f"({len(fresh) / days:.1f} a day), worth ${worth:,.2f} at the paper size (${worth / days:,.2f} a day)"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=str(ROOT / "state" / "us"))
    ap.add_argument("--settle", action="store_true", help="also look up settlement prices (one public request per paper purchase)")
    args = ap.parse_args()
    snaps, markets, log, rewards = load(Path(args.state))
    lines = [f"Forward tests on Polymarket US, from {snaps['ts'].nunique()} snapshot(s), {len(snaps):,} rows", ""]
    lines += section_recorder(log) + [""]
    rw_lines, rw = section_rewards(rewards)
    lines += rw_lines + [""]
    f1_lines, f1 = section_f1(snaps, markets, args.settle)
    lines += f1_lines + [""]
    f2_lines, f2 = section_f2(snaps, markets, args.settle)
    lines += f2_lines + [""] + section_flow(snaps)
    OUT.mkdir(parents=True, exist_ok=True)
    if len(rw):
        rw.to_csv(OUT / "usf_rewards.csv", index=False)
    f1.to_csv(OUT / "usf_f1_purchases.csv", index=False)
    f2.to_csv(OUT / "usf_f2_purchases.csv", index=False)
    text = "\n".join(lines) + "\n"
    if len(rw):
        text += "\nreward programmes\n" + rw.round(2).to_string(index=False) + "\n"
    (OUT / "us_forward_output.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
