"""Test K1 on what ``kht us-top --programmes kpic`` recorded: small orders at the best prices of the earnings markets.

docs/13_round_six.md, section 4c. A paper account: no order was placed and
no reward was paid to anyone.

    python scripts/us_kpi_score.py --settle     # look up how finished markets settled (public data), then score

The exchange lists a few markets on each company's quarterly figures, two or
three days before the company reports, and pays a reward pool for each
event and day. The rule is the rule of test G1 (``src/kht/trading/top_rule.py``),
and two things are added because these markets end in a jump at a time known
in advance:

    nothing rests from the cut-off on: 15:00 US Eastern on the day of the
    report when the company reports after the market close, and midnight US
    Eastern at the start of that day otherwise;

    whatever the account holds at the cut-off is sold at the best bid as
    read (or bought back at the best offer), down the book as far as it
    takes, and pays the fee a buyer or seller who takes a price pays.

One account is judged: the events that are one market, 100 contracts a side,
and only events listed from 18:00 UTC on 18 November 2026.

Writes reports/research/kp_*.csv and kp_summary.txt.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kht.api.polymarket_us import taker_fee_per_share  # noqa: E402
from kht.trading import top_rule as rule  # noqa: E402
from kht.trading.us_top import decode  # noqa: E402

_spec = importlib.util.spec_from_file_location("us_top_score", Path(__file__).resolve().parent / "us_top_score.py")
top = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(top)

OUT = ROOT / "reports" / "research"
EASTERN = ZoneInfo("America/New_York")
EVENT = re.compile(r"^kpic-(?P<event>.+?-(?P<date>\d{4}-\d{2}-\d{2}))-(?P<leg>.+)$")
AFTER_CLOSE_CUT = 15              # o'clock, US Eastern, on the day of the report, for a company that reports after the market close
DAY = 86_400.0
MINIMUM = 1.0                     # a reward under a dollar for a market and a day is not paid
MIN_EVENTS, MIN_DATES, BAR_NET, BAR_T = 12, 5, 5.0, 3.0
COUNTED_FROM = 1_795_024_800.0    # 18 November 2026, 18:00 UTC: only events listed from here on count; the earlier ones were seen before the rule was fixed
WHOLE_START = 6 * 3600.0          # an event is recorded whole if its first reading came within this long of its listing,
WHOLE_COVER = 0.85                # readings cover this share of the half minutes from there to the cut-off,
WHOLE_END = 600.0                 # and there is a reading within this long after the cut-off, to close what is held
CAPS = (100, 50, 10)
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)


def event_of(slug: str) -> tuple[str, str] | None:
    """The event a market belongs to and the day its company reports, both read from the market's name."""
    m = EVENT.match(slug)
    return (m.group("event"), m.group("date")) if m else None


def cutoff(date: str, reports: object) -> float:
    """The moment from which nothing rests: 15:00 Eastern on the day of the report if it comes after the close, else that day's first minute."""
    y, mo, d = (int(x) for x in date.split("-"))
    hour = AFTER_CLOSE_CUT if str(reports) == "after" else 0
    return datetime(y, mo, d, hour, 0, tzinfo=EASTERN).timestamp()


def close_out(pos: float, bids: list[tuple[float, float]], asks: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    """Sell what is held to the bids as read, or buy back what is owed from the offers. Returns cash, fee, contracts closed and their value traded."""
    cash = fee = done = notional = 0.0
    left = abs(pos)
    for px, qty in (bids if pos > 0 else asks):
        if left <= rule.EPS:
            break
        take = min(left, qty)
        cash += take * px if pos > 0 else -take * px
        fee += take * taker_fee_per_share(px)
        notional += take * px
        done += take
        left -= take
    return cash, fee, done, notional


def simulate(rows: list[dict], terms: dict, size: float, cut: float) -> dict:
    """One market, one order size: fills until the cut-off, the reward by the day, and what was held closed at the cut-off."""
    target, discount = float(terms["target"]), float(terms["discount"])
    max_spread = None if pd.isna(terms.get("max_spread")) else float(terms["max_spread"])
    pos = cash = fees = rest_s = qualify_s = seen_s = bought = sold = notional = 0.0
    n_fills = 0
    credit: dict[str, float] = {}
    q = prev = None
    closed_at = None
    left_open = 0.0
    for i, r in enumerate(rows):
        ts = float(r["ts"])
        bids, asks = decode(r.get("bids")), decode(r.get("asks"))
        if q is not None and prev is not None and (q["bid_px"] is not None or q["ask_px"] is not None):
            bf, af = rule.fills(q, prev, r, bids, asks)
            if bf > rule.EPS:
                pos += bf; cash -= bf * q["bid_px"]; bought += bf; notional += bf * q["bid_px"]; n_fills += 1
            if af > rule.EPS:
                pos -= af; cash += af * q["ask_px"]; sold += af; notional += af * q["ask_px"]; n_fills += 1
        if ts >= cut:                                   # the cut-off: nothing rests any more, and what is held is closed at the prices read
            if abs(pos) > rule.EPS and str(r.get("state")) == "OPEN":
                got, fee, done, traded = close_out(pos, bids, asks)
                cash += got; fees += fee; notional += traded
                pos -= done if pos > 0 else -done
            closed_at, left_open = ts, pos
            break
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        dt = min(float(nxt["ts"]) - ts, rule.MAX_CREDIT, max(cut - ts, 0.0)) if nxt is not None else 0.0
        seen_s += dt
        q = rule.quotes(bids, asks, pos, size, target, max_spread, str(r.get("state")))
        if str(r.get("state")) == "OPEN" and rule.qualifies(bids, asks, target, max_spread):
            qualify_s += dt
        if q["bid_px"] is not None or q["ask_px"] is not None:
            sb, sa = rule.shares(bids, asks, q, target, discount, max_spread)
            day = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")
            credit[day] = credit.get(day, 0.0) + dt * (sb + sa) / 2.0
            rest_s += dt
        prev = r
    return {"pos": pos, "cash": cash, "fees": fees, "credit": credit, "rest_s": rest_s, "qualify_s": qualify_s, "seen_s": seen_s, "bought": bought, "sold": sold,
            "notional": notional, "fills": n_fills, "closed_at": closed_at, "left_open": left_open if closed_at is not None else pos}


def event_rows(slug: str, rows: list[dict], terms: dict, settle: float | None, in_event: int, now: float) -> list[dict]:
    """Every order size on one market: the reward day by day, what the fills and the closing made, and whether it was recorded whole."""
    ev = event_of(slug)
    if ev is None or not rows:
        return []
    event, date = ev
    cut = cutoff(date, terms.get("reports"))
    first = float(rows[0]["ts"])
    before = [r for r in rows if float(r["ts"]) < cut]
    listed = terms.get("listed")
    listed = float(listed) if listed is not None and not pd.isna(listed) else None
    span = max(min(cut, float(rows[-1]["ts"])) - first, 1.0)
    cover = len(before) * 30.0 / (span + 30.0)
    after = [r for r in rows if float(r["ts"]) >= cut]
    saw_cut = bool(after) and float(after[0]["ts"]) - cut <= WHOLE_END
    whole = bool(listed is not None and listed >= COUNTED_FROM and first - listed <= WHOLE_START and cover >= WHOLE_COVER and saw_cut and first < cut)
    pool = float(terms["pool"]) / max(in_event, 1)        # for an event of several markets the pool is divided evenly: an assumption, and only described
    out = []
    for size in rule.SIZES:
        s = simulate(rows, terms, size, cut)
        by_day = {d: pool * c / DAY for d, c in s["credit"].items()}
        reward = sum(by_day.values())
        paid = sum(v for v in by_day.values() if v >= MINIMUM)
        held = s["left_open"]
        over = now >= cut and (saw_cut or settle is not None)
        if not over:
            pnl = np.nan
        elif abs(held) > rule.EPS:                         # what could not be closed is held to the result
            pnl = s["cash"] - s["fees"] + held * settle if settle is not None else np.nan
        else:
            pnl = s["cash"] - s["fees"]
        row = {"slug": slug, "event": event, "report_date": date, "reports": terms.get("reports") if isinstance(terms.get("reports"), str) else "", "in_event": in_event,
               "size": size, "whole": whole, "first": first, "cut": cut, "hours": s["seen_s"] / 3600.0, "cover": cover, "qualifies": s["qualify_s"] / max(s["seen_s"], 1.0),
               "resting": s["rest_s"] / max(s["seen_s"], 1.0), "share": sum(s["credit"].values()) / s["rest_s"] if s["rest_s"] > 0 else 0.0,
               "reward_formula": reward, "reward_paid": paid, "fills": s["fills"], "bought": s["bought"], "sold": s["sold"], "notional": s["notional"], "fees": s["fees"],
               "held_after_cut": held, "settle": settle if settle is not None else np.nan, "pnl_fills": pnl, "net": paid + pnl if not pd.isna(pnl) else np.nan, "pool": pool}
        for pct in CAPS:                                   # described: a cap at a share of what the account itself traded, the closing trade included
            capped = min(paid, pct / 100.0 * s["notional"])
            row[f"reward_cap_{pct}"] = capped if capped >= MINIMUM else 0.0
        out.append(row)
    return out


def verdict(events: pd.DataFrame) -> str:
    """The bar of docs/13, section 4c, read on the judged account."""
    if not len(events):
        return "NOT YET JUDGED: nothing recorded"
    j = events[(events["in_event"] == 1) & (events["size"] == rule.JUDGED) & events["whole"] & events["net"].notna()]
    n, dates = len(j), j["report_date"].nunique()
    if n < MIN_EVENTS or dates < MIN_DATES:
        return f"NOT YET JUDGED: {n} events recorded whole and finished on {dates} report dates; {MIN_EVENTS} on {MIN_DATES} are asked for"
    mean, sd = j["net"].mean(), j["net"].std(ddof=1)
    t = mean / (sd / np.sqrt(n)) if sd > 0 else float("inf") if mean > 0 else float("-inf")
    ok = mean >= BAR_NET and t >= BAR_T
    return (f"{'PASSES' if ok else 'DOES NOT PASS'}: {n} events on {dates} report dates, net ${mean:,.2f} an event on average "
            f"(at least ${BAR_NET:g} asked), t {t:.2f} (at least {BAR_T:g} asked)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=str(ROOT / "state" / "us-kpi"))
    ap.add_argument("--settle", action="store_true", help="look up how finished markets settled (public data)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    state, out = Path(args.state), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    b, m = top.load(state)
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say("Test K1: small orders at the best prices of the earnings markets (docs/13_round_six.md, section 4c)")
    say(f"scored {pd.Timestamp.now(tz='UTC'):%d %B %Y, %H:%M} UTC. A paper account. No order was placed and no reward was paid to anyone.")
    if not len(b) or not len(m):
        say("nothing recorded yet")
        (out / "kp_summary.txt").write_text("\n".join(lines) + "\n")
        return 0
    now = pd.Timestamp.now(tz="UTC").timestamp()
    say(f"recorded: {len(b):,} readings of {b['slug'].nunique()} markets, from {pd.Timestamp(b['ts'].min(), unit='s'):%d %b %H:%M} to "
        f"{pd.Timestamp(b['ts'].max(), unit='s'):%d %b %H:%M} UTC")
    terms = m.set_index("slug").to_dict("index")
    keys = {s: event_of(s) for s in terms}
    per_event: dict[str, int] = {}
    for s, k in keys.items():
        if k is not None:
            per_event[k[0]] = per_event.get(k[0], 0) + 1
    closed = [s for s, g in b.groupby("slug") if (g["state"] != "OPEN").any()]
    settle = top.settlements(state, closed, args.settle)
    rows = []
    for slug, g in b.groupby("slug"):
        if slug not in terms or keys.get(slug) is None or pd.isna(terms[slug].get("pool")) or pd.isna(terms[slug].get("target")):
            continue
        y = float(settle[slug]) if slug in settle.index else None
        rows += event_rows(slug, g.to_dict("records"), terms[slug], y, per_event[keys[slug][0]], now)
    events = pd.DataFrame(rows)
    if not len(events):
        say("no earnings market with known terms yet")
        (out / "kp_summary.txt").write_text("\n".join(lines) + "\n")
        return 0
    events.round(4).to_csv(out / "kp_events.csv", index=False)
    show = ["event", "report_date", "reports", "whole", "hours", "cover", "qualifies", "resting", "share", "reward_paid", "fills", "bought", "sold", "fees", "held_after_cut",
            "pnl_fills", "net"]
    one = events[(events["in_event"] == 1) & (events["size"] == rule.JUDGED)].sort_values(["report_date", "event"])
    say()
    say(f"events that are one market, {rule.JUDGED} contracts a side (qualifies: share of the time the book was paid; resting: share of the time our orders rested; "
        "share: our part of the score while resting)")
    say(one[show].round(3).to_string(index=False) if len(one) else "   none yet")
    k = events[(events["in_event"] == 1) & events["whole"] & events["net"].notna()]
    say()
    say("events that are one market, by order size, recorded whole and finished")
    if len(k):
        g = k.groupby("size").agg(events=("net", "size"), reward=("reward_paid", "sum"), fills=("fills", "sum"), contracts=("bought", lambda s: s.sum() + k.loc[s.index, "sold"].sum()),
                                  fees=("fees", "sum"), pnl_fills=("pnl_fills", "sum"), net=("net", "sum"), an_event=("net", "mean"), worst=("net", "min"),
                                  t=("net", lambda s: s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if len(s) > 1 and s.std(ddof=1) > 0 else np.nan),
                                  **{f"cap_{p}": (f"reward_cap_{p}", "sum") for p in CAPS}).reset_index()
        g.round(2).to_csv(out / "kp_by_size.csv", index=False)
        say(g.round(2).to_string(index=False))
    else:
        say("   none yet")
    many = events[(events["in_event"] > 1) & (events["size"] == rule.JUDGED)]
    if len(many):
        say()
        say("events of several markets, the pool divided evenly between them (an assumption; described, not judged)")
        g = many.groupby(["report_date", "event"]).agg(markets=("slug", "size"), whole=("whole", "all"), reward=("reward_paid", "sum"), fills=("fills", "sum"),
                                                       pnl_fills=("pnl_fills", "sum"), net=("net", "sum")).reset_index()
        g.round(2).to_csv(out / "kp_events_of_several.csv", index=False)
        say(g.round(2).to_string(index=False))
    say()
    say("Verdict by the bar fixed in advance (events that are one market, 100 contracts a side): " + verdict(events))
    (out / "kp_summary.txt").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
