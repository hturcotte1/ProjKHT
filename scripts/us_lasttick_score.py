"""Score the live recordings of crypto markets' last minutes by the rule of test L1.

docs/11_crypto_us.md, section 5. The recorder (kht us-lasttick) wrote down
books with sizes; this applies the rule to them, looks up what each market
settled at, and keeps two paper accounts.

    python scripts/us_lasttick_score.py [--state state/us-lasttick] [--settle] [--out reports/research]

``--settle`` asks the exchange what the traded markets settled at (public,
no key) and remembers the answers in <state>/settlements.csv.

What this prints is items 1 and 4 of the evidence listed in docs/11. A
column of trades with no loss in it is what the rule produces almost
always, whether it is sound or not. It is not the evidence that it is.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

from kht.trading import lasttick_rule as rule  # noqa: E402

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
ORDER = ["trade", "out of reach, but the book disagrees", "out of reach, nobody bidding", "out of reach, nobody offering", "within reach",
         "no fresh index level", "cannot be read", "no reach for this coin and horizon", "outside the time window"]
MIN_DAYS, MIN_A_DAY = 5, 50.0            # what docs/11 asks of the small account before a real test is worth discussing


def load(state: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Every run's readings, markets and index levels."""
    runs = sorted((state / "runs").glob("*")) if (state / "runs").exists() else []
    books = [pd.read_csv(r / "books.csv.gz") for r in runs if (r / "books.csv.gz").exists()]
    markets = [pd.read_csv(r / "markets.csv") for r in runs if (r / "markets.csv").exists()]
    index = [pd.read_csv(r / "index.csv") for r in runs if (r / "index.csv").exists()]
    b = pd.concat(books, ignore_index=True) if books else pd.DataFrame()
    m = pd.concat(markets, ignore_index=True) if markets else pd.DataFrame()
    i = pd.concat(index, ignore_index=True) if index else pd.DataFrame()
    if len(m):
        # a market followed in two runs: its terms are the same; the price to beat is whichever run had it
        m = m.sort_values("first_seen").groupby("slug", as_index=False).agg({c: "last" for c in m.columns if c != "slug"} | {"price_to_beat": "max"})
    return b, m, i


class Levels:
    """The newest index level of a coin that had been published by a given moment."""

    def __init__(self, index: pd.DataFrame):
        self.by_coin = {c: g.sort_values("ts")[["ts", "level", "at"]].to_numpy() for c, g in index.groupby("coin")} if len(index) else {}

    def at(self, coin: str, ts: float) -> tuple[float | None, float | None]:
        a = self.by_coin.get(coin)
        if a is None:
            return None, None
        k = int(np.searchsorted(a[:, 0], ts, side="right")) - 1
        return (None, None) if k < 0 else (float(a[k, 1]), float(a[k, 2]))


def apply(books: pd.DataFrame, markets: pd.DataFrame, index: pd.DataFrame, reach: dict) -> tuple[list[dict], pd.DataFrame]:
    """The rule on every followed market: its trade, if any, and for every market what became of it."""
    levels = Levels(index)
    terms = {m["slug"]: m for m in markets.to_dict("records")}
    trades, fate = [], []
    for slug, g in books.sort_values("ts").groupby("slug", sort=False):
        m = terms.get(slug)
        if m is None:
            continue
        got, best, seen = None, "outside the time window", 0
        for b in g.to_dict("records"):
            level, level_at = levels.at(m["coin"], b["ts"])
            t, why = rule.decide(m, b, float(b["ts"]), level, level_at, reach)
            if why != "outside the time window":
                seen += 1
                best = why                                   # for a market never traded: how its last reading in the window was judged
            if t is not None:
                got = t
                break
        if got is not None:
            trades.append(got)
        fate.append({"slug": slug, "coin": m["coin"], "kind": m["kind"], "horizon": m["horizon"], "end": float(m["end"]), "readings": seen,
                     "fate": "trade" if got is not None else best})
    return trades, pd.DataFrame(fate)


def settlements(state: Path, slugs: list[str], look_up: bool) -> pd.Series:
    """What each market settled at, remembered in <state>/settlements.csv; ``look_up`` asks the exchange for the missing ones."""
    path = state / "settlements.csv"
    known = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["slug", "settle", "checked"])
    have = set(known.loc[known["settle"].notna(), "slug"])
    missing = [s for s in slugs if s not in have]
    if look_up and missing:
        from kht.api.http import Http
        from kht.api.polymarket_us import PolymarketUS

        us = PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": 6.0}))
        rows = [{"slug": s, "settle": us.settlement(s), "checked": int(time.time())} for s in missing]
        known = pd.concat([known[~known["slug"].isin(missing)], pd.DataFrame(rows)], ignore_index=True)
        known.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)
    return known.dropna(subset=["settle"]).set_index("slug")["settle"].astype(float)


def account(trades: list[dict], settle: pd.Series) -> pd.DataFrame:
    t = pd.DataFrame(trades)
    if not len(t):
        return t
    t["settle"] = t["slug"].map(settle)
    t["pnl"] = [rule.pnl(r, r["settle"]) if pd.notna(r["settle"]) else np.nan for r in t.to_dict("records")]
    t["lost"] = t["pnl"] < 0
    t["end_utc"] = pd.to_datetime(t["end"], unit="s").dt.strftime("%Y-%m-%d %H:%M")
    t["day"] = pd.to_datetime(t["end"], unit="s").dt.strftime("%Y-%m-%d")
    return t


def by(t: pd.DataFrame, key: str) -> pd.DataFrame:
    if not len(t):
        return pd.DataFrame()
    g = t.groupby(key).agg(trades=("slug", "size"), contracts=("qty", "sum"), locked=("locked", "sum"), premium=("premium", "sum"),
                           settled=("settle", lambda s: int(s.notna().sum())), lost=("lost", "sum"), pnl=("pnl", "sum")).reset_index()
    return g


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="state/us-lasttick")
    ap.add_argument("--reach", default=str(ROOT / "config" / "lasttick_reach.json"))
    ap.add_argument("--settle", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "reports" / "research"))
    args = ap.parse_args()
    state, out = Path(args.state), Path(args.out)
    books, markets, index = load(state)
    lines = ["Test L1 on live books (docs/11_crypto_us.md, section 5). No order was placed: these are paper trades against orders seen in the book."]
    if not len(books):
        lines.append("Nothing has been recorded yet.")
        print("\n".join(lines))
        return
    reach = rule.load_reach(Path(args.reach))
    trades, fate = apply(books, markets, index, reach)
    settle = settlements(state, [t["slug"] for t in trades], args.settle)
    everything = account(trades, settle)
    small = account(rule.small_account(trades), settle)
    ends = fate.groupby("end").size()
    daily_ends = fate[fate["horizon"].isin(["daily", "weekly", "monthly", "1d"])]["end"].nunique()
    first, last = pd.Timestamp(books["ts"].min(), unit="s"), pd.Timestamp(books["ts"].max(), unit="s")
    lines += [f"recorded: {first:%d %B %H:%M} to {last:%d %B %H:%M} UTC; {len(books):,} readings of {len(fate):,} markets ending at {len(ends):,} different times, "
              f"{daily_ends} of them the time of a daily settlement", "",
              "what became of each market followed (a market is counted once, by how the rule judged it)"]
    counts = fate["fate"].value_counts()
    lines += [f"   {k:<42} {int(counts.get(k, 0)):>6,}" for k in ORDER if counts.get(k, 0)]
    fate.to_csv(out / "lt_fate.csv", index=False)
    for name, t in (("L1-all (every trade the rule finds, 2,000 contracts a market at most)", everything), ("L1-10k ($10,000 to lock at each settlement time)", small)):
        lines += ["", name]
        if not len(t):
            lines.append("   no trade")
            continue
        done = t[t["settle"].notna()]
        lines.append(f"   trades {len(t):,} ({int((t['side'] == 'sell').sum()):,} sales, {int((t['side'] == 'buy').sum()):,} purchases); contracts {t['qty'].sum():,.0f}; "
                     f"premium after the fee ${t['premium'].sum():,.2f}; most locked at one settlement ${t.groupby('end')['locked'].sum().max():,.0f}")
        lines.append(f"   settled {len(done):,} of {len(t):,}; lost {int(done['lost'].sum()):,}; result ${done['pnl'].sum():,.2f}")
        d = by(t, "day")
        lines.append("   by day of settlement (UTC):")
        lines.append("   " + d.round(2).to_string(index=False).replace("\n", "\n   "))
    everything.to_csv(out / "lt_trades.csv", index=False)
    by(everything, "end_utc").to_csv(out / "lt_by_end.csv", index=False)
    small.to_csv(out / "lt_trades_10k.csv", index=False)
    if len(small):
        d = by(small, "day")
        with_daily = set(pd.to_datetime(fate.loc[fate["horizon"].isin(["daily", "1d"]), "end"], unit="s").dt.strftime("%Y-%m-%d"))
        d = d[d["day"].isin(with_daily)]
        lost = int(everything["lost"].sum())
        lines += ["", f"what docs/11 asks before a real test is worth discussing: {MIN_DAYS} daily settlements recorded (so far {len(with_daily)}), "
                      f"L1-10k collecting ${MIN_A_DAY:.0f} a day on average (so far ${d['premium'].mean() if len(d) else 0.0:,.2f} over {len(d)} days), "
                      f"and no result that was out of reach coming in (so far {lost} lost)."]
    refused = fate[fate["fate"] == "out of reach, but the book disagrees"]
    if len(refused):
        lines += ["", f"{len(refused)} markets were out of reach by the rule while their book said otherwise. They were not traded. Each is a fact to check:",
                  "   " + refused[["slug", "end"]].assign(end=pd.to_datetime(refused["end"], unit="s")).to_string(index=False).replace("\n", "\n   ")]
    text = "\n".join(lines) + "\n"
    (out / "lt_summary.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    sys.exit(main())
