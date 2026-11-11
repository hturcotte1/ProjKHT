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
ORDER = ["trade", "out of reach, but the book disagrees", "out of reach, nobody bidding", "out of reach, nobody offering",
         "out of reach, but the index has been moving fast", "out of reach, too little index history", "within reach",
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


def known_levels(state: Path, index: pd.DataFrame, markets: pd.DataFrame, look_up: bool) -> dict[str, list[tuple[float, float]]]:
    """Each coin's index levels as (moment, level): those the recorder saw, and those looked up since for the brake.

    The brake needs the hour before every reading. The recorder only has
    the levels published while it ran, so with ``look_up`` the missing
    five-minute marks are asked for (public, no key) and remembered in
    <state>/levels.csv. A level looked up later is used for the brake
    only, never as "where the price is" at a reading.
    """
    path = state / "levels.csv"
    cached = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["coin", "at", "level"])
    have = {(c, float(a)): float(v) for c, a, v in cached.dropna(subset=["level"]).itertuples(index=False)}
    if len(index):
        have.update({(c, float(a)): float(v) for c, a, v in index[["coin", "at", "level"]].itertuples(index=False)})
    if look_up and len(markets):
        from kht.api.http import Http
        from kht.api.polymarket_us import PolymarketUS
        from kht.trading.us_recorder import _amount

        tried = {(c, float(a)) for c, a in cached[["coin", "at"]].itertuples(index=False)}
        want = set()
        for coin, end in markets[["coin", "end"]].drop_duplicates().itertuples(index=False):
            first = (int(end) - rule.FIRST - rule.BRAKE_WINDOW - rule.BRAKE_STEP) // rule.BRAKE_STEP * rule.BRAKE_STEP
            want |= {(coin, float(m)) for m in range(first, int(end) - rule.LAST + 1, rule.BRAKE_STEP) if coin in rule.PRODUCT}
        missing = sorted(want - set(have) - tried)
        if missing:
            us = PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": 6.0}))
            rows = []
            for coin, at in missing:
                try:
                    level = _amount((us.market(rule.updown_slug(coin, "5m", at)).get("assetPriceTerms") or {}).get("priceToBeat"))
                except Exception:
                    level = None
                rows.append({"coin": coin, "at": at, "level": level})
                if level is not None:
                    have[(coin, at)] = level
            pd.concat([cached, pd.DataFrame(rows)], ignore_index=True).to_csv(path, index=False)
    out: dict[str, list[tuple[float, float]]] = {}
    for (coin, at), level in sorted(have.items()):
        out.setdefault(coin, []).append((at, level))
    return out


def apply(books: pd.DataFrame, markets: pd.DataFrame, index: pd.DataFrame, reach: dict, brake: dict | None = None,
          history: dict[str, list[tuple[float, float]]] | None = None) -> tuple[list[dict], pd.DataFrame]:
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
            t, why = rule.decide(m, b, float(b["ts"]), level, level_at, reach, brake, (history or {}).get(m["coin"]))
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
    ap.add_argument("--settle", action="store_true", help="ask the exchange for settlements and for index levels the recorder did not see")
    ap.add_argument("--out", default=str(ROOT / "reports" / "research"))
    args = ap.parse_args()
    state, out = Path(args.state), Path(args.out)
    books, markets, index = load(state)
    lines = ["Test L1 on live books (docs/11_crypto_us.md, section 5). No order was placed: these are paper trades against orders seen in the book."]
    if not len(books):
        lines.append("Nothing has been recorded yet.")
        print("\n".join(lines))
        return
    strict = rule.load_reach(Path(args.reach))
    recent, brake = rule.load_recent(Path(args.reach))
    history = known_levels(state, index, markets, args.settle)
    runs = {"L1-recent": apply(books, markets, index, recent, brake, history), "L1-strict": apply(books, markets, index, strict)}
    settle = settlements(state, sorted({t["slug"] for trades, _ in runs.values() for t in trades}), args.settle)
    fate = runs["L1-recent"][1]
    ends = fate.groupby("end").size()
    daily = set(pd.to_datetime(fate.loc[fate["horizon"].isin(["daily", "1d"]), "end"], unit="s").dt.strftime("%Y-%m-%d"))
    first, last = pd.Timestamp(books["ts"].min(), unit="s"), pd.Timestamp(books["ts"].max(), unit="s")
    lines += [f"recorded: {first:%d %B %H:%M} to {last:%d %B %H:%M} UTC; {len(books):,} readings of {len(fate):,} markets ending at {len(ends):,} different times, "
              f"{len(daily)} of them a daily settlement"]
    for name, (trades, f) in runs.items():
        tag = name.split("-")[1]
        counts = f["fate"].value_counts()
        lines += ["", f"===== {name}: " + ("the reach of 2023 to 2026, with the brake" if tag == "recent" else "the reach of the worst year since 2020, as first written") + " =====",
                  "what became of each market followed (a market is counted once, by how the rule judged it)"]
        lines += [f"   {k:<50} {int(counts.get(k, 0)):>6,}" for k in ORDER if counts.get(k, 0)]
        f.to_csv(out / f"lt_fate_{tag}.csv", index=False)
        everything = account(trades, settle)
        small = account(rule.small_account(trades), settle)
        for label, t in ((f"{name}-all (every trade the rule finds, 2,000 contracts a market at most)", everything),
                         (f"{name}-10k ($10,000 to lock at each settlement time)", small)):
            lines += ["", label]
            if not len(t):
                lines.append("   no trade")
                continue
            done = t[t["settle"].notna()]
            lines.append(f"   trades {len(t):,} ({int((t['side'] == 'sell').sum()):,} sales, {int((t['side'] == 'buy').sum()):,} purchases); contracts {t['qty'].sum():,.0f}; "
                         f"premium after the fee ${t['premium'].sum():,.2f}; most locked at one settlement ${t.groupby('end')['locked'].sum().max():,.0f}")
            lines.append(f"   settled {len(done):,} of {len(t):,}; lost {int(done['lost'].sum()):,}; result ${done['pnl'].sum():,.2f}")
            far = t["gap"] / t["reach"]
            lines.append("   how far out of reach, by premium: " + "; ".join(
                f"more than {k:g} times the reach ${t.loc[far > k, 'premium'].sum():,.2f} ({t.loc[far > k, 'qty'].sum():,.0f} contracts)" for k in (1.5, 2.0)))
            lines.append("   by day of settlement (UTC):")
            lines.append("   " + by(t, "day").round(2).to_string(index=False).replace("\n", "\n   "))
        everything.to_csv(out / f"lt_trades_{tag}.csv", index=False)
        small.to_csv(out / f"lt_trades_{tag}_10k.csv", index=False)
        by(everything, "end_utc").to_csv(out / f"lt_by_end_{tag}.csv", index=False)
        if tag == "recent":
            d = by(small, "day") if len(small) else pd.DataFrame(columns=["day", "premium"])
            d = d[d["day"].isin(daily)]
            lost = int(everything["lost"].sum()) if len(everything) else 0
            lines += ["", f"what docs/11 asks before a real test is worth discussing: {MIN_DAYS} daily settlements recorded (so far {len(daily)}); "
                          f"L1-recent-10k collecting ${MIN_A_DAY:.0f} a day on average (so far ${d['premium'].sum() / max(1, len(daily)):,.2f} over {len(daily)} days); "
                          f"and no result that was out of reach coming in (so far {lost} lost)."]
        refused = f[f["fate"] == "out of reach, but the book disagrees"]
        if len(refused):
            lines += ["", f"{len(refused)} markets were out of reach by this yardstick while their book said otherwise. They were not traded. Each is a fact to check:",
                      "   " + refused[["slug", "end"]].assign(end=pd.to_datetime(refused["end"], unit="s")).to_string(index=False).replace("\n", "\n   ")]
    text = "\n".join(lines) + "\n"
    (out / "lt_summary.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    sys.exit(main())
