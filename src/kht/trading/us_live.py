"""UTR matches from a quarter of an hour before their listed start until their market closes.

docs/13_round_six.md, test D1. Read-only, public data, no key.

A tennis match seldom starts at the minute it is listed for. The people who
rest orders before a match take them away at the listed start. The people
who make prices during play come when play begins. Between the two the book
is nearly empty, the match is not being played, and a reward pool is
running. This writes down, every half minute and for every UTR match in
that stretch and through play:

* what the exchange's own public listing says of the match: whether it is
  being played, the set it is in, the score, and when that was last
  updated (the listing carries a live score from its data provider);
* the whole book of the market on who wins, with the running totals of
  trading.

Nothing is decided here. The rule of test D1 is applied afterwards, by
scripts/us_delay_score.py, to what this wrote down.

Files, under ``state/us-live/runs/<run>/``:

    books.csv.gz   every reading: the book as ``kht us-top`` writes it, and beside it the listed start, live or not, the period, the score
    markets.csv    each market read: its match, and the terms of its two reward periods (the six hours before the start, and play)
"""

from __future__ import annotations

import concurrent.futures as cf
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..api.polymarket_us import PolymarketUS
from .us_recorder import _append, _num
from .us_rewards import _when, _write, _write_gz
from .us_top import BOOK_FIELDS as TOP_BOOK_FIELDS
from .us_top import book_row

SERIES = ("utr",)                 # the tours followed: the first word of the match's name in the listing
TAG = "tennis"                    # the listing is asked for tennis only: six requests instead of fifty
PERIODS = {"day_of": "dayof", "live": "live"}     # the two reward periods kept, and what their columns are called
SWEEP = 30.0                      # seconds between two readings of one book: the public book is renewed every thirty
AHEAD = 900.0                     # a match is followed from this long before its listed start
AFTER = 120.0                     # and until this long after its market has stopped being open
LONGEST = 30 * 3600.0             # or this long after it was first read, whichever comes first (a suspended match can stay for days)
SCHEDULE_EVERY = 900              # seconds between two readings of the reward schedule
GIVE_UP = 20                      # readings in a row without a book after which a match is let go

BOOK_FIELDS = TOP_BOOK_FIELDS + ["start", "live", "period", "score", "state_t"]
MARKET_FIELDS = ["run", "slug", "event", "title", "first_seen", "start_first",
                 "dayof_program", "dayof_pool", "dayof_target", "dayof_discount", "dayof_max_spread",
                 "live_program", "live_pool", "live_target", "live_discount", "live_max_spread"]
LOG_FIELDS = ["run", "started", "ended", "minutes", "cycles", "listings", "schedule_reads", "books", "errors", "markets"]


def series_of(event_slug: str) -> str:
    return (event_slug or "").split("-", 1)[0]


def matches(listing: list[dict[str, Any]], series: tuple[str, ...] = SERIES) -> dict[str, dict[str, Any]]:
    """The matches of our tours in one reading of the listing, by the market on who wins: start, live or not, period, score."""
    found: dict[str, dict[str, Any]] = {}
    for ev in listing:
        slug = ev.get("slug") or ""
        if series_of(slug) not in series:
            continue
        state = ev.get("eventState") or {}
        for m in ev.get("markets") or []:
            ms = m.get("slug") or ""
            if not ms.endswith(slug) or m.get("closed"):          # the market on who wins is named after the match, behind the product's code
                continue
            found[ms] = {"event": slug, "title": ev.get("title") or "", "start": _when(ev.get("startTime") or ev.get("startDate")),
                         "live": bool(ev.get("live")), "period": str(ev.get("period") or ""), "score": str(ev.get("score") or ""),
                         "ended": bool(ev.get("ended")), "state_t": _when(state.get("updatedAt") or ev.get("updatedAt"))}
    return found


def reward_terms(schedule: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Each market's terms for the six hours before the start and for play, from one reading of the reward schedule."""
    out: dict[str, dict[str, Any]] = {}
    for m in schedule:
        slug = m.get("marketSlug") or ""
        row: dict[str, Any] = {}
        for tp in m.get("timePeriods") or []:
            name = PERIODS.get(tp.get("period") or "")
            if name is None or tp.get("status") != "active" or tp.get("programType") not in (None, "liquidityProgram"):
                continue
            row.update({f"{name}_program": tp.get("programId"), f"{name}_pool": _num(tp.get("rewardPool")), f"{name}_target": _num(tp.get("targetSize")),
                        f"{name}_discount": _num(tp.get("discountFactor")), f"{name}_max_spread": _num(tp.get("maxSpread"))})
        if slug and row:
            out[slug] = row
    return out


def run(state: Path, minutes: float, us: PolymarketUS | None = None, budget: float = 3.0, sweep: float = SWEEP, series: tuple[str, ...] = SERIES,
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
    known: dict[str, dict[str, Any]] = {}           # every market followed in this run
    last_state: dict[str, dict[str, Any]] = {}      # what the listing last said of each
    gone: dict[str, float] = {}                     # when a market was first seen not open
    done: set[str] = set()                          # followed to its end
    failed: dict[str, int] = {}                     # readings in a row that brought no book
    terms: dict[str, dict[str, Any]] = {}
    books: list[dict[str, Any]] = []
    counts = {"schedule": 0, "listings": 0, "errors": 0}
    scheduled_at = [-1e18]
    busy = [False]

    def read_schedule() -> None:
        try:
            found = reward_terms([m for m in us.iter_incentives(statuses=None) if series_of(str(m.get("marketSlug") or "").split("-", 1)[-1]) in series])
            with lock:
                terms.update(found)
                counts["schedule"] += 1
        except Exception:
            with lock:
                counts["errors"] += 1
        finally:
            busy[0] = False

    def flush() -> None:
        with lock:
            rows = [{"run": run_id, "slug": s, **m, **terms.get(s, {})} for s, m in known.items()]
        _write_gz(out / "books.csv.gz", BOOK_FIELDS, books)
        _write(out / "markets.csv", MARKET_FIELDS, rows)

    def one(slug: str) -> tuple[str, float, dict[str, Any] | None]:
        try:
            return slug, now(), us.book(slug)
        except Exception:
            return slug, now(), None

    cycles, flushed = 0, started
    while now() - started < minutes * 60.0 and (max_cycles is None or cycles < max_cycles):
        t = now()
        if t - scheduled_at[0] >= SCHEDULE_EVERY and not busy[0]:
            scheduled_at[0], busy[0] = t, True
            if background:
                threading.Thread(target=read_schedule, daemon=True).start()
            else:
                read_schedule()
        listed: dict[str, dict[str, Any]] | None
        try:
            listed = matches(list(us.iter_events(max_pages=30, closed=False, active=True, tagSlug=TAG)), series)
            counts["listings"] += 1
        except Exception:
            listed = None                           # the listing could not be read: the books are still read, and say that nothing is known of the match
            counts["errors"] += 1
        if listed is not None:
            for slug, m in listed.items():
                if slug in done or m["start"] is None:
                    continue
                if slug not in known and m["start"] - AHEAD <= t and not m["ended"]:
                    known[slug] = {"event": m["event"], "title": m["title"], "first_seen": round(t, 1), "start_first": m["start"]}
                if slug in known:
                    last_state[slug] = m
            for slug in known:
                if slug not in listed and slug in last_state:        # no longer listed as open: what was last said of it is no longer known to hold
                    last_state[slug] = {**last_state[slug], "live": "", "period": "", "score": "", "state_t": None, "unlisted": True}
        active = [s for s in known if s not in done]
        if active:
            with cf.ThreadPoolExecutor(max_workers=min(8, len(active))) as pool:
                for slug, ts, book in pool.map(one, active):
                    if not book:
                        counts["errors"] += 1
                        failed[slug] = failed.get(slug, 0) + 1
                        if failed[slug] >= GIVE_UP:      # ten minutes without a book: the market is gone, and asking on would only count errors
                            done.add(slug)
                        continue
                    failed.pop(slug, None)
                    try:
                        row = book_row(run_id, ts, slug, book)
                    except Exception:                # one odd book must not end the run
                        counts["errors"] += 1
                        continue
                    s = last_state.get(slug, {}) if listed is not None else {}
                    live = s.get("live", "")
                    row.update({"start": s.get("start"), "live": int(live) if isinstance(live, bool) else "", "period": s.get("period", ""), "score": s.get("score", ""),
                                "state_t": s.get("state_t")})
                    books.append(row)
                    if row["state"] != "OPEN":
                        gone.setdefault(slug, ts)
                    else:
                        gone.pop(slug, None)
                    if (slug in gone and ts - gone[slug] >= AFTER) or ts - known[slug]["first_seen"] >= LONGEST:
                        done.add(slug)
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
    line = {"run": run_id, "started": int(started), "ended": int(ended), "minutes": round((ended - started) / 60.0, 1), "cycles": cycles,
            "listings": counts["listings"], "schedule_reads": counts["schedule"], "books": len(books), "errors": counts["errors"], "markets": len(known)}
    _append(state / "log.csv", LOG_FIELDS, [line])
    (state / "STATUS.md").write_text(status_text(line, known, books))
    return line


def status_text(line: dict[str, Any], known: dict[str, dict[str, Any]], books: list[dict[str, Any]]) -> str:
    """A plain summary of one run. It lists what was read and scores nothing."""
    stamp = datetime.fromtimestamp(line["ended"], timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    waiting = sum(1 for b in books if b.get("period") == "NS" and b.get("start") and b["ts"] >= b["start"] and b["state"] == "OPEN")
    playing = sum(1 for b in books if b.get("live") == 1)
    return "\n".join([
        "# UTR matches around their start", "",
        f"*Written by `kht us-live` at the end of a run: {stamp}. It lists what was read. The rule of test D1 (`docs/13_round_six.md`) is applied by "
        "`scripts/us_delay_score.py`, not here.*", "",
        f"- Run `{line['run']}`: {line['minutes']:.0f} minutes, {line['books']:,} readings of {line['markets']} matches, {line['listings']:,} readings of the listing, "
        f"{line['schedule_reads']} of the reward schedule, {line['errors']} errors.",
        f"- Readings of a match past its listed start and still listed as not started: {waiting:,}. Readings of a match listed as being played: {playing:,}.",
    ]) + "\n"
