"""Score the recordings of whole ladders by the rule of test L3.

docs/11_crypto_us.md, section 13. The second copy of the recorder
(kht us-lasttick --state state/us-ladder --kinds range ...) wrote down the
book of every daily and weekly bracket, with sizes, through the five and a
half hours before it settled. This applies the rule of L3 to each reading:
sell to the best bid of a bracket that is far enough, once a bracket, and
hold to settlement.

    python scripts/us_lasthours_score.py [--state state/us-ladder] [--settle] [--out reports/research]

``--settle`` asks the exchange what the sold brackets settled at, and for
the index levels the brake needs from before the recorder began (public,
no key). The answers are remembered in <state>/settlements.csv and
<state>/levels.csv.

The evening of 12 November 2026 was looked at before the rule was fixed.
It is shown apart and counted for nothing.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

from kht.trading import lasthours_rule as rule  # noqa: E402
from kht.trading import lasttick_rule as l1  # noqa: E402

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
COUNTED_FROM = 1_794_528_000.0            # 13 November 2026, 00:00 UTC: ladders ending before this were seen before the rule was fixed
MIN_EVENINGS, MIN_AN_EVENING = 4, 50.0    # the bar of docs/11, section 13
RECORDED, MOST, GRID = 120, 0.9, 120      # an evening counts if this many two-minute stretches found this share of the Bitcoin ladder read
MONEY = 10_000.0
ORDER = ["trade", "far enough, but the book disagrees", "far enough, nobody bidding", "far enough, but the index has been moving fast",
         "far enough, too little index history", "not far enough", "the index is in this bracket", "no fresh index level", "cannot be read",
         "no reach for this coin and time ahead", "outside the time window", "not a bracket of a daily or weekly ladder"]


def load(state: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Every run's readings, markets and index levels."""
    runs = sorted((state / "runs").glob("*")) if (state / "runs").exists() else []
    read = lambda name: [d for d in (pd.read_csv(r / name) for r in runs if (r / name).exists()) if len(d)]
    books, markets, index = read("books.csv.gz"), read("markets.csv"), read("index.csv")
    b = pd.concat(books, ignore_index=True) if books else pd.DataFrame()
    m = pd.concat(markets, ignore_index=True) if markets else pd.DataFrame()
    i = pd.concat(index, ignore_index=True) if index else pd.DataFrame()
    if len(m):
        m = m.sort_values("first_seen").drop_duplicates("slug", keep="last")
    return b, m, i


class Levels:
    """The newest index level of a coin that the recorder had seen published by a given moment."""

    def __init__(self, index: pd.DataFrame):
        self.by_coin = {c: g.sort_values("ts")[["ts", "level", "at"]].to_numpy() for c, g in index.groupby("coin")} if len(index) else {}

    def at(self, coin: str, ts: float) -> tuple[float | None, float | None]:
        a = self.by_coin.get(coin)
        if a is None:
            return None, None
        k = int(np.searchsorted(a[:, 0], ts, side="right")) - 1
        return (None, None) if k < 0 else (float(a[k, 1]), float(a[k, 2]))


def known_levels(state: Path, index: pd.DataFrame, markets: pd.DataFrame, look_up: bool) -> dict[str, list[tuple[float, float]]]:
    """Each coin's index levels as (moment, level), for the brake: those the recorder saw, and those looked up since.

    The brake looks at the hour before a reading, and the recorder only has
    the levels published while it ran. A level looked up later is used for
    the brake and never as "where the price is".
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
            first = (int(end) - rule.FIRST - l1.BRAKE_WINDOW - l1.BRAKE_STEP) // l1.BRAKE_STEP * l1.BRAKE_STEP
            want |= {(coin, float(m)) for m in range(first, int(end) - rule.LAST + 1, l1.BRAKE_STEP) if coin in l1.PRODUCT}
        missing = sorted(want - set(have) - tried)
        if missing:
            us = PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": 6.0}))
            rows = []
            for coin, at in missing:
                try:
                    level = _amount((us.market(l1.updown_slug(coin, "5m", at)).get("assetPriceTerms") or {}).get("priceToBeat"))
                except Exception:
                    level = None
                rows.append({"coin": coin, "at": at, "level": level})
                if level is not None:
                    have[(coin, at)] = level
            state.mkdir(parents=True, exist_ok=True)
            pd.concat([cached, pd.DataFrame(rows)], ignore_index=True).to_csv(path, index=False)
    out: dict[str, list[tuple[float, float]]] = {}
    for (coin, at), level in sorted(have.items()):
        out.setdefault(coin, []).append((at, level))
    return out


def apply(books: pd.DataFrame, markets: pd.DataFrame, index: pd.DataFrame, reach: dict, brake: dict | None = None,
          history: dict[str, list[tuple[float, float]]] | None = None) -> tuple[list[dict], pd.DataFrame]:
    """The rule on every bracket followed: its sale, if any, and for every bracket what became of it."""
    levels = Levels(index)
    terms = {m["slug"]: m for m in markets.to_dict("records")}
    trades, fate = [], []
    for slug, g in books.sort_values("ts").groupby("slug", sort=False):
        m = terms.get(slug)
        if m is None:
            continue
        rows = g.to_dict("records")
        got, best, seen = None, "outside the time window", 0
        for k, b in enumerate(rows):
            level, level_at = levels.at(m["coin"], b["ts"])
            t, why = rule.decide(m, b, float(b["ts"]), level, level_at, reach, brake, (history or {}).get(m["coin"]))
            if why not in ("outside the time window", "not a bracket of a daily or weekly ladder"):
                seen += 1
                best = why
            elif seen == 0:
                best = why
            if t is not None:
                nxt = rows[k + 1] if k + 1 < len(rows) else None
                # described, not judged: was the bid still there, at that price and for that size, at the next reading of this bracket?
                t["still_next"] = (None if nxt is None else
                                   bool((l1._f(nxt.get("bid1")) or 0.0) >= t["price"] - 1e-9 and (l1._f(nxt.get("bid_qty1")) or 0.0) >= t["qty"] - 1e-9))
                got = t
                break
        if got is not None:
            trades.append(got)
        fate.append({"slug": slug, "coin": m["coin"], "horizon": m["horizon"], "end": float(m["end"]), "readings": seen, "fate": "trade" if got is not None else best})
    return trades, pd.DataFrame(fate)


def settlements(state: Path, slugs: list[str], look_up: bool) -> dict[str, float]:
    """What "Yes" paid in each bracket, as far as known. The file is shared with the scorer of L2."""
    path = state / "settlements.csv"
    known = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["slug", "settle"])
    have = {s: float(v) for s, v in known[["slug", "settle"]].dropna(subset=["settle"]).itertuples(index=False)}
    missing = [s for s in slugs if s not in have]
    if look_up and missing:
        from kht.api.http import Http
        from kht.api.polymarket_us import PolymarketUS

        us = PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": 6.0}))
        for s in missing:
            v = us.settlement(s)
            if v is not None:
                have[s] = float(v)
        state.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(sorted(have.items()), columns=["slug", "settle"]).to_csv(path, index=False)
    return have


def recorded(books: pd.DataFrame, markets: pd.DataFrame) -> dict[float, int]:
    """For each settlement time: in how many two-minute stretches most of that evening's Bitcoin ladder was read."""
    out: dict[float, int] = {}
    m = markets[(markets["kind"] == "range") & (markets["coin"] == "btc") & markets["horizon"].isin(rule.HORIZONS)]
    for end, g in m.groupby("end"):
        g = g[g["horizon"] == ("daily" if (g["horizon"] == "daily").any() else "weekly")]
        b = books[books["slug"].isin(g["slug"])]
        b = b[(float(end) - b["ts"] >= rule.LAST - GRID) & (float(end) - b["ts"] <= rule.FIRST)]
        slot = ((float(end) - b["ts"]) // GRID).astype(int)
        out[float(end)] = int((b.groupby(slot)["slug"].nunique() >= MOST * len(g)).sum())
    return out


def account(trades: list[dict], paid: dict[str, float]) -> pd.DataFrame:
    t = pd.DataFrame(trades)
    if not len(t):
        return t
    t["settle"] = t["slug"].map(paid)
    t["pnl"] = [rule.pnl(r, r["settle"]) if pd.notna(r["settle"]) else np.nan for r in t.to_dict("records")]
    t["lost"] = t["pnl"] < 0
    t["evening"] = pd.to_datetime(t["end"], unit="s").dt.strftime("%d %b %H:%M")
    t["counted"] = t["end"] >= COUNTED_FROM
    return t


def by_evening(t: pd.DataFrame, ends: dict[float, int]) -> pd.DataFrame:
    """One row a settlement time: was it recorded, what was sold, what it made."""
    rows = []
    for end, n in sorted(ends.items()):
        g = t[t["end"] == end] if len(t) else t
        rows.append({"end": end, "evening": f"{datetime.fromtimestamp(end, timezone.utc):%d %b %H:%M}", "counted": end >= COUNTED_FROM, "btc_stretches": n, "recorded": n >= RECORDED,
                     "sales": len(g), "of_a_contract_or_more": int((g["qty"] >= 1).sum()) if len(g) else 0, "contracts": float(g["qty"].sum()) if len(g) else 0.0,
                     "tied_up": float(g["locked"].sum()) if len(g) else 0.0, "premium": float(g["premium"].sum()) if len(g) else 0.0,
                     "settled": bool(len(g) == 0 or g["settle"].notna().all()), "lost": int(g["lost"].sum()) if len(g) else 0,
                     "pnl": float(g["pnl"].sum()) if len(g) and g["settle"].notna().all() else (0.0 if len(g) == 0 else np.nan)})
    return pd.DataFrame(rows)


def by_ladder(t: pd.DataFrame) -> pd.DataFrame:
    """For each ladder: what was sold in it, and its largest sale, which is the most that ladder can lose."""
    if not len(t):
        return pd.DataFrame()
    g = t.groupby(["evening", "end", "coin", "horizon"]).agg(brackets=("slug", "size"), contracts=("qty", "sum"), premium=("premium", "sum"), tied_up=("locked", "sum"),
                                                           largest_sale=("locked", "max"), first_minutes_left=("left", lambda s: round(s.max() / 60.0)),
                                                           last_minutes_left=("left", lambda s: round(s.min() / 60.0)), nearest=("gap", "min"),
                                                           still_next=("still_next", lambda s: f"{int(s.fillna(False).sum())} of {int(s.notna().sum())}"),
                                                           lost=("lost", "sum"), pnl=("pnl", lambda s: s.sum(min_count=len(s)))).reset_index()
    return g.sort_values(["end", "coin", "horizon"]).drop(columns=["end"])


def verdict(ev: pd.DataFrame) -> str:
    rec = ev[ev["counted"] & ev["recorded"] & ev["settled"]] if len(ev) else ev
    if len(rec) < MIN_EVENINGS:
        return f"NOT YET JUDGED: {len(rec)} evenings recorded and settled since the rule was fixed, {MIN_EVENINGS} are asked for"
    mean, lost = float(rec["pnl"].mean()), int(rec["lost"].sum())
    ok = mean >= MIN_AN_EVENING and lost == 0
    return (f"{'PASSED' if ok else 'NOT PASSED'}: {len(rec)} evenings, ${mean:,.2f} an evening on average (at least ${MIN_AN_EVENING:,.0f} asked), "
            f"brackets sold that paid: {lost} (none allowed)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--state", default=str(ROOT / "state" / "us-ladder"))
    ap.add_argument("--reach", default=str(ROOT / "config" / "lasthours_reach.json"))
    ap.add_argument("--settle", action="store_true", help="ask the exchange for settlements and for the index levels the brake lacks")
    ap.add_argument("--out", default=str(ROOT / "reports" / "research"))
    args = ap.parse_args()
    state, out = Path(args.state), Path(args.out)
    reach, brake = rule.load(Path(args.reach))
    b, m, i = load(state)
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say("Test L3: selling far brackets while the bids are there (docs/11_crypto_us.md, section 13)")
    say(f"scored {datetime.now(timezone.utc):%d %B %Y, %H:%M UTC}. Paper sales against bids seen in the book. No order was placed.")
    if not len(b) or not len(m):
        say("Nothing has been recorded yet.")
        return 0
    m = m[(m["kind"] == "range") & m["horizon"].isin(rule.HORIZONS)]
    b = b[b["slug"].isin(m["slug"])]
    say(f"recorded: {len(b):,} readings of {b['slug'].nunique():,} brackets, from {datetime.fromtimestamp(b['ts'].min(), timezone.utc):%d %b %H:%M} to "
        f"{datetime.fromtimestamp(b['ts'].max(), timezone.utc):%d %b %H:%M} UTC")
    history = known_levels(state, i, m, args.settle)
    trades, fate = apply(b, m, i, reach, brake, history)
    now = datetime.now(timezone.utc).timestamp()
    paid = settlements(state, sorted({t["slug"] for t in trades if t["end"] + 120 < now}), args.settle)
    t_all = account(trades, paid)
    t_10k = account(rule.small_account(trades, money=MONEY), paid)
    ends = recorded(b, m)
    ev_all, ev_10k = by_evening(t_all, ends), by_evening(t_10k, ends)

    say()
    say("what became of each bracket followed (a bracket is counted once, by its sale or by how its last reading was judged)")
    counts = fate.groupby(["fate"]).size()
    for k in ORDER:
        if k in counts.index:
            say(f"   {k:<55} {counts[k]:>5}")

    for name, t, ev in (("L3-all (every sale the rule finds, 2,000 contracts a bracket at most)", t_all, ev_all),
                        (f"L3-10k (${MONEY:,.0f} to tie up at each settlement time)", t_10k, ev_10k)):
        say()
        say(name)
        say(ev.drop(columns=["end"]).round(2).to_string(index=False))
        lad = by_ladder(t)
        if len(lad):
            say("   by ladder (largest_sale is the most that ladder can lose; still_next: bids sold to that stood as large at the bracket's next reading)")
            say(lad.round({"contracts": 1, "premium": 2, "tied_up": 2, "largest_sale": 2, "nearest": 4, "pnl": 2}).to_string(index=False))

    say()
    say("Evenings before 13 November were looked at before the rule was fixed. They are shown and counted for nothing.")
    say("Verdict by the bar fixed in advance, for L3-10k: " + verdict(ev_10k))

    out.mkdir(parents=True, exist_ok=True)
    fate.to_csv(out / "lh_fate.csv", index=False)
    t_all.to_csv(out / "lh_trades.csv", index=False)
    t_10k.to_csv(out / "lh_trades_10k.csv", index=False)
    ev_all.to_csv(out / "lh_by_evening.csv", index=False)
    ev_10k.to_csv(out / "lh_by_evening_10k.csv", index=False)
    by_ladder(t_all).to_csv(out / "lh_ladders.csv", index=False)
    (out / "lh_summary.txt").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
