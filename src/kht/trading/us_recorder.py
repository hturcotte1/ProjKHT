"""Record what could really be bought on Polymarket US, cycle by cycle.

Polymarket US publishes no trades, and its price history cannot be trusted
for a backtest: it has no sizes, and for an empty side of a book it shows the
last trade as if it were a quote (docs/06_polymarket_us.md, section 7). The
only evidence about that exchange worth having is its live order books. So
every cycle this reads them and writes them down:

* the three best prices on each side, with sizes, of every open market
  outside sports and crypto that shows any quote;
* for each market whose question also trades on polymarket.com
  (``kht.trading.twins``), the best bid and ask there at the same moment.

Nothing is traded and no key is used: both exchanges serve this publicly.
Any rule can be scored later against what was actually on offer, and the
gap between the two exchanges can be followed from snapshot to snapshot.

Files, under the state directory:

    snapshots/YYYY-MM-DD/HHMMSS.csv.gz   one row per market per cycle
    markets.csv                          what each US market is (appended to, never rewritten)
    twins.csv                            its twin on polymarket.com, if any (appended to)
    rewards.csv                          one line per reward programme per cycle: how many books would be paid
    schedule_fields.csv                  every field the reward schedule carries, per cycle: a new one means the rules have changed
    log.csv                              one line per cycle
    STATUS.md                            the latest cycle in words

It also reads the exchange's public schedule of rewards for resting orders
and notes, for each book, whether it would be paid that second and how much
score there is to share (docs/08_rewards.md).

Only the standard library and ``requests`` are used.
"""

from __future__ import annotations

import concurrent.futures as cf
import csv
import gzip
import io
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..api.polymarket import Polymarket, best_bid_ask
from ..api.polymarket_us import PolymarketUS, taker_fee_per_share
from .twins import Twin, pair_all

CATEGORIES = ("politics", "culture", "macro", "technology", "climate", "finance", "geopolitics", "science")
LEVELS = 3

REWARD_CATEGORIES = {"POL", "CUL", "MAC", "TECH", "CLI", "FIN", "GEO", "SCI"}       # as the reward schedule names them
REWARD_FIELDS = ["rw_program", "rw_pool", "rw_target", "rw_bid_at", "rw_ask_at", "rw_bid_score", "rw_ask_score", "rw_bid_ok", "rw_ask_ok"]
SNAPSHOT_FIELDS = (["ts", "slug"]
                   + [f"{side}{part}{i}" for side in ("bid", "ask") for i in range(1, LEVELS + 1) for part in ("", "_qty")]
                   + ["bid_levels", "ask_levels", "bid_total", "ask_total", "last", "last_qty", "last_ts", "traded", "open_interest", "state",
                      "intl_id", "intl_bid", "intl_bid_qty", "intl_ask", "intl_ask_qty", "intl_last"] + REWARD_FIELDS)
PROGRAMME_FIELDS = ["ts", "program", "period", "pool", "target", "discount", "max_spread", "markets", "books", "bid_sides_paid", "ask_sides_paid",
                    "markets_paid_both", "events", "events_with_none"]
MARKET_FIELDS = ["slug", "market_id", "category", "subcategory", "market_type", "event_id", "event_title", "label", "question", "end_date",
                 "tick", "fee_theta", "first_seen"]
TWIN_FIELDS = ["slug", "intl_id", "token_yes", "condition", "rule", "intl_event_id", "intl_label", "intl_question", "neg_risk", "first_seen"]
LOG_FIELDS = ["ts", "markets_open", "markets_quoted", "books_read", "two_sided", "twins", "twins_both_books", "us_cheaper_yes", "us_cheaper_no",
              "seconds", "errors"]


def _amount(x: Any) -> float | None:
    try:
        return float((x or {}).get("value"))
    except (AttributeError, TypeError, ValueError):
        return None


def _num(x: Any) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def book_sides(book: dict[str, Any]) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """(price, size) levels of one book, best first: bids, then offers. Empty levels are dropped."""
    def side(key: str, best_first_desc: bool) -> list[tuple[float, float]]:
        out = []
        for lvl in book.get(key) or []:
            px, qty = _amount(lvl.get("px")), _num(lvl.get("qty"))
            if px is not None and qty is not None and qty > 0:
                out.append((px, qty))
        return sorted(out, reverse=best_first_desc)

    return side("bids", True), side("offers", False)


def reward_walk(levels: list[tuple[float, float]], target: float, discount: float, tick: float = 0.01) -> tuple[float | None, float]:
    """One side of a book as the liquidity programme scores it (docs.polymarket.us/incentives/liquidity).

    The exchange walks from the best price outwards, adding up resting size
    until the target size is reached. Every order inside that range scores
    discount ** (ticks from the best price) * size; orders beyond it score
    nothing. Returns the price at which the target was reached (None if the
    whole side is smaller than the target, in which case it is not paid)
    and the side's total score.
    """
    if not levels:
        return None, 0.0
    best, cum, score = levels[0][0], 0.0, 0.0
    for px, qty in levels:
        score += discount ** round(abs(px - best) / tick) * qty
        cum += qty
        if cum >= target - 1e-9:
            return px, score
    return None, score


def reward_state(book: dict[str, Any], prog: dict[str, Any], tick: float = 0.01) -> dict[str, Any]:
    """Whether each side of this book would be paid this second, and how much score there is to share.

    A programme with a maximum spread pays a second only if both sides reach
    the target and the two prices at which they reach it are no further
    apart than twice that spread. A programme without one pays each side on
    its own.
    """
    bids, asks = book_sides(book)
    target, discount, max_spread = float(prog["target"]), float(prog["discount"]), prog.get("max_spread")
    bid_at, bid_score = reward_walk(bids, target, discount, tick)
    ask_at, ask_score = reward_walk(asks, target, discount, tick)
    if max_spread is not None:
        ok = bid_at is not None and ask_at is not None and (ask_at - bid_at) <= 2.0 * float(max_spread) + 1e-9
        bid_ok = ask_ok = ok
    else:
        bid_ok, ask_ok = bid_at is not None, ask_at is not None
    return {"rw_program": prog["program"], "rw_pool": prog["pool"], "rw_target": target, "rw_bid_at": bid_at, "rw_ask_at": ask_at,
            "rw_bid_score": round(bid_score, 2), "rw_ask_score": round(ask_score, 2), "rw_bid_ok": int(bid_ok), "rw_ask_ok": int(ask_ok)}


KNOWN_PERIOD_FIELDS = {"programId", "programType", "start", "end", "rewardPool", "status", "discountFactor", "targetSize", "period", "createdAt",
                       "maxSpread", "minTakerNotional"}
FIELD_FIELDS = ["ts", "field", "periods", "known", "examples"]


def schedule_fields(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every field the reward schedule carries on a time period, how often, and whether it was there on 11 November 2026.

    The exchange has filed amended rules, in force from 18 November 2026,
    under which a reward may be capped at a share of what the account itself
    trades, or need a minimum of trading (docs/09_sports_rewards.md,
    section 9). When such a parameter is published it will appear as a
    field not seen before, and this is where it will be noticed.
    """
    count: dict[str, int] = {}
    examples: dict[str, list[str]] = {}
    for p in entries:
        for tp in p.get("timePeriods") or []:
            for key, value in tp.items():
                count[key] = count.get(key, 0) + 1
                if key not in KNOWN_PERIOD_FIELDS and len(examples.setdefault(key, [])) < 5:
                    examples[key].append(f"{tp.get('programId')}={value}")
    return [{"field": k, "periods": n, "known": int(k in KNOWN_PERIOD_FIELDS), "examples": "; ".join(examples.get(k, []))} for k, n in sorted(count.items())]


def reward_schedule(us: PolymarketUS, fields: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    """The active liquidity programme of each market outside sports and crypto, by market slug.

    If ``fields`` is given, the summary of ``schedule_fields`` is added to it.
    """
    out: dict[str, dict[str, Any]] = {}
    entries = list(us.iter_incentives())
    if fields is not None:
        fields.extend(schedule_fields(entries))
    for p in entries:
        if p.get("category") not in REWARD_CATEGORIES or not p.get("marketSlug"):
            continue
        for tp in p.get("timePeriods") or []:
            if tp.get("status") == "active" and tp.get("programType") == "liquidityProgram" and tp.get("targetSize") and tp.get("discountFactor") is not None:
                out[p["marketSlug"]] = {"program": tp.get("programId"), "period": tp.get("period"), "pool": _num(tp.get("rewardPool")) or 0.0,
                                        "target": float(tp["targetSize"]), "discount": float(tp["discountFactor"]), "max_spread": _num(tp.get("maxSpread"))}
                break
    return out


def parse_book(book: dict[str, Any]) -> dict[str, Any]:
    """The top of one Polymarket US book as a flat row (prices of "Yes"; sizes in contracts)."""
    bids, asks = book_sides(book)
    stats = book.get("stats") or {}
    row: dict[str, Any] = {"bid_levels": len(bids), "ask_levels": len(asks),
                           "bid_total": round(sum(q for _, q in bids), 2), "ask_total": round(sum(q for _, q in asks), 2)}
    for name, levels in (("bid", bids), ("ask", asks)):
        for i in range(LEVELS):
            px, qty = levels[i] if i < len(levels) else (None, None)
            row[f"{name}{i + 1}"] = px
            row[f"{name}_qty{i + 1}"] = qty
    row.update(last=_amount(stats.get("lastTradePx")), last_qty=_num(stats.get("lastTradeQty")), last_ts=(stats.get("lastTradeSetTime") or "")[:19],
               traded=_num(stats.get("sharesTraded")), open_interest=_num(stats.get("openInterest")),
               state=str(book.get("state") or "").replace("MARKET_STATE_", ""))
    return row


def gaps(row: dict[str, Any], theta: float = 0.095) -> tuple[float | None, float | None]:
    """How far the US book sits beyond the polymarket.com book, after the US taker fee.

    First value: buying "Yes" on US at its ask costs this much less than the
    polymarket.com bid. Second: buying "No" on US (selling "Yes" at the US
    bid) costs this much less than "No" at the polymarket.com ask. Positive
    means the US price is the cheaper one by more than the fee. None if a
    needed quote is missing.
    """
    a, b, ib, ia = row.get("ask1"), row.get("bid1"), row.get("intl_bid"), row.get("intl_ask")
    yes = None if a is None or ib is None else ib - a - taker_fee_per_share(a, theta)
    no = None if b is None or ia is None else b - ia - taker_fee_per_share(b, theta)
    return yes, no


def _append(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    new = not path.exists()
    with path.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerows(rows)


def _known(path: Path, key: str) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="") as fh:
        return {r[key] for r in csv.DictReader(fh)}


def record(state: Path, us: PolymarketUS | None = None, intl: Polymarket | None = None, now: float | None = None,
           with_twins: bool = True, workers: int = 6, max_books: int | None = None) -> dict[str, Any]:
    """Run one recording cycle and return its log line."""
    us = us or PolymarketUS()
    t0 = time.time()
    now = float(now if now is not None else t0)
    stamp = datetime.fromtimestamp(now, tz=timezone.utc)
    state.mkdir(parents=True, exist_ok=True)
    errors = 0

    # ---- what is open on Polymarket US
    events: dict[str, dict[str, Any]] = {}
    markets: dict[str, tuple[dict[str, Any], dict[str, Any] | None]] = {}
    for cat in CATEGORIES:
        for e in us.iter_events(closed=False, categories=cat, orderBy="id", orderDirection="asc"):
            events[str(e.get("id"))] = e
            for m in e.get("markets") or []:
                if m.get("slug"):
                    markets[m["slug"]] = (m, e)
        for m in us.iter_markets(closed=False, categories=cat, orderBy="id", orderDirection="asc"):
            if m.get("slug") and m["slug"] not in markets:
                markets[m["slug"]] = (m, None)
    quoted = [s for s, (m, _) in markets.items() if _amount(m.get("bestBidQuote")) is not None or _amount(m.get("bestAskQuote")) is not None]
    if max_books is not None:
        quoted = quoted[:max_books]

    # ---- which of them carry a reward for resting orders
    schedule: dict[str, dict[str, Any]] = {}
    fields: list[dict[str, Any]] = []
    try:
        schedule = reward_schedule(us, fields)
    except Exception:                                       # the schedule is extra; the books are the point
        errors += 1

    # ---- their order books
    def one(slug: str) -> tuple[str, dict[str, Any] | None]:
        try:
            book = us.book(slug)
            row = parse_book(book)
            prog = schedule.get(slug)
            if prog is not None:
                row.update(reward_state(book, prog, _num(markets[slug][0].get("orderPriceMinTickSize")) or 0.01))
            return slug, row
        except Exception:                                   # a market that closed in the meantime; counted, not fatal
            return slug, None

    rows: dict[str, dict[str, Any]] = {}
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        for slug, row in pool.map(one, quoted):
            if row is None:
                errors += 1
            elif row["bid_levels"] or row["ask_levels"]:
                rows[slug] = {"ts": int(now), "slug": slug, **row}

    # ---- the same questions on polymarket.com
    twins: dict[str, Twin] = {}
    if with_twins and rows:
        try:
            intl = intl or Polymarket()
            intl_events = [e for e in intl.iter_events(closed=False, active=True)]
            twins = pair_all([e for e in events.values()], intl_events)
            last = {str(m.get("id")): _num(m.get("lastTradePrice")) for e in intl_events for m in e.get("markets") or []}
            wanted = {s: tw for s, tw in twins.items() if s in rows}
            books = {}
            tokens = sorted({tw.token_yes for tw in wanted.values()})
            for b in intl.books(tokens):
                if isinstance(b, dict) and b.get("asset_id"):
                    books[str(b["asset_id"])] = b
            for slug, tw in wanted.items():
                row = rows[slug]
                row["intl_id"], row["intl_last"] = tw.intl_id, last.get(tw.intl_id)
                b = books.get(tw.token_yes)
                if b is not None:
                    bid, ask, bid_qty, ask_qty = best_bid_ask(b)
                    row.update(intl_bid=bid, intl_bid_qty=bid_qty if bid is not None else None, intl_ask=ask, intl_ask_qty=ask_qty if ask is not None else None)
        except Exception:                                   # polymarket.com unreachable: the US books are still worth keeping
            errors += 1

    # ---- write
    day = state / "snapshots" / stamp.strftime("%Y-%m-%d")
    day.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=SNAPSHOT_FIELDS, extrasaction="ignore")
    w.writeheader()
    for slug in sorted(rows):
        w.writerow({k: ("" if v is None else v) for k, v in rows[slug].items()})
    with gzip.open(day / f"{stamp.strftime('%H%M%S')}.csv.gz", "wt", newline="") as fh:
        fh.write(buf.getvalue())

    seen = _known(state / "markets.csv", "slug")
    fresh = []
    for slug in sorted(rows):
        if slug in seen:
            continue
        m, e = markets[slug]
        fresh.append({"slug": slug, "market_id": m.get("id"), "category": m.get("category"), "subcategory": m.get("eventSubcategory"),
                      "market_type": m.get("marketType"), "event_id": (e or {}).get("id"), "event_title": (e or {}).get("title"),
                      "label": m.get("title"), "question": m.get("question"), "end_date": m.get("endDate"), "tick": m.get("orderPriceMinTickSize"),
                      "fee_theta": m.get("feeCoefficient"), "first_seen": int(now)})
    _append(state / "markets.csv", MARKET_FIELDS, fresh)
    seen_twins = _known(state / "twins.csv", "slug")
    _append(state / "twins.csv", TWIN_FIELDS, [
        {"slug": s, "intl_id": tw.intl_id, "token_yes": tw.token_yes, "condition": tw.condition, "rule": tw.rule, "intl_event_id": tw.intl_event_id,
         "intl_label": tw.intl_label, "intl_question": tw.intl_question, "neg_risk": int(tw.neg_risk), "first_seen": int(now)}
        for s, tw in sorted(twins.items()) if s in rows and s not in seen_twins])

    two_sided = sum(1 for r in rows.values() if r["bid1"] is not None and r["ask1"] is not None)
    both = [r for r in rows.values() if r.get("intl_bid") is not None and r.get("intl_ask") is not None]
    cheap = []
    for r in both:
        m, _ = markets[r["slug"]]
        theta = _num(m.get("feeCoefficient")) or 0.095
        yes, no = gaps(r, theta)
        if yes is not None and yes > 0:
            cheap.append(("Yes", yes, r["ask1"], r["ask_qty1"], r))
        if no is not None and no > 0:
            cheap.append(("No", no, 1.0 - r["bid1"], r["bid_qty1"], r))
    line = {"ts": int(now), "markets_open": len(markets), "markets_quoted": len(quoted), "books_read": len(rows), "two_sided": two_sided,
            "twins": sum(1 for s in twins if s in rows), "twins_both_books": len(both),
            "us_cheaper_yes": sum(1 for c in cheap if c[0] == "Yes"), "us_cheaper_no": sum(1 for c in cheap if c[0] == "No"),
            "seconds": round(time.time() - t0, 1), "errors": errors}
    _append(state / "log.csv", LOG_FIELDS, [line])
    programmes = programme_rows(int(now), schedule, rows, markets)
    _append(state / "rewards.csv", PROGRAMME_FIELDS, programmes)
    _append(state / "schedule_fields.csv", FIELD_FIELDS, [{"ts": int(now), **f} for f in fields])
    new = [f for f in fields if not f["known"]]
    notice = ""
    if new:
        notice = ("\n## The reward schedule carries fields that were not there on 11 November 2026\n\n"
                  "The exchange's amended rules, in force from 18 November 2026, allow a reward to be capped at a share of what an account itself "
                  "trades (docs/09_sports_rewards.md, section 9). Look at these before trusting any reward figure:\n\n"
                  + "\n".join(f"- `{f['field']}` on {f['periods']:,} time periods, for example {f['examples']}" for f in new) + "\n")
    (state / "STATUS.md").write_text(status_text(stamp, line, cheap, markets) + rewards_text(programmes) + notice)
    return line


def programme_rows(ts: int, schedule: dict[str, dict[str, Any]], rows: dict[str, dict[str, Any]],
                   markets: dict[str, tuple[dict[str, Any], dict[str, Any] | None]]) -> list[dict[str, Any]]:
    """One line per reward programme: how many of its markets' books would be paid this second."""
    by: dict[str, dict[str, Any]] = {}
    for slug, prog in schedule.items():
        g = by.setdefault(prog["program"], {"ts": ts, "program": prog["program"], "period": prog["period"], "pool": prog["pool"], "target": prog["target"],
                                            "discount": prog["discount"], "max_spread": prog["max_spread"], "markets": 0, "books": 0, "bid_sides_paid": 0,
                                            "ask_sides_paid": 0, "markets_paid_both": 0, "_events": {}})
        g["markets"] += 1
        # a market the event listing did not return is grouped with its neighbours by the slug without its last part (the answer)
        event = str((markets.get(slug, (None, None))[1] or {}).get("id") or slug.rsplit("-", 1)[0])
        paid = g["_events"].setdefault(event, 0)
        r = rows.get(slug)
        if r is not None and "rw_bid_ok" in r:
            g["books"] += 1
            g["bid_sides_paid"] += r["rw_bid_ok"]
            g["ask_sides_paid"] += r["rw_ask_ok"]
            g["markets_paid_both"] += int(r["rw_bid_ok"] and r["rw_ask_ok"])
            g["_events"][event] = paid + r["rw_bid_ok"] + r["rw_ask_ok"]
    out = []
    for g in by.values():
        events = g.pop("_events")
        g["events"], g["events_with_none"] = len(events), sum(1 for v in events.values() if v == 0)
        out.append(g)
    return sorted(out, key=lambda g: -g["pool"])


def rewards_text(programmes: list[dict[str, Any]]) -> str:
    if not programmes:
        return ""
    out = ["", "## Rewards for resting orders", "",
           "Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its "
           "markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, "
           "close together. This is how many would have been paid at the moment of this cycle.", "",
           "| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for g in programmes:
        spread = "none" if g["max_spread"] is None else f"{100 * g['max_spread']:g}c"
        out.append(f"| {g['program']} ({g['period']}) | ${g['pool']:,.0f} | {g['target']:,.0f} | {spread} | {g['markets']:,} | {g['bid_sides_paid']:,} "
                   f"| {g['ask_sides_paid']:,} | {g['events_with_none']:,} of {g['events']:,} |")
    return "\n".join(out) + "\n"


def status_text(stamp: datetime, line: dict[str, Any], cheap: list[tuple[str, float, float, float, dict[str, Any]]],
                markets: dict[str, tuple[dict[str, Any], dict[str, Any] | None]]) -> str:
    out = [f"# Polymarket US recorder: {stamp.strftime('%Y-%m-%d %H:%M')} UTC", "",
           "Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.", "",
           f"- open markets outside sports and crypto: {line['markets_open']:,}; showing any quote: {line['markets_quoted']:,}",
           f"- order books recorded: {line['books_read']:,}, of which {line['two_sided']:,} have orders on both sides",
           f"- recorded markets with a twin on polymarket.com: {line['twins']:,}; with a two-sided book there too: {line['twins_both_books']:,}",
           f"- twins where the US price is the cheaper one by more than the US fee: {line['us_cheaper_yes'] + line['us_cheaper_no']:,} "
           f"({line['us_cheaper_yes']:,} on the \"Yes\" side, {line['us_cheaper_no']:,} on the \"No\" side)",
           f"- took {line['seconds']:.0f} seconds; {line['errors']} errors", ""]
    if cheap:
        cost = sum(px * qty for _, _, px, qty, _ in cheap if qty)
        worth = sum(gap * qty for _, gap, _, qty, _ in cheap if qty)
        out += [f"Taking every one of these at the best US price would cost ${cost:,.0f}, and the gaps add up to ${worth:,.2f}. "
                "A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); "
                "they are recorded for the forward test fixed there.", "",
                "The 25 largest by what the gap is worth at the size on offer:", "",
                "| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |",
                "|---|---:|---:|---:|---:|---:|---|"]
        for side, gap, px, qty, r in sorted(cheap, key=lambda c: -c[1] * (c[3] or 0.0))[:25]:
            m, e = markets[r["slug"]]
            name = f"{(e or {}).get('title') or m.get('question') or ''}: {m.get('title') or ''}".strip(": ")
            size = f"{qty:,.0f}" if qty >= 10 else f"{qty:.2f}"
            out.append(f"| {side} | {100 * px:.1f}c | {size} | {100 * r['intl_bid']:.1f}c / {100 * r['intl_ask']:.1f}c | {100 * gap:.1f}c "
                       f"| ${gap * qty:,.2f} | {name[:90]} |")
    return "\n".join(out) + "\n"
