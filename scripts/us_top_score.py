"""Test G1 on what ``kht us-top`` recorded: small orders at the best prices of single-market reward programmes.

docs/13_round_six.md, section 4. The rule is ``src/kht/trading/top_rule.py``.
A paper account: no order was placed and no reward was paid to anyone.

    python scripts/us_top_score.py --settle     # look up how finished markets settled (public data), then score

For each market read, and each order size, it walks the readings in order:
between two readings the orders resting since the first may be traded
against; at each reading the rule says what rests until the next. The reward
is the published pool times our share of the score over the seconds the book
qualified, divided by the seconds the market was open, as the filed rules
divide it.

Writes reports/research/tp_*.csv and tp_summary.txt.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kht.api.polymarket_us import PolymarketUS  # noqa: E402
from kht.trading import top_rule as rule  # noqa: E402
from kht.trading.us_top import decode, wanted  # noqa: E402

OUT = ROOT / "reports" / "research"
JUDGED_PROGRAMMES = ("metals_gold_updown_1d", "metals_silver_updown_1d")
MIN_DAYS, MIN_DATES, BAR_T, BAR_NET = 10, 6, 3.0, 20.0
Q1_BAR_NET, Q1_FILLS_AT_MOST, Q1_PAID_DAYS = 20.0, 0.25, 4       # test Q1: dollars a market-day, fills as a share of the reward, market-days with a reward
WHOLE_START = 900.0       # a market-day is recorded whole if its first open reading came within this long of the start of its window,
WHOLE_COVER = 0.85        # readings cover this share of the half minutes it was open,
WHOLE_END = 180.0         # and it was seen to close within this long of its last open reading
MINIMUM = 1.0             # a reward under a dollar for a market and a day is not paid
CAPS = (100, 50, 10)
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)


def load(state: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    books = [pd.read_csv(p) for p in sorted(state.glob("runs/*/books.csv.gz"))]
    markets = [pd.read_csv(p) for p in sorted(state.glob("runs/*/markets.csv"))]
    b = pd.concat([x for x in books if len(x)], ignore_index=True) if any(len(x) for x in books) else pd.DataFrame()
    m = pd.concat([x for x in markets if len(x)], ignore_index=True) if any(len(x) for x in markets) else pd.DataFrame()
    if len(b):
        b = b.sort_values(["slug", "ts"]).drop_duplicates(["slug", "ts"]).reset_index(drop=True)
    if len(m):
        m = m.sort_values("first_seen").groupby("slug", as_index=False).last()      # the fullest description of each market
    return b, m


def settlements(state: Path, slugs: list[str], look_up: bool, us: PolymarketUS | None = None) -> pd.Series:
    path = state / "settlements.csv"
    known = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["slug", "settle", "asof"])
    have = set(known["slug"])
    if look_up:
        us = us or PolymarketUS()
        rows = []
        for slug in slugs:
            if slug in have:
                continue
            value = us.settlement(slug)
            if value is not None:
                rows.append({"slug": slug, "settle": value, "asof": int(time.time())})
        if rows:
            known = pd.concat([known, pd.DataFrame(rows)], ignore_index=True)
            known.to_csv(path, index=False)
    return known.drop_duplicates("slug", keep="last").set_index("slug")["settle"].astype(float)


def simulate(rows: list[dict], terms: dict, size: float) -> dict:
    """One market, one order size: the account's fills, what it holds at the end, and its share of the score over time."""
    target, discount = float(terms["target"]), float(terms["discount"])
    max_spread = None if pd.isna(terms.get("max_spread")) else float(terms["max_spread"])
    pos = cash = credit = qualify_s = rest_s = 0.0
    bought = sold = notional = 0.0
    n_fills = 0
    q = None
    prev = None
    trades = []
    for i, r in enumerate(rows):
        bids, asks = decode(r.get("bids")), decode(r.get("asks"))
        if q is not None and prev is not None and (q["bid_px"] is not None or q["ask_px"] is not None):
            bf, af = rule.fills(q, prev, r, bids, asks)
            if bf > rule.EPS:
                pos += bf; cash -= bf * q["bid_px"]; bought += bf; notional += bf * q["bid_px"]; n_fills += 1
                trades.append({"ts": r["ts"], "side": "bid", "px": q["bid_px"], "qty": bf})
            if af > rule.EPS:
                pos -= af; cash += af * q["ask_px"]; sold += af; notional += af * q["ask_px"]; n_fills += 1
                trades.append({"ts": r["ts"], "side": "ask", "px": q["ask_px"], "qty": af})
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        dt = min(float(nxt["ts"]) - float(r["ts"]), rule.MAX_CREDIT) if nxt is not None else 0.0
        q = rule.quotes(bids, asks, pos, size, target, max_spread, str(r.get("state")))
        if str(r.get("state")) == "OPEN" and rule.qualifies(bids, asks, target, max_spread):
            qualify_s += dt
        if q["bid_px"] is not None or q["ask_px"] is not None:
            sb, sa = rule.shares(bids, asks, q, target, discount, max_spread)
            credit += dt * (sb + sa) / 2.0
            rest_s += dt
        prev = r
    return {"pos": pos, "cash": cash, "credit": credit, "qualify_s": qualify_s, "rest_s": rest_s, "bought": bought, "sold": sold, "notional": notional,
            "fills": n_fills, "trades": trades}


def simulate_last_tick(rows: list[dict], terms: dict) -> dict:
    """One market under the rule of test Q1: the target size at the last tick of a side nobody stands on."""
    target, discount = float(terms["target"]), float(terms["discount"])
    max_spread = None if pd.isna(terms.get("max_spread")) else float(terms["max_spread"])
    bought = sold = cash = credit = rest_s = 0.0
    n_fills = 0
    q = prev = None
    for i, r in enumerate(rows):
        bids, asks = decode(r.get("bids")), decode(r.get("asks"))
        if q is not None and prev is not None and (q["bid_px"] is not None or q["ask_px"] is not None):
            bf, af = rule.fills(q, prev, r, bids, asks)
            if bf > rule.EPS:
                bought += bf; cash -= bf * q["bid_px"]; n_fills += 1
            if af > rule.EPS:
                sold += af; cash += af * q["ask_px"]; n_fills += 1
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        dt = min(float(nxt["ts"]) - float(r["ts"]), rule.MAX_CREDIT) if nxt is not None else 0.0
        q = rule.last_tick(bids, asks, bought, sold, target, max_spread, str(r.get("state")))
        if q["bid_px"] is not None or q["ask_px"] is not None:
            sb, sa = rule.shares(bids, asks, q, target, discount, max_spread)
            credit += dt * (sb + sa) / 2.0
            rest_s += dt
        prev = r
    return {"bought": bought, "sold": sold, "cash": cash, "credit": credit, "rest_s": rest_s, "fills": n_fills}


def last_tick_day(slug: str, rows: list[dict], terms: dict, settle: float | None) -> dict | None:
    """One market under test Q1: reward by the formula, what its fills made, and whether the day was recorded whole."""
    sized = market_day(slug, rows, terms, settle)
    if not sized:
        return None
    frame = sized[0]                                                     # the same day, the same test of wholeness, the same length
    s = simulate_last_tick(rows, terms)
    open_s = frame["open_hours"] * 3600.0
    reward = float(terms["pool"]) * s["credit"] / open_s
    paid = reward if reward >= MINIMUM else 0.0
    pnl = (s["cash"] + (s["bought"] - s["sold"]) * settle) if settle is not None else np.nan
    return {"slug": slug, "program": frame["program"], "day": frame["day"], "whole": frame["whole"], "open_hours": frame["open_hours"], "cover": frame["cover"],
            "qualifies": frame["qualifies"], "resting": s["rest_s"] / open_s, "reward_formula": reward, "reward_paid": paid, "fills": s["fills"],
            "bought": s["bought"], "sold": s["sold"], "settle": settle if settle is not None else np.nan, "pnl_fills": pnl,
            "net": paid + pnl if settle is not None else np.nan, "pool": float(terms["pool"]), "target": float(terms["target"])}


def verdict_last_tick(days: pd.DataFrame) -> str:
    """The bar of docs/13, section 4b, read on gold and silver together."""
    if not len(days):
        return "NOT YET JUDGED: nothing recorded"
    j = days[days["program"].isin(JUDGED_PROGRAMMES) & days["whole"] & days["net"].notna()]
    n, dates = len(j), j["day"].nunique()
    if n < MIN_DAYS or dates < MIN_DATES:
        return f"NOT YET JUDGED: {n} market-days recorded whole and settled on {dates} dates; {MIN_DAYS} on {MIN_DATES} are asked for"
    mean, reward, cost, paid_days = j["net"].mean(), j["reward_paid"].sum(), -j["pnl_fills"].clip(upper=0).sum(), int((j["reward_paid"] >= MINIMUM).sum())
    ok = mean >= Q1_BAR_NET and cost <= Q1_FILLS_AT_MOST * reward and paid_days >= Q1_PAID_DAYS
    return (f"{'PASSES' if ok else 'DOES NOT PASS'}: {n} market-days on {dates} dates, net ${mean:,.2f} a market-day on average (at least ${Q1_BAR_NET:g} asked); "
            f"fills cost ${cost:,.2f} against ${reward:,.2f} of reward (at most {Q1_FILLS_AT_MOST:.0%} asked); a reward on {paid_days} market-days (at least {Q1_PAID_DAYS} asked)")


def market_day(slug: str, rows: list[dict], terms: dict, settle: float | None) -> list[dict]:
    """Every order size on one market: reward by the formula, what the fills made, and whether the day was recorded whole."""
    open_rows = [r for r in rows if str(r.get("state")) == "OPEN"]
    if not open_rows:
        return []
    first, last = float(open_rows[0]["ts"]), float(open_rows[-1]["ts"])
    after = [r for r in rows if float(r["ts"]) > last]
    closed_seen = bool(after) and float(after[0]["ts"]) - last <= WHOLE_END
    window_start = terms.get("window_start")
    window_start = float(window_start) if window_start is not None and not pd.isna(window_start) else None
    open_s = max(last - first, 1.0) + 30.0
    cover = len(open_rows) * 30.0 / open_s
    whole = bool(closed_seen and cover >= WHOLE_COVER and window_start is not None and first - window_start <= WHOLE_START)
    if not whole:
        # a part of a day must not be paid as if it were the whole of one: it is divided by the length of the market's window
        window_end = terms.get("window_end")
        nominal = float(window_end) - window_start if window_start is not None and window_end is not None and not pd.isna(window_end) else 82_800.0
        open_s = max(open_s, nominal)
        cover = len(open_rows) * 30.0 / open_s
    program = wanted(str(terms.get("program") or ""), JUDGED_PROGRAMMES + ("crypto_btc_updown_1d", "crypto_alt_updown_1d")) or str(terms.get("program") or "")
    out = []
    for size in rule.SIZES:
        s = simulate(rows, terms, size)
        reward = float(terms["pool"]) * s["credit"] / open_s
        paid = reward if reward >= MINIMUM else 0.0
        pnl = (s["cash"] + s["pos"] * settle) if settle is not None else np.nan
        row = {"slug": slug, "program": program, "day": pd.Timestamp(last, unit="s", tz="UTC").strftime("%Y-%m-%d"), "size": size, "whole": whole,
               "first": first, "last": last, "open_hours": open_s / 3600.0, "cover": cover, "qualifies": s["qualify_s"] / open_s, "resting": s["rest_s"] / open_s,
               "share": s["credit"] / s["rest_s"] if s["rest_s"] > 0 else 0.0, "reward_formula": reward, "reward_paid": paid, "fills": s["fills"],
               "bought": s["bought"], "sold": s["sold"], "notional": s["notional"], "held_at_end": s["pos"], "settle": settle if settle is not None else np.nan,
               "pnl_fills": pnl, "net": paid + pnl if settle is not None else np.nan, "pool": float(terms["pool"])}
        for pct in CAPS:
            capped = min(reward, pct / 100.0 * s["notional"])
            row[f"reward_cap_{pct}"] = capped if capped >= MINIMUM else 0.0
        out.append(row)
    return out


def verdict(days: pd.DataFrame) -> str:
    """The bar of docs/13, section 4, read on the judged account."""
    j = days[days["program"].isin(JUDGED_PROGRAMMES) & (days["size"] == rule.JUDGED) & days["whole"] & days["net"].notna()]
    n, dates = len(j), j["day"].nunique()
    if n < MIN_DAYS or dates < MIN_DATES:
        return f"NOT YET JUDGED: {n} market-days recorded whole and settled on {dates} dates; {MIN_DAYS} on {MIN_DATES} are asked for"
    mean, sd = j["net"].mean(), j["net"].std(ddof=1)
    t = mean / (sd / np.sqrt(n)) if sd > 0 else float("inf") if mean > 0 else float("-inf")
    ok = mean >= BAR_NET and t >= BAR_T
    return (f"{'PASSES' if ok else 'DOES NOT PASS'}: {n} market-days on {dates} dates, net ${mean:,.2f} a market-day on average "
            f"(at least ${BAR_NET:g} asked), t {t:.2f} (at least {BAR_T:g} asked)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=str(ROOT / "state" / "us-top"))
    ap.add_argument("--settle", action="store_true", help="look up how finished markets settled (public data)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    state, out = Path(args.state), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    b, m = load(state)
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say("Test G1: small orders at the best prices of single-market reward programmes (docs/13_round_six.md, section 4)")
    say(f"scored {pd.Timestamp.now(tz='UTC'):%d %B %Y, %H:%M} UTC. A paper account. No order was placed and no reward was paid to anyone.")
    if not len(b):
        say("nothing recorded yet")
        (out / "tp_summary.txt").write_text("\n".join(lines) + "\n")
        return 0
    say(f"recorded: {len(b):,} readings of {b['slug'].nunique()} markets, from {pd.Timestamp(b['ts'].min(), unit='s'):%d %b %H:%M} to "
        f"{pd.Timestamp(b['ts'].max(), unit='s'):%d %b %H:%M} UTC")
    closed = [s for s, g in b.groupby("slug") if (g["state"] != "OPEN").any()]
    settle = settlements(state, closed, args.settle)
    terms = m.set_index("slug").to_dict("index") if len(m) else {}
    rows, ticks = [], []
    for slug, g in b.groupby("slug"):
        if slug not in terms or pd.isna(terms[slug].get("pool")) or pd.isna(terms[slug].get("target")):
            continue
        y = float(settle[slug]) if slug in settle.index else None
        recs = g.to_dict("records")
        rows += market_day(slug, recs, terms[slug], y)
        lt = last_tick_day(slug, recs, terms[slug], y)
        if lt is not None:
            ticks.append(lt)
    days = pd.DataFrame(rows)
    last_ticks = pd.DataFrame(ticks)
    if not len(days):
        say("no market with known terms yet")
        (out / "tp_summary.txt").write_text("\n".join(lines) + "\n")
        return 0
    days.round(4).to_csv(out / "tp_market_days.csv", index=False)
    show = ["day", "program", "whole", "open_hours", "cover", "qualifies", "resting", "share", "reward_paid", "fills", "bought", "sold", "held_at_end", "settle", "pnl_fills", "net"]
    j = days[days["size"] == rule.JUDGED].sort_values(["program", "day"])
    say()
    say(f"each market-day, {rule.JUDGED} contracts a side (qualifies: share of the time the book was paid; resting: share of the time our orders rested; "
        "share: our part of the score while resting)")
    say(j[show].round(3).to_string(index=False))
    say()
    say("by programme and order size, market-days recorded whole and settled")
    k = days[days["whole"] & days["net"].notna()]
    if len(k):
        g = k.groupby(["program", "size"]).agg(days=("net", "size"), reward=("reward_paid", "sum"), fills=("fills", "sum"), contracts=("bought", lambda s: s.sum() + k.loc[s.index, "sold"].sum()),
                                               pnl_fills=("pnl_fills", "sum"), net=("net", "sum"), a_day=("net", "mean"), worst=("net", "min"),
                                               t=("net", lambda s: s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if len(s) > 1 and s.std(ddof=1) > 0 else np.nan),
                                               **{f"cap_{p}": (f"reward_cap_{p}", "sum") for p in CAPS}).reset_index()
        g.round(2).to_csv(out / "tp_by_programme.csv", index=False)
        say(g.round(2).to_string(index=False))
    else:
        say("   none yet")
    say()
    say("Verdict by the bar fixed in advance (gold and silver together, 100 contracts a side): " + verdict(days))

    # ---- test Q1: the target size at the last tick of a side nobody stands on (docs/13, section 4b)
    say()
    say("Test Q1: the target size at the last tick of a side nobody is standing on (docs/13_round_six.md, section 4b)")
    if len(last_ticks):
        last_ticks.round(4).to_csv(out / "tp_last_tick_days.csv", index=False)
        show = ["day", "program", "whole", "open_hours", "qualifies", "resting", "reward_paid", "fills", "bought", "sold", "settle", "pnl_fills", "net"]
        say("each market-day (qualifies: share of the time the book was paid as it was; resting: share of the time our order rested and made it paid)")
        say(last_ticks.sort_values(["program", "day"])[show].round(3).to_string(index=False))
        k = last_ticks[last_ticks["whole"] & last_ticks["net"].notna()]
        if len(k):
            g = k.groupby("program").agg(days=("net", "size"), with_reward=("reward_paid", lambda s: int((s >= MINIMUM).sum())), reward=("reward_paid", "sum"),
                                         fills=("fills", "sum"), bought=("bought", "sum"), sold=("sold", "sum"), pnl_fills=("pnl_fills", "sum"), net=("net", "sum"),
                                         a_day=("net", "mean"), worst=("net", "min")).reset_index()
            g.round(2).to_csv(out / "tp_last_tick_by_programme.csv", index=False)
            say()
            say("by programme, market-days recorded whole and settled")
            say(g.round(2).to_string(index=False))
    say()
    say("Verdict by the bar fixed in advance (gold and silver together): " + verdict_last_tick(last_ticks))
    (out / "tp_summary.txt").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
