"""Score the live recordings of whole crypto ladders by the rule of test L2.

docs/11_crypto_us.md, section 12. A second copy of the recorder
(kht us-lasttick --state state/us-ladder --kinds range ...) wrote down the
books of every daily and weekly bracket, with sizes, through the five and
a half hours before they settled. This applies the rule to them: one paper
account of $10,000 that sells every bracket of a ladder at once when that
locks enough, and what it kept once the ladder settled.

A second account stands beside the judged one. It differs in one thing:
it takes the exchange's "mutually exclusive collateral return" as switched
on (docs/11, section 12, "What the exchange ties up for a ladder"). Once a
ladder is sold, that account has only its largest leg tied up, and the
rest of the money is free for the other ladders.

    python scripts/us_ladder_score.py [--state state/us-ladder] [--settle] [--out reports/research]

``--settle`` asks the exchange what each bracket settled at (public, no
key) and remembers the answers in <state>/settlements.csv.

Beside the account it describes each ladder's day: at every reading, how
many brackets had a bid and what a sale would have locked. That part is
described, not judged.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

from kht.trading import ladder_rule as rule  # noqa: E402

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
MIN_EVENINGS, MIN_SALES, MIN_AN_EVENING = 5, 4, 20.0      # the bar of docs/11, section 12
RECORDED = 120                                            # readings of the daily Bitcoin ladder with fresh books that make an evening count
MOST = 0.9                                                # a reading has fresh books if this share of the ladder's brackets were read in time
LOOKS = [300, 240, 180, 120, 60, 30, 16, 2]               # minutes before the end at which the day is described in the printed summary


def load(state: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Every run's readings and markets."""
    runs = sorted((state / "runs").glob("*")) if (state / "runs").exists() else []
    books = [pd.read_csv(r / "books.csv.gz") for r in runs if (r / "books.csv.gz").exists()]
    markets = [pd.read_csv(r / "markets.csv") for r in runs if (r / "markets.csv").exists()]
    b = pd.concat(books, ignore_index=True) if books else pd.DataFrame()
    m = pd.concat(markets, ignore_index=True) if markets else pd.DataFrame()
    if len(m):
        m = m.sort_values("first_seen").drop_duplicates("slug", keep="last")      # a market followed in two runs has the same terms in both
    return b, m


def ladders(markets: pd.DataFrame) -> list[dict]:
    """The ladders of the test: the brackets of one coin with the same length and the same end. In the order they are served."""
    out = []
    if not len(markets):
        return out
    m = markets[(markets["kind"] == "range") & markets["horizon"].isin(rule.HORIZONS) & markets["coin"].isin(rule.COINS)]
    for (end, coin, horizon), g in m.groupby(["end", "coin", "horizon"]):
        out.append({"end": float(end), "coin": coin, "horizon": horizon, "slugs": sorted(g["slug"]),
                    "name": f"{coin} {horizon} {datetime.fromtimestamp(float(end), timezone.utc):%d %b %H:%M}"})
    return sorted(out, key=lambda x: (x["end"], rule.COINS.index(x["coin"]), rule.HORIZONS.index(x["horizon"])))


class Books:
    """The last recorded book of a bracket at a given moment."""

    def __init__(self, books: pd.DataFrame):
        self.ts: dict[str, np.ndarray] = {}
        self.levels: dict[str, list] = {}
        if len(books):
            for slug, g in books.sort_values("ts").groupby("slug", sort=False):
                self.ts[slug] = g["ts"].to_numpy(dtype=float)
                self.levels[slug] = [rule.bids(r) for r in g.to_dict("records")]

    def at(self, slug: str, t: float):
        """The bids as last recorded by ``t``; None if that reading is too old, or there is none."""
        a = self.ts.get(slug)
        if a is None:
            return None
        k = int(np.searchsorted(a, t, side="right")) - 1
        return None if k < 0 or t - a[k] > rule.FRESH else self.levels[slug][k]


def account(found: list[dict], books: Books, money: float = rule.MONEY, collateral_return: bool = False) -> tuple[list[dict], pd.DataFrame]:
    """The rule on every ladder: its sale, if any, and a description of every reading.

    Without ``collateral_return`` every contract sold ties up $1 less its
    price until the ladder settles, and the ladders that settle together
    share the money. With it, the exchange's documented netting for a
    mutually exclusive event is taken as switched on: a sale still has to be
    opened with a dollar a contract, but once it stands only its largest
    leg is tied up. What that frees may be used for other ladders and not
    for the one it came from.
    """
    events = sorted((t, i) for i, lad in enumerate(found) for t in rule.readings(lad["end"]))
    order = {i: (rule.COINS.index(lad["coin"]), rule.HORIZONS.index(lad["horizon"])) for i, lad in enumerate(found)}
    events.sort(key=lambda e: (e[0], order[e[1]]))
    positions: dict[int, dict] = {}
    curve = []

    def usable(i: int, end: float) -> float:
        """The money ladder ``i`` may still open sales with."""
        mine = positions[i]["margin"] if i in positions else 0.0
        others = [p for j, p in positions.items() if j != i and p["end"] == end]
        if collateral_return:
            return money - mine - sum(p["pays_at_most"] for p in others)
        return money - mine - sum(p["margin"] for p in others)
    for t, i in events:
        lad = found[i]
        left = lad["end"] - t
        seen = {s: books.at(s, t) for s in lad["slugs"]}
        fresh = {s: lv for s, lv in seen.items() if lv is not None}
        with_bid = {s: lv for s, lv in fresh.items() if lv}
        free = rule.best(with_bid, money) if with_bid else None            # what an untouched account would lock: described, not judged
        curve.append({"ladder": lad["name"], "coin": lad["coin"], "horizon": lad["horizon"], "end": lad["end"], "ts": t, "minutes_left": round(left / 60.0, 1),
                      "brackets": len(lad["slugs"]), "fresh": len(fresh), "with_bid": len(with_bid),
                      "at_1c": sum(1 for lv in with_bid.values() if abs(lv[0][0] - 0.01) < 1e-9), "sum_best_bids": round(sum(lv[0][0] for lv in with_bid.values()), 4),
                      "locks_10": round(rule.sale(with_bid, 10.0)["locks"], 2) if with_bid else np.nan,
                      "locks_100": round(rule.sale(with_bid, 100.0)["locks"], 2) if with_bid else np.nan,
                      "best_q": free["q"] if free else np.nan, "best_locks": round(free["locks"], 2) if free else np.nan,
                      "best_margin": round(free["margin"], 2) if free else np.nan})
        if not with_bid:
            continue
        have = usable(i, lad["end"])
        pos = positions.get(i)
        if pos is None:
            s = rule.decide(with_bid, left, have)
            if s is not None:
                positions[i] = {**s, "ladder": lad["name"], "coin": lad["coin"], "horizon": lad["horizon"], "end": lad["end"], "ts": t, "left": left,
                                "brackets": len(lad["slugs"]), "first_legs": len(s["legs"]), "locked_at_sale": s["locks"], "added": 0, "slugs": lad["slugs"]}
        else:
            legs = rule.top_up(with_bid, pos, have)
            if legs:
                rule.add(pos, legs)
                pos["added"] += len(legs)
    return [positions[i] for i in sorted(positions)], pd.DataFrame(curve)


def settlements(state: Path, slugs: list[str], look_up: bool) -> dict[str, float]:
    """What "Yes" paid in each bracket, as far as known: remembered in <state>/settlements.csv, asked for with ``look_up``."""
    path = state / "settlements.csv"
    known = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["slug", "settle"])
    have = {s: float(v) for s, v in known.dropna(subset=["settle"]).itertuples(index=False)}
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


def evenings(found: list[dict], curve: pd.DataFrame, positions: list[dict], paid: dict[str, float]) -> pd.DataFrame:
    """One row a settlement time: was it recorded, was anything sold, what was kept."""
    rows = []
    for end in sorted({lad["end"] for lad in found}):
        mine = [lad for lad in found if lad["end"] == end]
        # the Bitcoin ladder that settles then: the daily one, and on a Friday, when there is none, the weekly one
        c = curve[(curve["end"] == end) & (curve["coin"] == "btc")]
        c = c[c["horizon"] == ("daily" if (c["horizon"] == "daily").any() else "weekly")]
        good = int((c["fresh"] >= MOST * c["brackets"]).sum()) if len(c) else 0
        pos = [p for p in positions if p["end"] == end]
        settled = all(all(s in paid for s in lad["slugs"]) for lad in mine)
        odd = [lad["name"] for lad in mine if all(s in paid for s in lad["slugs"]) and abs(sum(paid[s] for s in lad["slugs"]) - 1.0) > 1e-9]
        kept = sum(rule.result(p, paid) for p in pos) if settled else np.nan
        rows.append({"end": end, "evening": f"{datetime.fromtimestamp(end, timezone.utc):%d %b %H:%M}", "ladders": len(mine), "btc_readings": good,
                     "recorded": good >= RECORDED, "sales": len(pos), "locked": sum(p["locks"] for p in pos), "margin": sum(p["margin"] for p in pos),
                     "settled": settled, "kept": kept, "ladders_not_paying_one": ", ".join(odd)})
    return pd.DataFrame(rows)


def verdict(ev: pd.DataFrame, positions: list[dict], paid: dict[str, float]) -> str:
    rec = ev[ev["recorded"] & ev["settled"]] if len(ev) else ev
    if len(rec) < MIN_EVENINGS:
        return f"NOT YET JUDGED: {len(rec)} evenings recorded and settled, {MIN_EVENINGS} are asked for"
    with_sale, mean = int((rec["sales"] > 0).sum()), float(rec["kept"].fillna(0.0).mean())
    ends = set(rec["end"])
    lost = [p["ladder"] for p in positions if p["end"] in ends and rule.result(p, paid) < -1e-9]
    ok = with_sale >= MIN_SALES and mean >= MIN_AN_EVENING and not lost
    return (f"{'PASSED' if ok else 'NOT PASSED'}: {len(rec)} evenings, a sale on {with_sale} (at least {MIN_SALES} asked), ${mean:,.2f} kept an evening on average "
            f"(at least ${MIN_AN_EVENING:,.0f} asked), ladders with a loss: {', '.join(lost) or 'none'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--state", default=str(ROOT / "state" / "us-ladder"))
    ap.add_argument("--settle", action="store_true", help="ask the exchange what each bracket settled at")
    ap.add_argument("--out", default=str(ROOT / "reports" / "research"))
    args = ap.parse_args()
    state, out = Path(args.state), Path(args.out)
    b, m = load(state)
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say("Test L2: selling every bracket of a ladder at once (docs/11_crypto_us.md, section 12)")
    say(f"scored {datetime.now(timezone.utc):%d %B %Y, %H:%M UTC}. A paper account. No order was placed.")
    if not len(b) or not len(m):
        say("Nothing has been recorded yet.")
        return 0
    found = ladders(m)
    say(f"recorded: {len(b):,} readings of {b['slug'].nunique():,} brackets in {len(found)} ladders, from "
        f"{datetime.fromtimestamp(b['ts'].min(), timezone.utc):%d %b %H:%M} to {datetime.fromtimestamp(b['ts'].max(), timezone.utc):%d %b %H:%M} UTC")
    recorded = Books(b)
    positions, curve = account(found, recorded)
    netted, _ = account(found, recorded, collateral_return=True)
    now = datetime.now(timezone.utc).timestamp()
    ended = [s for lad in found if lad["end"] + 120 < now for s in lad["slugs"]]
    paid = settlements(state, ended, args.settle)
    ev = evenings(found, curve, positions, paid)
    ev_netted = evenings(found, curve, netted, paid)

    def show(pos: list[dict]) -> None:
        if not pos:
            say("  no sale: at no reading did a sale lock what the rule asks ($25, or $10 in the last half hour)")
            return
        rows = []
        for p in pos:
            done = all(s in paid for s in p["slugs"])
            rows.append({"ladder": p["ladder"], "sold at (UTC)": f"{datetime.fromtimestamp(p['ts'], timezone.utc):%H:%M}", "minutes left": round(p["left"] / 60.0),
                         "size": p["q"], "brackets sold": len(p["legs"]), "of": p["brackets"], "added later": p["added"], "money in": round(p["money"], 2),
                         "fees": round(p["fees"], 2), "pays at most": p["pays_at_most"], "locked": round(p["locks"], 2), "money to open it": round(p["margin"], 2),
                         "kept": round(rule.result(p, paid), 2) if done else np.nan})
        say(pd.DataFrame(rows).to_string(index=False))

    say()
    say("The judged account: $10,000 for each settlement time, a dollar less its price tied up for every contract sold")
    show(positions)
    say()
    say("By settlement time:")
    say(ev.drop(columns=["end"]).round(2).to_string(index=False))
    if len(ev) and ev["ladders_not_paying_one"].astype(bool).any():
        say("  A ladder in which not exactly one bracket paid is not what the rule takes a ladder to be. Look at it before anything else.")
    say()
    say("Verdict by the bar fixed in advance: " + verdict(ev, positions, paid))

    say()
    say("The second account: the same rule and the same $10,000, with the exchange's collateral return taken as switched on,")
    say("so that a ladder once sold ties up only its largest leg and the other ladders can use the rest")
    show(netted)
    say()
    say("By settlement time:")
    say(ev_netted.drop(columns=["end"]).round(2).to_string(index=False))
    say()
    say("The same bar read for the second account: " + verdict(ev_netted, netted, paid))

    say()
    say("The day of each ladder, described and not judged: what an untouched $10,000 would have locked at a reading")
    look = curve[curve["minutes_left"].isin([float(x) for x in LOOKS])]
    if len(look):
        t = look.assign(cell=lambda d: d.apply(lambda r: "-" if r["fresh"] == 0 else f"{r['at_1c']:.0f} at 1c, {'' if pd.isna(r['best_locks']) else format(r['best_locks'], '+.0f')}", axis=1))
        say(t.pivot(index="ladder", columns="minutes_left", values="cell").reindex(columns=[float(x) for x in LOOKS]).rename(columns=lambda c: f"{c:.0f} min left").to_string())
    top = curve.dropna(subset=["best_locks"])
    if len(top):
        peak = top.loc[top.groupby("ladder")["best_locks"].idxmax(), ["ladder", "minutes_left", "with_bid", "at_1c", "sum_best_bids", "best_q", "best_locks", "best_margin"]]
        say()
        say("Each ladder's best reading:")
        say(peak.rename(columns={"minutes_left": "minutes left", "with_bid": "brackets with a bid", "at_1c": "at 1c", "sum_best_bids": "sum of best bids",
                                 "best_q": "size", "best_locks": "locked", "best_margin": "money tied up"}).to_string(index=False))

    out.mkdir(parents=True, exist_ok=True)
    curve.to_csv(out / "ld_curve.csv", index=False)
    ev.to_csv(out / "ld_evenings.csv", index=False)
    ev_netted.to_csv(out / "ld_evenings_return.csv", index=False)
    for name, pos in (("", positions), ("_return", netted)):
        legs = [{"ladder": p["ladder"], "slug": s, **leg, "paid": paid.get(s, np.nan)} for p in pos for s, leg in p["legs"].items()]
        pd.DataFrame(legs).to_csv(out / f"ld_legs{name}.csv", index=False)
        pd.DataFrame([{k: v for k, v in p.items() if k not in ("legs", "slugs")} for p in pos]).to_csv(out / f"ld_sales{name}.csv", index=False)
    (out / "ld_summary.txt").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
