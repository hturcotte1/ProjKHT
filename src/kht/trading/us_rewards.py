"""A paper account that rests small orders before games on Polymarket US.

Polymarket US pays a published reward to resting orders in every game it
lists (docs/09_sports_rewards.md). This follows every game in the reward
programmes for match winners through the six hours before its start and
works out, from the real order books:

* what an order of a given size, resting at the price where other people's
  size is, would have been paid by the published formula;
* how often such an order would have been traded against, at what price.

It is a simulation. Nothing is traded and no key is used: the schedule of
rewards and the order books are public. The rules below are fixed in
docs/09 and must not be changed while the test runs.

Files, under the state directory:

    runs/<run>/games.csv.gz   one row per game per US date: seconds watched, and what each order size accrued
    runs/<run>/hits.csv       one row each time a resting order would have been traded against
    log.csv                   one line per run
    STATUS.md                 the latest run in words

``scripts/us_rewards_score.py`` adds the runs up and judges them.

Only the standard library and ``requests`` are used.
"""

from __future__ import annotations

import concurrent.futures as cf
import csv
import gzip
import io
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from ..api.polymarket_us import PolymarketUS
from .us_recorder import _amount, _append, _num, book_sides, reward_walk

MONEYLINE = re.compile(r"(?:^|_)(?:moneyline|ml)(?:_|$)")      # programmes on who wins the game
PRODUCT = "aec"                     # the exchange's code for a two-way market on who wins
GRID = (10, 25, 50, 100, 250, 500, 1000)   # order sizes followed, in contracts on each side
DEPTH = 20.0                        # other people's contracts that mark a price as real
MAX_TICKS = 5                       # how far from the best price that level may be
MAX_WIDTH = 0.10                    # widest gap between our two prices at which we still quote
PULL = 600                          # seconds before the recorded start at which quoting stops
WINDOW = 6 * 3600                   # the "day-of" period: six hours before the start
MAX_GAP = 900                       # two readings further apart than this are not joined up
REFRESH = 1800                      # seconds between readings of the reward schedule
ET = ZoneInfo("America/New_York")   # the exchange counts reward days in Eastern Time
TICKS = (0.01, 0.005, 0.0025, 0.001)

GAME_FIELDS = (["run", "slug", "date", "program", "pool", "markets_in_event", "target", "discount", "max_spread", "start", "first_ts", "last_ts", "polls",
                "obs_s", "quote_s", "cap_s", "paid_bid_s", "paid_ask_s", "paid_bid_alone_s", "paid_ask_alone_s", "score_bid_s", "score_ask_s"]
               + [f"acc_bid_{x}" for x in GRID] + [f"acc_ask_{x}" for x in GRID]
               + ["mid_first", "mid_last", "bid_last", "ask_last", "vol_first", "vol_last", "state_last"])
HIT_FIELDS = ["run", "slug", "program", "start", "t0", "t1", "side", "px", "dv", "vwap", "last", "crossed", "cross_qty", "mid0", "mid1", "best_bid1", "best_ask1"]
LOG_FIELDS = ["run", "started", "ended", "minutes", "cycles", "books", "errors", "games", "games_quoted", "hits"]


def _when(x: Any) -> float | None:
    """A timestamp from the gateway as seconds since 1970. It writes them two ways."""
    if not x:
        return None
    s = str(x).strip().replace(" ", "T")
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    m = re.match(r"^(.*?)(\.\d+)?([+-]\d{2}(?::?\d{2})?)?$", s)
    if not m:
        return None
    head, frac, zone = m.group(1), (m.group(2) or "")[:7], m.group(3) or "+00:00"
    if len(zone) == 3:
        zone += ":00"
    try:
        return datetime.fromisoformat(head + frac + zone).timestamp()
    except ValueError:
        return None


def event_key(slug: str) -> str:
    """What game a market belongs to: its slug without the product code, up to the date."""
    m = re.search(r"\d{4}-\d{2}-\d{2}", slug)
    body = slug.split("-", 1)[1] if "-" in slug else slug
    return body[: m.end() - (len(slug) - len(body))] if m else body


def games(schedule: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """The two-way markets on who wins a game that sit in a "day-of" reward programme.

    The pool of a programme is for one game and one period, and is shared
    by the programme's markets in that game. Where the market on who wins
    is the programme's only market in its game, the pool is its own.
    Where it is not (table tennis lists two more), the pool is taken to be
    split equally, which is an assumption.
    """
    per_event: dict[tuple[str, str], int] = {}
    found: dict[str, dict[str, Any]] = {}
    for m in schedule:
        slug = m.get("marketSlug") or ""
        if m.get("category") != "SPR" or not slug:
            continue
        start = _when(m.get("eventStartTime"))
        for tp in m.get("timePeriods") or []:
            pid = tp.get("programId") or ""
            if tp.get("period") != "day_of" or tp.get("programType") != "liquidityProgram" or tp.get("status") != "active" or not MONEYLINE.search(pid):
                continue
            per_event[(pid, event_key(slug))] = per_event.get((pid, event_key(slug)), 0) + 1
            pool, target, discount = _num(tp.get("rewardPool")), _num(tp.get("targetSize")), _num(tp.get("discountFactor"))
            if (m.get("instrumentProduct") != PRODUCT or m.get("instrumentState") != "INSTRUMENT_STATE_OPEN" or start is None
                    or not pool or not target or discount is None):
                continue
            found[slug] = {"slug": slug, "program": pid, "pool": pool, "target": target, "discount": discount, "max_spread": _num(tp.get("maxSpread")),
                           "start": start, "event": event_key(slug)}
    for g in found.values():
        g["markets_in_event"] = per_event.get((g["program"], g["event"]), 1)
    return found


def infer_tick(prices: list[float]) -> float:
    """The largest tick size every quoted price is a multiple of."""
    for tick in TICKS:
        if all(abs(p / tick - round(p / tick)) < 1e-6 for p in prices):
            return tick
    return TICKS[-1]


def quote_level(levels: list[tuple[float, float]], tick: float, depth: float = DEPTH, max_ticks: int = MAX_TICKS) -> float | None:
    """The price our order joins on one side of a book.

    Walking from the best price, it is the first price by which other
    people's orders add up to ``depth`` contracts. An order of a fraction of
    a contract at the best price is not a price anybody stands behind. If
    that level is more than ``max_ticks`` from the best price, there is no
    real price near and the side is not quoted.
    """
    if not levels:
        return None
    best, cum = levels[0][0], 0.0
    for px, qty in levels:
        if round(abs(px - best) / tick) > max_ticks:
            return None
        cum += qty
        if cum >= depth - 1e-9:
            return px
    return None


def side_with_order(levels: list[tuple[float, float]], at: float, x: float, target: float, discount: float, tick: float) -> tuple[float | None, float]:
    """One side of a book with ``x`` contracts of ours resting at the price ``at``.

    Returns the price at which the side reaches the target size (None if it
    never does, in which case it is not paid) and our share of the side's
    score. Scored as the exchange documents it: every order from the best
    price to the price where the target is reached scores
    discount ** (ticks from the best price) * size.
    """
    if not levels:
        return None, 0.0
    best, cum, score, ours = levels[0][0], 0.0, 0.0, 0.0
    for px, qty in levels:
        mine = x if abs(px - at) < 1e-9 else 0.0
        weight = discount ** round(abs(px - best) / tick)
        score += weight * (qty + mine)
        ours += weight * mine
        cum += qty + mine
        if cum >= target - 1e-9:
            return px, (ours / score if score > 0 else 0.0)
    return None, (ours / score if score > 0 else 0.0)


def read_book(book: dict[str, Any]) -> dict[str, Any]:
    bids, asks = book_sides(book)
    st = book.get("stats") or {}
    return {"bids": bids, "asks": asks, "state": book.get("state") or "", "vol": _num(st.get("sharesTraded")), "notional": _amount(st.get("notionalTraded")),
            "last": _amount(st.get("lastTradePx")), "last_t": _when(st.get("lastTradeSetTime")),
            "low": _amount(st.get("lowPx")), "low_t": _when(st.get("lowSetTime")), "high": _amount(st.get("highPx")), "high_t": _when(st.get("highSetTime"))}


def _paid(bid_at: float | None, ask_at: float | None, max_spread: float | None) -> tuple[bool, bool]:
    """Whether each side is paid this second. With a maximum spread, both are or neither is."""
    if max_spread is not None:
        ok = bid_at is not None and ask_at is not None and (ask_at - bid_at) <= 2.0 * max_spread + 1e-9
        return ok, ok
    return bid_at is not None, ask_at is not None


def quote_state(b: dict[str, Any], game: dict[str, Any]) -> dict[str, Any]:
    """What the paper account would have resting in this book, and what each order size would score.

    ``quoting`` is true when both sides have a real price near the best and
    those two prices are at most MAX_WIDTH apart. ``share[x]`` holds, for
    each order size, our share of each side's score with that order in the
    book, or 0 where the side would not be paid.
    """
    bids, asks = b["bids"], b["asks"]
    tick = infer_tick([p for p, _ in bids + asks]) if bids or asks else 0.01
    target, discount, max_spread = game["target"], game["discount"], game["max_spread"]
    out: dict[str, Any] = {"best_bid": bids[0][0] if bids else None, "best_ask": asks[0][0] if asks else None, "quoting": False, "share": {}}
    out["mid"] = (out["best_bid"] + out["best_ask"]) / 2.0 if bids and asks else None
    alone_bid_at, score_bid = reward_walk(bids, target, discount, tick)
    alone_ask_at, score_ask = reward_walk(asks, target, discount, tick)
    out["alone"] = _paid(alone_bid_at, alone_ask_at, max_spread)
    out["score"] = (score_bid, score_ask)
    bid_px, ask_px = quote_level(bids, tick), quote_level(asks, tick)
    if bid_px is None or ask_px is None or ask_px <= bid_px or ask_px - bid_px > MAX_WIDTH + 1e-9:
        return out
    out.update({"quoting": True, "bid_px": bid_px, "ask_px": ask_px})
    for x in GRID:
        bid_at, bid_share = side_with_order(bids, bid_px, x, target, discount, tick)
        ask_at, ask_share = side_with_order(asks, ask_px, x, target, discount, tick)
        bid_ok, ask_ok = _paid(bid_at, ask_at, max_spread)
        out["share"][x] = (bid_share if bid_ok else 0.0, ask_share if ask_ok else 0.0)
    return out


def hits(prev: dict[str, Any], q: dict[str, Any], cur: dict[str, Any], t0: float) -> list[dict[str, Any]]:
    """Whether an order resting since ``t0`` at the prices in ``q`` would have been traded against by ``cur``.

    Polymarket US publishes no list of trades. A book carries the running
    total of contracts and dollars traded, the last trade and the day's
    lowest and highest trade. If contracts traded between two readings and
    any of the three says a trade took place at our bid or below, the bid
    is taken to have been hit, for as many contracts as traded. The same
    for the offer. This assumes our order is first in line and that all of
    the trading went through it, which is the unkind assumption if being
    traded against is bad news. If the other side's orders have moved to
    our price or through it, they would have traded against us instead of
    resting there: the order is taken to be hit for their size.
    """
    out = []
    dv = None
    if prev.get("vol") is not None and cur.get("vol") is not None:
        dv = cur["vol"] - prev["vol"]
        if dv < -1e-9:                      # the running total starts again with a new session
            dv = cur["vol"]
    vwap = None
    if dv is not None and dv > 1e-9 and prev.get("notional") is not None and cur.get("notional") is not None:
        v = (cur["notional"] - prev["notional"]) / dv
        vwap = v if 0.0 < v < 1.0 else None
    new_last = cur["last"] if cur.get("last") is not None and (cur.get("last_t") or 0) > t0 else None
    new_low = cur["low"] if cur.get("low") is not None and (cur.get("low_t") or 0) > t0 else None
    new_high = cur["high"] if cur.get("high") is not None and (cur.get("high_t") or 0) > t0 else None
    lows = [p for p in (vwap, new_last, new_low) if p is not None]
    highs = [p for p in (vwap, new_last, new_high) if p is not None]
    traded = dv is not None and dv > 1e-9
    for side, px in (("bid", q["bid_px"]), ("ask", q["ask_px"])):
        if side == "bid":
            by_trade = traded and bool(lows) and min(lows) <= px + 1e-9
            through = sum(qty for p, qty in cur["asks"] if p <= px + 1e-9)
        else:
            by_trade = traded and bool(highs) and max(highs) >= px - 1e-9
            through = sum(qty for p, qty in cur["bids"] if p >= px - 1e-9)
        if by_trade or through > 0:
            out.append({"side": side, "px": px, "dv": round(dv, 4) if by_trade else "", "vwap": round(vwap, 4) if vwap is not None else "",
                        "last": new_last if new_last is not None else "", "crossed": int(through > 0), "cross_qty": round(through, 4) if through > 0 else ""})
    return out


def et_date(ts: float) -> str:
    return datetime.fromtimestamp(ts, ET).strftime("%Y-%m-%d")


class Follower:
    """One game being followed: its last reading, and what the paper orders have accrued so far."""

    def __init__(self, game: dict[str, Any]):
        self.game = game
        self.prev: tuple[float, dict[str, Any], dict[str, Any]] | None = None       # time, book, quote state
        self.days: dict[str, dict[str, Any]] = {}
        self.first_ts: float | None = None
        self.last_ts: float | None = None
        self.polls = 0
        self.first: dict[str, Any] = {}
        self.last: dict[str, Any] = {}
        self.hits: list[dict[str, Any]] = []
        self.quoted = False
        self.done = False

    def _day(self, ts: float) -> dict[str, Any]:
        key = et_date(ts)
        if key not in self.days:
            self.days[key] = {"obs_s": 0.0, "quote_s": 0.0, "cap_s": 0.0, "paid_bid_s": 0.0, "paid_ask_s": 0.0, "paid_bid_alone_s": 0.0, "paid_ask_alone_s": 0.0,
                              "score_bid_s": 0.0, "score_ask_s": 0.0, **{f"acc_bid_{x}": 0.0 for x in GRID}, **{f"acc_ask_{x}": 0.0 for x in GRID}}
        return self.days[key]

    def see(self, ts: float, book: dict[str, Any]) -> None:
        """Take one reading of the game's order book at time ``ts``."""
        g = self.game
        b = read_book(book)
        q = quote_state(b, g)
        opens, pulls = g["start"] - WINDOW, g["start"] - PULL
        if self.prev is not None:
            t0, b0, q0 = self.prev
            lo, hi = max(t0, opens), min(ts, pulls)
            if hi > lo and ts - t0 <= MAX_GAP:
                seg, day = hi - lo, self._day(t0)
                day["obs_s"] += seg
                day["paid_bid_alone_s"] += seg * q0["alone"][0]
                day["paid_ask_alone_s"] += seg * q0["alone"][1]
                day["score_bid_s"] += seg * q0["score"][0]
                day["score_ask_s"] += seg * q0["score"][1]
                if q0["quoting"]:
                    self.quoted = True
                    day["quote_s"] += seg
                    day["cap_s"] += seg * (q0["bid_px"] + 1.0 - q0["ask_px"])
                    primary = q0["share"][100]
                    day["paid_bid_s"] += seg * (primary[0] > 0)
                    day["paid_ask_s"] += seg * (primary[1] > 0)
                    for x in GRID:
                        day[f"acc_bid_{x}"] += seg * q0["share"][x][0]
                        day[f"acc_ask_{x}"] += seg * q0["share"][x][1]
                    for h in hits(b0, q0, b, t0):
                        self.hits.append({"slug": g["slug"], "program": g["program"], "start": int(g["start"]), "t0": int(t0), "t1": int(ts), **h,
                                          "mid0": q0["mid"] if q0["mid"] is not None else "", "mid1": q["mid"] if q["mid"] is not None else "",
                                          "best_bid1": q["best_bid"] if q["best_bid"] is not None else "",
                                          "best_ask1": q["best_ask"] if q["best_ask"] is not None else ""})
        snap = {"mid": q["mid"], "bid": q.get("bid_px"), "ask": q.get("ask_px"), "vol": b["vol"], "state": b["state"]}
        if self.first_ts is None:
            self.first_ts, self.first = ts, snap
        if ts <= pulls or not self.last:
            self.last = snap                 # the last reading before quoting stops
        self.done = ts >= pulls              # one reading after quoting stops closes the last interval
        self.last_ts = ts
        self.polls += 1
        self.prev = (ts, b, q)

    def rows(self, run: str) -> list[dict[str, Any]]:
        g = self.game
        base = {"run": run, "slug": g["slug"], "program": g["program"], "pool": g["pool"], "markets_in_event": g["markets_in_event"], "target": g["target"],
                "discount": g["discount"], "max_spread": "" if g["max_spread"] is None else g["max_spread"], "start": int(g["start"]),
                "first_ts": int(self.first_ts or 0), "last_ts": int(self.last_ts or 0), "polls": self.polls,
                "mid_first": _blank(self.first.get("mid")), "mid_last": _blank(self.last.get("mid")), "bid_last": _blank(self.last.get("bid")),
                "ask_last": _blank(self.last.get("ask")), "vol_first": _blank(self.first.get("vol")), "vol_last": _blank(self.last.get("vol")),
                "state_last": self.last.get("state", "")}
        return [{**base, "date": date, **{k: round(v, 3) for k, v in day.items()}} for date, day in sorted(self.days.items())]


def _blank(x: Any) -> Any:
    return "" if x is None else x


def _write_gz(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", newline="") as fh:
        fh.write(buf.getvalue())
    tmp.replace(path)


def _write(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(path)


def run(state: Path, minutes: float, us: PolymarketUS | None = None, interval: float = 120.0, budget: float = 5.0, workers: int = 8,
        now: Callable[[], float] = time.time, sleep: Callable[[float], None] = time.sleep, max_cycles: int | None = None) -> dict[str, Any]:
    """Follow every game in its day-of period for ``minutes`` and write down what the paper orders did.

    Each game's book is read about every ``interval`` seconds, less often
    if that would take more than ``budget`` requests a second.
    """
    if us is None:
        from ..api.http import Http

        us = PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": budget + 2.0}))
    started = now()
    run_id = datetime.fromtimestamp(started, timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = state / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    followers: dict[str, Follower] = {}
    schedule: dict[str, dict[str, Any]] = {}
    read_at, cycles, books, errors, flushed = -1e18, 0, 0, 0, started

    def flush() -> None:
        _write_gz(out / "games.csv.gz", GAME_FIELDS, [r for f in followers.values() for r in f.rows(run_id)])
        _write(out / "hits.csv", HIT_FIELDS, [{"run": run_id, **h} for f in followers.values() for h in f.hits])

    def one(slug: str) -> tuple[str, float, dict[str, Any] | None]:
        try:
            book = us.book(slug)
            return slug, now(), book
        except Exception:
            return slug, now(), None

    while now() - started < minutes * 60.0 and (max_cycles is None or cycles < max_cycles):
        t = now()
        if t - read_at >= REFRESH:
            try:
                schedule = games(list(us.iter_incentives(statuses="active")))
                read_at = t
            except Exception:
                errors += 1
        for slug, g in schedule.items():
            if slug in followers:
                if not followers[slug].done:             # the exchange moves a start time now and then, and its periods move with it
                    followers[slug].game.update({k: g[k] for k in ("pool", "target", "discount", "max_spread", "markets_in_event", "start")})
            elif g["start"] - WINDOW <= t < g["start"] - PULL:
                followers[slug] = Follower(dict(g))
        # a game is read until one reading after quoting stops, which closes its last interval
        active = [s for s, f in followers.items() if not f.done and f.game["start"] - WINDOW <= t]
        with cf.ThreadPoolExecutor(max_workers=workers) as pool:
            for slug, ts, book in pool.map(one, active):
                if not book:
                    errors += 1
                    continue
                books += 1
                try:
                    followers[slug].see(ts, book)
                except Exception:                        # one odd book must not end five hours of recording
                    errors += 1
        cycles += 1
        if now() - flushed >= 900:
            flush()
            flushed = now()
        pause = max(interval, len(active) / budget) - (now() - t)
        if pause > 0 and now() - started + pause < minutes * 60.0:
            sleep(pause)
        elif pause > 0:
            break
    flush()
    ended = now()
    quoted = sum(1 for f in followers.values() if f.quoted)
    n_hits = sum(len(f.hits) for f in followers.values())
    line = {"run": run_id, "started": int(started), "ended": int(ended), "minutes": round((ended - started) / 60.0, 1), "cycles": cycles, "books": books,
            "errors": errors, "games": len(followers), "games_quoted": quoted, "hits": n_hits}
    _append(state / "log.csv", LOG_FIELDS, [line])
    (state / "STATUS.md").write_text(status_text(line, followers))
    return line


def status_text(line: dict[str, Any], followers: dict[str, Follower]) -> str:
    stamp = datetime.fromtimestamp(line["ended"], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    by_prog: dict[str, list[Follower]] = {}
    for f in followers.values():
        by_prog.setdefault(f.game["program"], []).append(f)
    rows = []
    for prog, fs in sorted(by_prog.items(), key=lambda kv: -len(kv[1])):
        obs = sum(d["obs_s"] for f in fs for d in f.days.values())
        quote = sum(d["quote_s"] for f in fs for d in f.days.values())
        acc = sum(d["acc_bid_100"] + d["acc_ask_100"] for f in fs for d in f.days.values())
        pool = fs[0].game["pool"] / fs[0].game["markets_in_event"]
        reward = sum((d["acc_bid_100"] + d["acc_ask_100"]) * f.game["pool"] / f.game["markets_in_event"] / (2.0 * WINDOW) for f in fs for d in f.days.values())
        rows.append(f"| {prog} | {len(fs)} | ${pool:,.2f} | {obs / 3600:,.0f} | {100 * quote / obs if obs else 0:.0f}% | "
                    f"{100 * acc / (2 * quote) if quote else 0:.0f}% | ${reward:,.2f} | {sum(len(f.hits) for f in fs)} |")
    return "\n".join([
        f"# Paper orders before games on Polymarket US: run ended {stamp}", "",
        "A simulation. No orders are placed and no key is used. What this is for, and the rules: docs/09_sports_rewards.md.", "",
        f"- ran for {line['minutes']:.0f} minutes; {line['cycles']} rounds of readings; {line['books']:,} order books read; {line['errors']} errors",
        f"- games followed in their six hours before the start: {line['games']:,}; with a price to rest at: {line['games_quoted']:,}",
        f"- times a resting order would have been traded against: {line['hits']:,}", "",
        "By reward programme, for orders of 100 contracts on each side. The reward is what the published formula gives, before the $1 minimum; "
        "it is not money anyone has been paid.", "",
        "| Programme | Games | Pool a game | Hours watched | Of them quoted | Share of the score | Reward by formula | Times traded against |",
        "|---|---:|---:|---:|---:|---:|---:|---:|", *rows, "",
        "The judged totals over all runs are in reports/research/usr_summary.txt (scripts/us_rewards_score.py).", ""])
