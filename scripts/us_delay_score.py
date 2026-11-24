"""Test D1 on what ``kht us-live`` recorded: orders resting between a UTR match's listed start and its real one.

docs/13_round_six.md, section 4d. A paper account: no order was placed and
no reward was paid to anyone.

    python scripts/us_delay_score.py --settle     # look up how finished matches settled (public data), then score

A tennis match seldom starts when it is listed to. From the first time its
listed start passes until the exchange's own listing shows the match as
started, the rule rests 500 contracts on each side, five cents either side
of the middle of the book, and takes them away at the first reading that
shows play. Whatever was traded against is closed from that reading on at
the prices read, fee paid.

While a match waits, the exchange moves its listed start forward ten or
twenty minutes at a time. The orders stay through that, as long as the
start as it then stands is past or no more than half an hour ahead. (This
was written in on 18 November 2026, before the recorder's first run and
before any match that counts: docs/13, section 4d.)

What that stretch is paid is not known, so the reward is worked out two
ways and the verdict says which it needs:

    as the last part of the six hours before the start ($10 a match), if
    the exchange counts those six hours back from the real start;

    with every second past the listed start, as it then stood, counted as
    play ($50 a match), and the rest as the six hours before.

Writes reports/research/dl_*.csv and dl_summary.txt.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kht.api.polymarket_us import taker_fee_per_share  # noqa: E402
from kht.trading import top_rule as rule  # noqa: E402
from kht.trading.us_top import decode  # noqa: E402

_here = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("us_top_score", _here / "us_top_score.py")
top = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(top)
_spec = importlib.util.spec_from_file_location("us_rewards_score", _here / "us_rewards_score.py")
usr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(usr)

OUT = ROOT / "reports" / "research"
SIZE = 500.0                      # contracts a side: the target size of the reward for play, and twice that of the six hours before
SIZES = (250.0, 500.0)            # 250 is followed beside it; it can only be paid as part of the six hours before
AWAY = 0.05                       # each order rests this far from the middle of the book, rounded outwards to a cent
AHEAD_MOST = 1800.0               # once a listed start has passed, orders stay while the start as it then stands is no further ahead than this
DAY_OF = 6 * 3600.0               # the length of the period before the start
COUNTED_FROM = 1_795_064_400.0    # 19 November 2026, 00:00 US Eastern (05:00 UTC): matches listed to start from here on count, as in test R2
MIN_MATCHES, MIN_DATES, BAR = 400, 10, 3.0
WHOLE_COVER = 0.85                # readings cover this share of the half minutes between the listed start and the real one
WHOLE_BEFORE = 60.0               # the first reading came no later than this after the listed start
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)


def _blank(x: object) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x)) or str(x).strip() in ("", "nan")


def waiting(r: dict) -> bool:
    """The listing says, in so many words, that the match has not started: period "NS", not live, no score."""
    if _blank(r.get("period")) or _blank(r.get("live")):
        return False
    try:
        live = int(float(r.get("live")))
    except (TypeError, ValueError):
        return False
    return str(r.get("period")) == "NS" and live == 0 and (_blank(r.get("score")) or str(r.get("score")) == "0-0")


def playing(r: dict) -> bool:
    """The listing says the match has started (or has been played): live, or any period but "NS"."""
    if _blank(r.get("period")) and _blank(r.get("live")):
        return False                                   # nothing is known: neither waiting nor playing
    try:
        live = int(float(r.get("live"))) if not _blank(r.get("live")) else 0
    except (TypeError, ValueError):
        live = 0
    return live == 1 or (not _blank(r.get("period")) and str(r.get("period")) != "NS")


def quotes(bids: list[tuple[float, float]], asks: list[tuple[float, float]], pos: float, size: float = SIZE) -> dict:
    """The two orders of the rule on one reading: ``size`` on each side, five cents from the middle, or none.

    Nothing rests unless both sides of the book show a price and the two
    best prices are at most three ticks apart: without that there is no
    middle to stand around. The bid is cut by what is already held, the
    offer by what is already owed.
    """
    none = {"bid_px": None, "bid_qty": 0.0, "ask_px": None, "ask_qty": 0.0}
    if not bids or not asks:
        return {**none, "why": "one side is empty"}
    bid, ask = bids[0][0], asks[0][0]
    if ask <= bid + rule.EPS or rule.ticks(ask, bid) > rule.MAX_SPREAD_TICKS:
        return {**none, "why": "best prices too far apart"}
    mid = (bid + ask) / 2.0
    bid_px = math.floor((mid - AWAY) / rule.TICK + 1e-6) * rule.TICK
    ask_px = math.ceil((mid + AWAY) / rule.TICK - 1e-6) * rule.TICK
    if bid_px < rule.LOW - rule.EPS or ask_px > rule.HIGH + rule.EPS:
        return {**none, "why": "too near the end of the price range"}
    bid_qty, ask_qty = max(0.0, min(size, size - pos)), max(0.0, min(size, size + pos))
    return {"bid_px": round(bid_px, 2) if bid_qty > rule.EPS else None, "bid_qty": bid_qty, "ask_px": round(ask_px, 2) if ask_qty > rule.EPS else None, "ask_qty": ask_qty,
            "why": "resting"}


def close_out(pos: float, bids: list[tuple[float, float]], asks: list[tuple[float, float]]) -> tuple[float, float, float]:
    """Sell what is held to the bids as read, or buy back what is owed from the offers. Returns cash, fee and contracts closed."""
    cash = fee = done = 0.0
    left = abs(pos)
    for px, qty in (bids if pos > 0 else asks):
        if left <= rule.EPS:
            break
        take = min(left, qty)
        cash += take * px if pos > 0 else -take * px
        fee += take * taker_fee_per_share(px)
        done += take
        left -= take
    return cash, fee, done


def simulate(rows: list[dict], terms: dict, size: float = SIZE) -> dict:
    """One match: the orders through the stretch between the listed start and the real one, their fills, and the closing when play shows."""
    live = (float(terms["live_target"]), float(terms["live_discount"]), None if pd.isna(terms.get("live_max_spread")) else float(terms["live_max_spread"]))
    before = (float(terms["dayof_target"]), float(terms["dayof_discount"]), None if pd.isna(terms.get("dayof_max_spread")) else float(terms["dayof_max_spread"]))
    pos = cash = fees = wait_s = rest_s = past_s = credit_live = credit_before = credit_ahead = bought = sold = 0.0
    n_fills = 0
    q = prev = None
    listed = started = closed = None
    opened = False                                     # a listed start has passed with the match not started
    for i, r in enumerate(rows):
        ts = float(r["ts"])
        bids, asks = decode(r.get("bids")), decode(r.get("asks"))
        is_open = str(r.get("state")) == "OPEN"
        if q is not None and prev is not None and (q["bid_px"] is not None or q["ask_px"] is not None):
            bf, af = rule.fills(q, prev, r, bids, asks)
            if bf > rule.EPS:
                pos += bf; cash -= bf * q["bid_px"]; bought += bf; n_fills += 1
            if af > rule.EPS:
                pos -= af; cash += af * q["ask_px"]; sold += af; n_fills += 1
        if not is_open and closed is None and listed is not None:
            closed = ts
        start = r.get("start")
        start = None if _blank(start) else float(start)
        q = None
        if playing(r):
            if started is None:
                started = ts
            if abs(pos) > rule.EPS and is_open:          # play shows: what was traded against is closed at the prices read
                got, fee, done = close_out(pos, bids, asks)
                cash += got; fees += fee
                pos -= done if pos > 0 else -done
        elif is_open and started is None and start is not None and waiting(r) and (ts >= start or (opened and start - ts <= AHEAD_MOST)):
            past = ts >= start                         # past the listed start as it stands at this reading
            if past and not opened:
                opened, listed = True, start
            nxt = rows[i + 1] if i + 1 < len(rows) else None
            dt = min(float(nxt["ts"]) - ts, rule.MAX_CREDIT) if nxt is not None else 0.0
            wait_s += dt
            q = quotes(bids, asks, pos, size)
            if q["bid_px"] is not None or q["ask_px"] is not None:
                rest_s += dt
                as_before = dt * sum(rule.shares(bids, asks, q, *before)) / 2.0
                credit_before += as_before
                if past:
                    past_s += dt
                    credit_live += dt * sum(rule.shares(bids, asks, q, *live)) / 2.0
                else:
                    credit_ahead += as_before
        prev = r
    last_open = max((float(r["ts"]) for r in rows if str(r.get("state")) == "OPEN"), default=None)
    return {"pos": pos, "cash": cash, "fees": fees, "wait_s": wait_s, "rest_s": rest_s, "past_s": past_s, "credit_live": credit_live, "credit_before": credit_before,
            "credit_ahead": credit_ahead, "bought": bought, "sold": sold, "fills": n_fills, "listed": listed, "started": started, "closed": closed, "last_open": last_open}


def match_rows(slug: str, rows: list[dict], terms: dict, settle: float | None) -> list[dict]:
    """Every order size on one match, with the reward worked out both ways."""
    if not rows or any(pd.isna(terms.get(k)) for k in ("live_pool", "live_target", "live_discount", "dayof_pool", "dayof_target", "dayof_discount")):
        return []
    first = float(rows[0]["ts"])
    start_first = terms.get("start_first")
    start_first = float(start_first) if start_first is not None and not pd.isna(start_first) else None
    starts = [float(r["start"]) for r in rows if not _blank(r.get("start"))]
    start_last = starts[-1] if starts else start_first
    out = []
    for size in SIZES:
        s = simulate(rows, terms, size)
        listed = s["listed"] if s["listed"] is not None else start_last
        over = s["started"] is not None or s["closed"] is not None            # seen to start, or seen to close without starting
        waited = [r for r in rows if listed is not None and float(r["ts"]) >= listed and (s["started"] is None or float(r["ts"]) < s["started"])
                  and (s["closed"] is None or float(r["ts"]) < s["closed"])]
        span = (min(x for x in (s["started"], s["closed"]) if x is not None) - listed) if over and listed is not None else np.nan
        cover = len(waited) * 30.0 / max(span, 30.0) if over and listed is not None and span > 0 else 1.0
        whole = bool(over and listed is not None and listed >= COUNTED_FROM and first <= listed + WHOLE_BEFORE and cover >= WHOLE_COVER)
        # the reward, two ways
        reward_before = float(terms["dayof_pool"]) * s["credit_before"] / DAY_OF
        play_s = (s["last_open"] - listed + 30.0) if s["last_open"] is not None and listed is not None and s["closed"] is not None else np.nan
        ahead = float(terms["dayof_pool"]) * s["credit_ahead"] / DAY_OF      # the seconds before the listed start as it then stood: the six hours before, either way
        if s["credit_live"] <= 0.0:
            reward_live = ahead                            # nothing that the terms of play would pay: the length of play does not matter
        else:
            reward_live = float(terms["live_pool"]) * s["credit_live"] / play_s + ahead if play_s == play_s and play_s > 0 else np.nan
        if abs(s["pos"]) > rule.EPS:                       # what could not be closed is held to the result
            pnl = s["cash"] - s["fees"] + s["pos"] * settle if settle is not None else np.nan
        else:
            pnl = s["cash"] - s["fees"]
        day = pd.Timestamp(listed, unit="s", tz="UTC").tz_convert("America/New_York").strftime("%Y-%m-%d") if listed is not None else ""
        out.append({"slug": slug, "day": day, "size": size, "whole": whole, "from_start": bool(listed is not None and first <= listed + WHOLE_BEFORE),
                    "listed": listed, "started": s["started"], "closed": s["closed"],
                    "wait_min": s["wait_s"] / 60.0, "rest_min": s["rest_s"] / 60.0, "past_min": s["past_s"] / 60.0,
                    "share_before": s["credit_before"] / s["rest_s"] if s["rest_s"] > 0 else 0.0,
                    "share_live": s["credit_live"] / s["past_s"] if s["past_s"] > 0 else 0.0, "reward_before": reward_before, "reward_live": reward_live,
                    "fills": s["fills"], "bought": s["bought"], "sold": s["sold"], "fees": s["fees"], "held": s["pos"], "settle": settle if settle is not None else np.nan,
                    "pnl_fills": pnl, "net_before": reward_before + pnl if pnl == pnl else np.nan,
                    "net_live": reward_live + pnl if pnl == pnl and reward_live == reward_live else np.nan})
    return out


KINDS = ("the listing showed play when it began", "called off before play", "played, and never shown as played")


def kind(row: dict) -> str:
    """How a finished match ended, as far as the rule is concerned.

    The rule trusts the listing's word that a match has not started. A
    match that settles on one player although the listing never showed
    play was played unseen, and the orders rested through it: whatever
    they made there is luck and is the opposite of what the rule means.
    """
    started, settle = row.get("started"), row.get("settle")
    if started is not None and not pd.isna(started):
        return KINDS[0]
    if settle is not None and not pd.isna(settle) and 0.01 < float(settle) < 0.99:
        return KINDS[1]
    return KINDS[2]


def _z(j: pd.DataFrame, col: str) -> tuple[float, float]:
    mean, z, _ = usr.clustered_z(j[col].to_numpy(), j["day"].to_numpy())
    return mean, z


def verdict(matches: pd.DataFrame) -> str:
    """The bar of docs/13, section 4d, read on the judged account (500 contracts a side)."""
    if not len(matches):
        return "NOT YET JUDGED: nothing recorded"
    j = matches[(matches["size"] == SIZE) & matches["whole"] & matches["net_before"].notna() & matches["net_live"].notna()]
    n, dates = len(j), j["day"].nunique()
    if n < MIN_MATCHES or dates < MIN_DATES:
        return f"NOT YET JUDGED: {n:,} matches recorded whole and finished on {dates} US dates; {MIN_MATCHES:,} on {MIN_DATES} are asked for"
    mb, zb = _z(j, "net_before")
    ml, zl = _z(j, "net_live")
    figures = (f"{n:,} matches on {dates} US dates; paid as the six hours before the start ${mb:,.3f} a match, z {zb:.2f}; "
               f"paid as play from the listed start ${ml:,.3f} a match, z {zl:.2f} (z of {BAR:g} asked)")
    if mb > 0 and zb >= BAR:
        return "PASSES: " + figures
    if ml > 0 and zl >= BAR:
        return "PASSES ONLY IF PLAY IS COUNTED FROM THE LISTED START: " + figures
    return "DOES NOT PASS: " + figures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=str(ROOT / "state" / "us-live"))
    ap.add_argument("--settle", action="store_true", help="look up how finished matches settled (public data)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    state, out = Path(args.state), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    b, m = top.load(state)
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say("Test D1: orders resting between a UTR match's listed start and its real one (docs/13_round_six.md, section 4d)")
    say(f"scored {pd.Timestamp.now(tz='UTC'):%d %B %Y, %H:%M} UTC. A paper account. No order was placed and no reward was paid to anyone.")
    if not len(b) or not len(m):
        say("nothing recorded yet")
        (out / "dl_summary.txt").write_text("\n".join(lines) + "\n")
        return 0
    say(f"recorded: {len(b):,} readings of {b['slug'].nunique()} matches, from {pd.Timestamp(b['ts'].min(), unit='s'):%d %b %H:%M} to "
        f"{pd.Timestamp(b['ts'].max(), unit='s'):%d %b %H:%M} UTC")
    terms = m.set_index("slug").to_dict("index")
    closed = [s for s, g in b.groupby("slug") if (g["state"] != "OPEN").any()]
    settle = top.settlements(state, closed, args.settle)
    rows = []
    for slug, g in b.groupby("slug"):
        if slug in terms:
            rows += match_rows(slug, g.to_dict("records"), terms[slug], float(settle[slug]) if slug in settle.index else None)
    matches = pd.DataFrame(rows)
    if not len(matches):
        say("no match with known reward terms yet")
        (out / "dl_summary.txt").write_text("\n".join(lines) + "\n")
        return 0
    matches.round(4).to_csv(out / "dl_matches.csv", index=False)
    j = matches[matches["size"] == SIZE]
    seen = j[(j["started"].notna() | j["closed"].notna()) & j["from_start"]]          # followed from the listed start: the others were already waiting or playing
    say()
    say(f"matches followed: {len(j):,}; followed from their listed start and seen to start or to close: {len(seen):,}; "
        f"recorded whole and listed to start from 19 November (US Eastern): {int(j['whole'].sum()):,}")
    if len(seen):
        w = seen["wait_min"]
        rested = f"the orders rested for {seen['rest_min'].sum() / w.sum():.0%}" if w.sum() > 0 else "there were none yet"
        late = (seen[["started", "closed"]].min(axis=1) - seen["listed"]) / 60.0
        say(f"minutes from the first listed start to the first sign of play (or the close): a quarter of matches under {late.quantile(0.25):.0f}, half under {late.median():.0f}, "
            f"a quarter over {late.quantile(0.75):.0f}; of the minutes in which the rule lets orders rest, {rested}")
    k = matches[matches["whole"] & matches["net_before"].notna() & matches["net_live"].notna()]        # the matches the verdict will read
    say()
    say("by order size, matches recorded whole and finished (reward both ways; fills closed when play shows, fee paid)")
    if len(k):
        g = k.groupby("size").agg(matches=("slug", "size"), waited_min=("wait_min", "sum"), rested_min=("rest_min", "sum"), past_min=("past_min", "sum"),
                                  share_before=("share_before", "mean"),
                                  share_live=("share_live", "mean"), reward_before=("reward_before", "sum"), reward_live=("reward_live", "sum"),
                                  matches_filled=("fills", lambda s: int((s > 0).sum())), contracts=("bought", lambda s: s.sum() + k.loc[s.index, "sold"].sum()),
                                  fees=("fees", "sum"), pnl_fills=("pnl_fills", "sum"), net_before=("net_before", "sum"), net_live=("net_live", "sum")).reset_index()
        g.round(2).to_csv(out / "dl_by_size.csv", index=False)
        say(g.round(2).to_string(index=False))
        d = k[k["size"] == SIZE].groupby("day").agg(matches=("slug", "size"), waited_min=("wait_min", "sum"), reward_before=("reward_before", "sum"),
                                                    reward_live=("reward_live", "sum"), matches_filled=("fills", lambda s: int((s > 0).sum())),
                                                    pnl_fills=("pnl_fills", "sum"), net_before=("net_before", "sum"), net_live=("net_live", "sum")).reset_index()
        d.round(2).to_csv(out / "dl_by_day.csv", index=False)
        say()
        say(f"by US date, {SIZE:g} contracts a side")
        say(d.round(2).to_string(index=False))
        kk = k[k["size"] == SIZE]
        kk = kk.assign(kind=[kind(r) for r in kk.to_dict("records")])
        e = kk.groupby("kind").agg(matches=("slug", "size"), rested_in=("rest_min", lambda s: int((s > 0).sum())), matches_filled=("fills", lambda s: int((s > 0).sum())),
                                   pnl_fills=("pnl_fills", "sum"), reward_before=("reward_before", "sum"), reward_live=("reward_live", "sum"),
                                   net_before=("net_before", "sum"), net_live=("net_live", "sum")).reindex([x for x in KINDS if x in set(kk["kind"])]).reset_index()
        e.round(2).to_csv(out / "dl_by_kind.csv", index=False)
        say()
        say("by how the match went (described: the rule trusts the listing, and a match played without the listing showing it is the case in which that fails)")
        say(e.round(2).to_string(index=False))
    else:
        say("   none yet")
    say()
    say("Verdict by the bar fixed in advance (500 contracts a side): " + verdict(matches))
    (out / "dl_summary.txt").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
