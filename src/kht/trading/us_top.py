"""The whole book of a few Polymarket US markets, read every half minute.

docs/13_round_six.md, test G1. Read-only, public data, no key.

Some reward programmes of the exchange cover a single market that is listed
afresh every day: gold up or down, silver up or down, and the same for four
coins. Their pools are large and belong to that one market. This reads the
book of each such market, to the depth the reward formula needs, each time
the public book can have changed (it is a snapshot the exchange renews
every thirty seconds), together with the running totals of trading.

Nothing is decided here. The rule of test G1 is applied afterwards, by
scripts/us_top_score.py, to what this wrote down.

Files, under ``state/us-top/runs/<run>/``:

    books.csv.gz   every reading: both sides of the book to twelve levels, the totals traded, the last, lowest and highest trade
    markets.csv    each market read: its programme, pool, target size, discount factor, maximum spread, and what it asks
    prices.csv.gz  the exchange's own reference price of each market's asset, as fifteen-second candles (added 18 November 2026)
"""

from __future__ import annotations

import concurrent.futures as cf
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..api.polymarket_us import PolymarketUS
from .us_recorder import _amount, _append, _num, book_sides
from .us_rewards import _when, _write, _write_gz

PROGRAMMES = ("metals_gold_updown_1d", "metals_silver_updown_1d", "crypto_btc_updown_1d", "crypto_alt_updown_1d")
SWEEP = 30.0              # seconds between two readings of one book: the public book is renewed every thirty
DEPTH = 12                # price levels kept on each side
SCHEDULE_EVERY = 900      # seconds between two readings of the reward schedule (it takes a hundred requests)
CHAIN_EVERY = 60          # seconds between two looks for the market that follows the one being read
AFTER = 120               # a market is read until this long after it has stopped being open
GIVE_UP = 120             # readings in a row without a book after which a market expected by name is dropped
DATED = re.compile(r"^(?P<stem>.+?)-(?P<date>\d{4}-\d{2}-\d{2})-(?P<hhmm>\d{4})z$")

BOOK_FIELDS = ["run", "ts", "slug", "state", "tx", "bids", "asks", "traded", "notional", "last", "last_t", "low", "low_t", "high", "high_t", "open_interest"]
MARKET_FIELDS = ["run", "slug", "program", "pool", "target", "discount", "max_spread", "period", "question", "window_start", "window_end", "end", "price_to_beat",
                 "first_seen", "asset"]
PRICE_FIELDS = ["run", "asset", "ts", "open", "high", "low", "close", "ticks"]
CANDLE = 15               # seconds in one candle of the reference price
LOG_FIELDS = ["run", "started", "ended", "minutes", "cycles", "schedule_reads", "books", "errors", "markets"]


def wanted(program_id: str, programmes: tuple[str, ...] = PROGRAMMES) -> str | None:
    """The programme of ours that a schedule entry belongs to, or None. Programme ids carry the date they were set up."""
    for p in programmes:
        if program_id == p or program_id.startswith(p + "_"):
            return p
    return None


def from_schedule(schedule: list[dict[str, Any]], programmes: tuple[str, ...] = PROGRAMMES) -> dict[str, dict[str, Any]]:
    """The open markets of our programmes in one reading of the reward schedule, with the programme's terms."""
    found: dict[str, dict[str, Any]] = {}
    for m in schedule:
        slug = m.get("marketSlug") or ""
        if not slug or m.get("instrumentState") != "INSTRUMENT_STATE_OPEN":
            continue
        for tp in m.get("timePeriods") or []:
            name = wanted(tp.get("programId") or "", programmes)
            if name is None or tp.get("status") != "active":
                continue
            pool, target, discount = _num(tp.get("rewardPool")), _num(tp.get("targetSize")), _num(tp.get("discountFactor"))
            if not pool or not target or discount is None:
                continue
            found[slug] = {"slug": slug, "program": tp.get("programId"), "pool": pool, "target": target, "discount": discount,
                           "max_spread": _num(tp.get("maxSpread")), "period": tp.get("period") or ""}
    return found


def next_slug(slug: str, next_window_start: Any) -> str | None:
    """The slug of the market that follows ``slug``, from the time the exchange gives for its next window."""
    m = DATED.match(slug)
    t = _when(next_window_start)
    if not m or t is None:
        return None
    d = datetime.fromtimestamp(t, timezone.utc)
    return f"{m.group('stem')}-{d:%Y-%m-%d}-{d:%H%M}z"


def market_terms(market: dict[str, Any]) -> dict[str, Any]:
    """What one such market asks, from the exchange's description of it."""
    t = market.get("assetPriceTerms") or {}
    beat = t.get("priceToBeat") or {}
    a = t.get("asset") or {}
    asset = f"{str(a.get('assetClass') or '').replace('ASSET_CLASS_', '').lower()}:{a.get('symbol')}" if a.get("symbol") and a.get("assetClass") else None
    return {"question": market.get("question") or "", "window_start": _when(t.get("windowStart")), "window_end": _when(t.get("windowEnd")),
            "end": _when(market.get("endDate")), "price_to_beat": _amount(beat) if beat else None, "next_window_start": t.get("nextWindowStart"),
            "asset": asset}


def _short(x: float, places: int) -> str:
    return f"{x:.{places}f}".rstrip("0").rstrip(".")


def encode(levels: list[tuple[float, float]], depth: int = DEPTH) -> str:
    """One side of a book as text, best price first: ``price:size;price:size``."""
    return ";".join(f"{_short(px, 4)}:{_short(qty, 2)}" for px, qty in levels[:depth])


def decode(text: Any) -> list[tuple[float, float]]:
    """The reverse of ``encode``."""
    if not isinstance(text, str) or not text:
        return []
    out = []
    for part in text.split(";"):
        px, _, qty = part.partition(":")
        out.append((float(px), float(qty)))
    return out


def book_row(run_id: str, ts: float, slug: str, book: dict[str, Any]) -> dict[str, Any]:
    bids, asks = book_sides(book)
    st = book.get("stats") or {}
    return {"run": run_id, "ts": round(ts, 1), "slug": slug, "state": str(book.get("state") or "").replace("MARKET_STATE_", ""),
            "tx": str(book.get("transactTime") or "")[:23], "bids": encode(bids), "asks": encode(asks),
            "traded": _num(st.get("sharesTraded")), "notional": _amount(st.get("notionalTraded")),
            "last": _amount(st.get("lastTradePx")), "last_t": _when(st.get("lastTradeSetTime")),
            "low": _amount(st.get("lowPx")), "low_t": _when(st.get("lowSetTime")), "high": _amount(st.get("highPx")), "high_t": _when(st.get("highSetTime")),
            "open_interest": _num(st.get("openInterest"))}


def earlier(state: Path, programmes: tuple[str, ...] = PROGRAMMES) -> dict[str, dict[str, Any]]:
    """The last market of each kind that earlier runs wrote down, with its programme's terms.

    A run can start while none of a programme's markets is open: gold's
    closes at 22:00 UTC and the next opens at 23:15. The market that was
    last read is then the only way to the name of the next one.
    """
    import csv

    last: dict[str, dict[str, Any]] = {}
    for path in sorted(state.glob("runs/*/markets.csv")):
        try:
            with path.open(newline="") as fh:
                rows = list(csv.DictReader(fh))
        except OSError:
            continue
        for r in rows:
            m = DATED.match(r.get("slug") or "")
            if not m or wanted(r.get("program") or "", programmes) is None:
                continue
            key = m.group("stem")
            stamp = m.group("date") + m.group("hhmm")
            if key not in last or stamp >= last[key]["_stamp"]:
                last[key] = {"_stamp": stamp, "slug": r["slug"], "program": r.get("program"), "pool": _num(r.get("pool")), "target": _num(r.get("target")),
                             "discount": _num(r.get("discount")), "max_spread": _num(r.get("max_spread")), "period": r.get("period") or ""}
    return {v["slug"]: {k: x for k, x in v.items() if k != "_stamp"} for v in last.values() if v["pool"] and v["target"] and v["discount"] is not None}


def run(state: Path, minutes: float, us: PolymarketUS | None = None, budget: float = 4.0, sweep: float = SWEEP, programmes: tuple[str, ...] = PROGRAMMES,
        now: Callable[[], float] = time.time, sleep: Callable[[float], None] = time.sleep, max_cycles: int | None = None,
        background: bool = True) -> dict[str, Any]:
    """Record for ``minutes``. ``background`` reads the long reward schedule in a second thread, so that it never delays a reading."""
    if us is None:
        from ..api.http import Http

        us = PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": budget}))
    started = now()
    run_id = datetime.fromtimestamp(started, timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = state / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    lock = threading.Lock()
    known: dict[str, dict[str, Any]] = {}           # every market this run knows of, with its terms
    gone: dict[str, float] = {}                     # when a market was first seen not open
    unread: dict[str, int] = {}                     # readings in a row that failed, for a market never read yet
    was_read: set[str] = set()                      # markets a book was read of in this run
    described: set[str] = set()
    books: list[dict[str, Any]] = []
    prices: list[dict[str, Any]] = []
    last_candle: dict[str, int] = {}                # the start of the newest finished candle kept, by asset
    for slug, terms in earlier(state, programmes).items():
        known[slug] = {**terms, "first_seen": round(started, 1)}
        gone[slug] = -1e18                          # a market of an earlier run: not read, only asked what follows it
    counts = {"schedule": 0, "errors": 0}
    scheduled_at = [-1e18]
    busy = [False]

    def read_schedule() -> None:
        try:
            found = from_schedule(list(us.iter_incentives(statuses=None)), programmes)
            with lock:
                for slug, terms in found.items():
                    if slug in known:
                        known[slug].update(terms)
                    else:
                        known[slug] = {**terms, "first_seen": round(now(), 1)}
                counts["schedule"] += 1
        except Exception:
            with lock:
                counts["errors"] += 1
        finally:
            busy[0] = False

    def describe(slug: str) -> None:
        """Fill in what a market asks: its window, its price to beat, and when the window after it starts."""
        try:
            terms = market_terms(us.market(slug))
        except Exception:
            counts["errors"] += 1
            return
        with lock:
            if slug in known:
                known[slug].update({k: v for k, v in terms.items() if v is not None})
                described.add(slug)

    def chain(t: float) -> None:
        """Add the market that follows each known one, from a minute before its window starts.

        This goes over every market known, open or long closed: gold's next
        market opens more than an hour after the one before it has closed.
        """
        with lock:
            for slug, m in list(known.items()):
                start = _when(m.get("next_window_start"))
                if start is None or start < t - 2 * 86_400 or start > t + CHAIN_EVERY:
                    continue
                follower = next_slug(slug, m.get("next_window_start"))
                if follower and follower not in known:
                    # it takes its programme's terms from the one before it until the schedule has been read again
                    known[follower] = {**{k: m.get(k) for k in ("program", "pool", "target", "discount", "max_spread", "period")},
                                       "slug": follower, "first_seen": round(t, 1)}
                    unread[follower] = 0

    def flush() -> None:
        with lock:
            rows = [{"run": run_id, **m} for s, m in known.items() if s in was_read]
        _write_gz(out / "books.csv.gz", BOOK_FIELDS, books)
        _write(out / "markets.csv", MARKET_FIELDS, rows)
        _write_gz(out / "prices.csv.gz", PRICE_FIELDS, prices)

    def read_prices(t: float, slugs: list[str]) -> None:
        """Keep the finished candles of the reference price of each asset whose market is being read. One request a sweep."""
        with lock:
            assets = sorted({known[s]["asset"] for s in slugs if known.get(s, {}).get("asset")})
        if not assets:
            return
        since = min((last_candle.get(a, 0) for a in assets), default=0)
        start = max(since + CANDLE, int(t) - 3600) if since else int(t) - 120
        try:
            got = us.asset_prices(assets, start, 0, f"{CANDLE}S")
        except Exception:
            counts["errors"] += 1
            return
        for asset, candles in got.items():
            for c in candles:
                if c["ts"] > last_candle.get(asset, 0) and c["ts"] + CANDLE <= t:      # the candle in progress waits for the next sweep
                    prices.append({"run": run_id, "asset": asset, **c})
                    last_candle[asset] = c["ts"]

    def one(slug: str) -> tuple[str, float, dict[str, Any] | None]:
        try:
            return slug, now(), us.book(slug)
        except Exception:
            return slug, now(), None

    cycles, flushed, chained_at = 0, started, -1e18
    while now() - started < minutes * 60.0 and (max_cycles is None or cycles < max_cycles):
        t = now()
        if t - scheduled_at[0] >= SCHEDULE_EVERY and not busy[0]:
            scheduled_at[0], busy[0] = t, True
            if background and known:
                threading.Thread(target=read_schedule, daemon=True).start()
            else:
                read_schedule()                      # the first reading is waited for: without it there is nothing to read
        with lock:
            active = [s for s in known if s not in gone or t - gone[s] <= AFTER]
        if t - chained_at >= CHAIN_EVERY:
            chained_at = t
            with lock:
                todo = [s for s, m in known.items() if s not in described or (s in active and s not in unread and m.get("price_to_beat") is None)]
            for slug in todo:                        # once for each market, and again while an open one has no price to beat yet
                describe(slug)
            chain(t)
            with lock:
                active = [s for s in known if s not in gone or t - gone[s] <= AFTER]
        if active:
            with cf.ThreadPoolExecutor(max_workers=min(8, len(active))) as pool:
                for slug, ts, book in pool.map(one, active):
                    if not book:
                        if slug in unread:           # a market looked for under its expected name before its book exists: not an error.
                            unread[slug] += 1        # Given up after an hour; the reading of the schedule finds it if it comes later.
                            if unread[slug] >= GIVE_UP:
                                with lock:
                                    known.pop(slug, None)
                                unread.pop(slug, None)
                        else:
                            counts["errors"] += 1
                        continue
                    unread.pop(slug, None)
                    was_read.add(slug)
                    try:
                        row = book_row(run_id, ts, slug, book)
                    except Exception:                # one odd book must not end the run
                        counts["errors"] += 1
                        continue
                    books.append(row)
                    if row["state"] != "OPEN":
                        gone.setdefault(slug, ts)
                    else:
                        gone.pop(slug, None)
            read_prices(now(), active)
        cycles += 1
        if now() - flushed >= 600:
            flush()
            flushed = now()
        pause = sweep - (now() - t)
        if pause > 0 and now() - started + pause < minutes * 60.0:
            sleep(pause)
        elif pause > 0:
            break
    flush()
    ended = now()
    read = {s: m for s, m in known.items() if s in was_read}
    line = {"run": run_id, "started": int(started), "ended": int(ended), "minutes": round((ended - started) / 60.0, 1), "cycles": cycles,
            "schedule_reads": counts["schedule"], "books": len(books), "errors": counts["errors"], "markets": len(read)}
    _append(state / "log.csv", LOG_FIELDS, [line])
    (state / "STATUS.md").write_text(status_text(line, read, books))
    return line


def status_text(line: dict[str, Any], known: dict[str, dict[str, Any]], books: list[dict[str, Any]]) -> str:
    """A plain summary of one run. It lists what was read and scores nothing."""
    stamp = datetime.fromtimestamp(line["ended"], timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    per: dict[str, int] = {}
    for b in books:
        per[b["slug"]] = per.get(b["slug"], 0) + 1
    lines = ["# The top of the book in single-market reward programmes", "",
             f"*Written by `kht us-top` at the end of a run: {stamp}. It lists what was read. The rule of test G1 (`docs/13_round_six.md`) is applied by "
             "`scripts/us_top_score.py`, not here.*", "",
             f"- Run `{line['run']}`: {line['minutes']:.0f} minutes, {line['books']:,} readings of {line['markets']} markets, "
             f"{line['schedule_reads']} readings of the reward schedule, {line['errors']} errors.", "",
             "| Market | Programme | Pool a day | Target size | Readings |", "|---|---|---:|---:|---:|"]
    for slug, m in sorted(known.items()):
        lines.append(f"| `{slug}` | {m.get('program') or ''} | ${m.get('pool') or 0:,.0f} | {m.get('target') or 0:,.0f} | {per.get(slug, 0):,} |")
    return "\n".join(lines) + "\n"
