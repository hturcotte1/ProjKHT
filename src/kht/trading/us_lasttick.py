"""Crypto markets on Polymarket US in their last minutes: the books, with sizes.

docs/11_crypto_us.md, section 5 (test L1). Read-only, public data, no key.

This lists the open crypto markets, keeps the index level the exchange
itself publishes (every five-minute up-or-down market carries the index at
its start as its "price to beat"), and reads the book of every market that
settles within the next quarter of an hour.

Nothing is decided here. The rule of L1 is applied afterwards, by
scripts/us_lasttick_score.py, to what this wrote down. So the recorder can
stay the same while the test runs.

A second copy of it runs beside the first for test L2 (docs/11, section
12): only the brackets ("range" markets), from five and a half hours
before their end, every two minutes, into ``state/us-ladder``. It is the
same program with other settings. With the settings left alone it records
exactly what it did before they existed.

Files, under ``state/us-lasttick/runs/<run>/``:

    books.csv.gz   every reading of a followed book: three levels a side with sizes
    markets.csv    what each followed market asks: kind, level or bracket, end
    index.csv      the index level of each coin whenever a newer one was published
"""

from __future__ import annotations

import concurrent.futures as cf
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..api.polymarket_us import PolymarketUS
from .us_recorder import LEVELS, _amount, _append, parse_book
from .us_rewards import _when, _write, _write_gz

FOLLOW = 17 * 60          # a market's book is read from this long before its end
AFTER = 45                # until this long after it
LIST_QUIET = 300          # seconds between two listings when nothing ends soon
LIST_BUSY = 50            # and when something does: the index level has to stay fresh
SWEEP = 40.0              # seconds between two readings of one book, at least (the public book changes every 30)
SKIP = frozenset({"5m", "15m", "hourly"})     # horizons that are not followed: thousands a day, and no orders of the kind L1 trades
INDEX_FROM = frozenset({"5m", "15m", "1h", "1d"})   # up-or-down horizons whose price to beat is an index level
PREFIX = "ASSET_PRICE_MARKET_TYPE_"

BOOK_FIELDS = (["run", "ts", "slug", "left", "state", "tx"]
               + [f"{side}{part}{i}" for side in ("bid", "ask") for i in range(1, LEVELS + 1) for part in ("", "_qty")]
               + ["bid_levels", "ask_levels", "bid_total", "ask_total", "traded", "last", "open_interest"])
MARKET_FIELDS = ["run", "slug", "kind", "horizon", "coin", "index", "start", "end", "strike", "lower", "upper", "range_kind", "direction", "price_to_beat",
                 "first_seen"]
INDEX_FIELDS = ["run", "ts", "coin", "level", "at", "slug"]
LOG_FIELDS = ["run", "started", "ended", "minutes", "cycles", "listings", "books", "errors", "markets", "ends"]


def terms(market: dict[str, Any]) -> dict[str, Any] | None:
    """What one listed crypto market asks, as a flat row; None if it is not a price market with an end."""
    t = market.get("assetPriceTerms") or {}
    kind = str(t.get("marketType") or "")
    end = _when(t.get("windowEnd"))
    slug = market.get("slug")
    if not slug or not kind.startswith(PREFIX) or end is None:
        return None
    return {"slug": slug, "kind": kind[len(PREFIX):].lower(), "horizon": str(t.get("horizon") or ""),
            "coin": str((t.get("asset") or {}).get("symbol") or "").lower(), "index": str(t.get("indexSymbol") or ""),
            "start": _when(t.get("windowStart")), "end": end, "strike": _amount(t.get("strike")), "lower": _amount(t.get("rangeLower")),
            "upper": _amount(t.get("rangeUpper")), "range_kind": str(t.get("rangeKind") or "").replace("ASSET_PRICE_RANGE_KIND_", "").lower(),
            "direction": str(t.get("direction") or "").replace("ASSET_PRICE_DIRECTION_", "").lower(), "price_to_beat": _amount(t.get("priceToBeat"))}


def index_levels(markets: dict[str, dict[str, Any]], now: float) -> dict[str, dict[str, Any]]:
    """The newest index level the exchange has published for each coin: {coin: {level, at, slug}}.

    An up-or-down market's price to beat is the index at its start. Among
    the markets of a coin that have started, the one that started last has
    the newest level.
    """
    out: dict[str, dict[str, Any]] = {}
    for m in markets.values():
        if m["kind"] != "up_down" or m["horizon"] not in INDEX_FROM or m["price_to_beat"] is None or m["start"] is None or m["start"] > now:
            continue
        best = out.get(m["coin"])
        # of two markets that started together (5 and 15 minutes), either will do: they carry the same value
        if best is None or m["start"] > best["at"]:
            out[m["coin"]] = {"level": m["price_to_beat"], "at": m["start"], "slug": m["slug"]}
    return out


def followed(markets: dict[str, dict[str, Any]], now: float, lead: float = FOLLOW, kinds: frozenset[str] | None = None) -> list[str]:
    """The markets whose book is read now: those ending within ``lead`` seconds, until a little after their end.

    ``kinds`` narrows it to some kinds of market ("range", "above_below", "one_touch", "up_down"); None is all of them.
    """
    return sorted(s for s, m in markets.items()
                  if m["horizon"] not in SKIP and (kinds is None or m["kind"] in kinds) and m["end"] - lead <= now <= m["end"] + AFTER)


def book_row(run_id: str, ts: float, market: dict[str, Any], book: dict[str, Any]) -> dict[str, Any]:
    row = parse_book(book)
    row.update(run=run_id, ts=round(ts, 1), slug=market["slug"], left=round(market["end"] - ts, 1), tx=str(book.get("transactTime") or "")[:23])
    return row


def run(state: Path, minutes: float, us: PolymarketUS | None = None, budget: float = 5.0, workers: int = 8, follow: float = FOLLOW,
        now: Callable[[], float] = time.time, sleep: Callable[[float], None] = time.sleep, max_cycles: int | None = None,
        sweep: float = SWEEP, kinds: frozenset[str] | None = None) -> dict[str, Any]:
    """Record for ``minutes``: the books of crypto markets about to end, and the index levels published meanwhile.

    ``follow`` is how long before its end a market starts to be read,
    ``sweep`` the least time between two readings of one book, and
    ``kinds`` the kinds of market that are read (None: all). Test L1 uses
    the defaults. The copy that records whole ladders for test L2 follows
    longer, reads less often and reads brackets only.
    """
    if us is None:
        from ..api.http import Http

        us = PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": budget}))
    started = now()
    run_id = datetime.fromtimestamp(started, timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = state / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    markets: dict[str, dict[str, Any]] = {}
    seen: dict[str, dict[str, Any]] = {}            # followed markets, as first seen (and brought up to date)
    levels: dict[str, dict[str, Any]] = {}
    books: list[dict[str, Any]] = []
    index_rows: list[dict[str, Any]] = []
    listed_at, listings, cycles, errors, flushed = -1e18, 0, 0, 0, started
    was_active = False

    def flush() -> None:
        _write_gz(out / "books.csv.gz", BOOK_FIELDS, books)
        _write(out / "markets.csv", MARKET_FIELDS, [{"run": run_id, **m} for m in seen.values()])
        _write(out / "index.csv", INDEX_FIELDS, index_rows)

    def one(slug: str) -> tuple[str, float, dict[str, Any] | None]:
        try:
            return slug, now(), us.book(slug)
        except Exception:
            return slug, now(), None

    while now() - started < minutes * 60.0 and (max_cycles is None or cycles < max_cycles):
        t = now()
        soon = any(m["horizon"] not in SKIP and (kinds is None or m["kind"] in kinds) and m["end"] - follow - LIST_QUIET <= t <= m["end"] + AFTER
                   for m in markets.values())
        if t - listed_at >= (LIST_BUSY if soon else LIST_QUIET):
            try:
                fresh = {}
                for raw in us.iter_markets(closed=False, categories="crypto"):
                    m = terms(raw)
                    if m is not None:
                        fresh[m["slug"]] = m
                # a market that has ended drops out of the list of open ones; it is kept until it is no longer read
                markets = {**{s: m for s, m in markets.items() if t <= m["end"] + AFTER}, **fresh}
                listed_at, listings = t, listings + 1
                for coin, lv in index_levels(markets, t).items():
                    if levels.get(coin, {}).get("at") != lv["at"]:
                        levels[coin] = lv
                        index_rows.append({"run": run_id, "ts": round(t, 1), "coin": coin, **lv})
            except Exception:
                errors += 1
        active = followed(markets, t, follow, kinds)
        for slug in active:
            if slug not in seen:
                seen[slug] = {**markets[slug], "first_seen": round(t, 1)}
            elif markets[slug].get("price_to_beat") is not None:
                seen[slug]["price_to_beat"] = markets[slug]["price_to_beat"]
        if active:
            with cf.ThreadPoolExecutor(max_workers=workers) as pool:
                for slug, ts, book in pool.map(one, active):
                    if not book:
                        errors += 1
                        continue
                    try:
                        books.append(book_row(run_id, ts, markets[slug], book))
                    except Exception:                    # one odd book must not end the run
                        errors += 1
        cycles += 1
        # written every ten minutes, and at once when the markets being followed have all ended:
        # a settlement that has been read should not wait in memory for the machine to last
        if now() - flushed >= 600 or (was_active and not active):
            flush()
            flushed = now()
        was_active = bool(active)
        pause = (max(sweep, len(active) / budget) if active else 20.0) - (now() - t)
        if pause > 0 and now() - started + pause < minutes * 60.0:
            sleep(pause)
        elif pause > 0:
            break
    flush()
    ended = now()
    line = {"run": run_id, "started": int(started), "ended": int(ended), "minutes": round((ended - started) / 60.0, 1), "cycles": cycles, "listings": listings,
            "books": len(books), "errors": errors, "markets": len(seen), "ends": len({m["end"] for m in seen.values()})}
    _append(state / "log.csv", LOG_FIELDS, [line])
    plain = kinds is None and follow == FOLLOW
    (state / "STATUS.md").write_text(status_text(line, seen, books, levels, None if plain else
                                                 f"only {', '.join(sorted(kinds)) if kinds else 'every kind of'} markets, "
                                                 f"from {follow / 60:.0f} minutes before their end"))
    return line


def status_text(line: dict[str, Any], seen: dict[str, dict[str, Any]], books: list[dict[str, Any]], levels: dict[str, dict[str, Any]],
                settings: str | None = None) -> str:
    """A plain summary of one run. It describes what was read; it scores nothing.

    ``settings`` says what a copy run with other settings than L1's was reading.
    """
    stamp = datetime.fromtimestamp(line["ended"], timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    kinds = Counter(f"{m['coin']} {m['kind'].replace('_', ' ')} ({m['horizon']})" for m in seen.values())
    last: dict[str, dict[str, Any]] = {}
    for b in books:                                         # the last reading of each market before its end
        if b["left"] >= 0:
            last[b["slug"]] = b
    low = [b for b in last.values() if b.get("bid1") is not None and b["bid1"] <= 0.011]
    high = [b for b in last.values() if b.get("ask1") is not None and b["ask1"] >= 0.989]
    head = (["# Crypto markets in their last minutes", "",
             f"*Written by `kht us-lasttick` at the end of a run: {stamp}. It lists what was read. The rule of `docs/11_crypto_us.md` is applied by "
             "`scripts/us_lasttick_score.py`, not here.*", ""] if settings is None else
            ["# Crypto ladders before they settle", "",
             f"*Written by `kht us-lasttick` at the end of a run: {stamp}. This copy of the recorder read {settings}. It lists what was read. "
             "The rule of `docs/11_crypto_us.md`, section 12, is applied by `scripts/us_ladder_score.py`, not here.*", ""])
    lines = head + [
             f"- Run `{line['run']}`: {line['minutes']:.0f} minutes, {line['listings']} listings, {line['books']:,} readings of {line['markets']:,} markets "
             f"ending at {line['ends']} different times, {line['errors']} errors.",
             f"- At the last reading before their end, {len(low):,} markets had a best bid of 1¢ ({sum(b['bid_qty1'] or 0 for b in low):,.0f} contracts) "
             f"and {len(high):,} a best offer of 99¢ ({sum(b['ask_qty1'] or 0 for b in high):,.0f} contracts). "
             "This counts every such market, near the price or far from it.",
             "- Index levels last published: " + (", ".join(f"{c.upper()} {v['level']:,.4f}".rstrip("0").rstrip(".") for c, v in sorted(levels.items())) or "none") + ".",
             "", "| Markets followed | Number |", "|---|---:|"]
    lines += [f"| {k} | {n:,} |" for k, n in sorted(kinds.items())]
    return "\n".join(lines) + "\n"
