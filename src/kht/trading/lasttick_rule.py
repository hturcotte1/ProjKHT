"""The rule of test L1: which results are out of reach, and what is traded against.

docs/11_crypto_us.md, section 5. Used by the history script, by the scorer
of the live recorder, and by nothing that places an order.

    In the last minutes before a crypto market settles, on a result the
    price can no longer reach in the time left: sell "Yes" to the best bid
    where "Yes" will pay nothing, or buy "Yes" at the best offer where it
    will pay $1. Hold to settlement.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

THETA = 0.095            # taker fee coefficient of a small account
FIRST = 15 * 60          # a reading counts if taken between this long
LAST = 2 * 60            # and this long before the market's end
MAX_AGE = 10 * 60        # an index level older than this is not used
CAP = 2_000.0            # contracts a market, at most
SELL_AT_MOST = 0.05      # a sale above this, or a purchase below BUY_AT_LEAST, is refused: the book disagrees with the rule
BUY_AT_LEAST = 0.95


def load_reach(path: Path) -> dict[str, dict[int, float]]:
    """The reach table written by scripts/lasttick_reach.py: {coin: {minutes: largest move counted as possible}}."""
    raw = json.loads(Path(path).read_text())["reach"]
    return {coin: {int(h): float(v) for h, v in row.items()} for coin, row in raw.items()}


def reach_for(reach: dict[str, dict[int, float]], coin: str, minutes: float) -> float | None:
    """The reach for a horizon of ``minutes``, rounded up to a whole minute. None if the table does not go that far."""
    row = reach.get(coin)
    if not row or not math.isfinite(minutes):
        return None
    return row.get(max(1, math.ceil(minutes - 1e-9)))


def gap(market: dict[str, Any], level: float) -> tuple[float, str] | None:
    """How far the index is from changing this market's result, as a share of the index, and the result as things stand.

    Returns (gap, "yes" or "no"), or None if the market cannot be read: a
    kind this rule does not know, a missing level, or a "hit" market whose
    level has been reached already.
    """
    if not level or level <= 0:
        return None
    kind = market.get("kind")
    strike, lower, upper = _f(market.get("strike")), _f(market.get("lower")), _f(market.get("upper"))
    if kind == "above_below":
        if strike is None:
            return None
        return abs(level - strike) / level, ("yes" if level >= strike else "no")
    if kind == "range":
        edges = [e for e in (lower, upper) if e is not None]
        if not edges:
            return None
        inside = (lower is None or level >= lower) and (upper is None or level <= upper)
        return min(abs(level - e) for e in edges) / level, ("yes" if inside else "no")
    if kind == "one_touch":
        direction = market.get("direction")
        if strike is None or direction not in ("up", "down"):
            return None
        if (direction == "up" and level >= strike) or (direction == "down" and level <= strike):
            return None                                   # reached: it settles "Yes" whatever happens next
        return abs(strike - level) / level, "no"
    if kind == "up_down":
        start = _f(market.get("price_to_beat"))
        if start is None:
            return None
        return abs(level - start) / level, ("yes" if level >= start else "no")
    return None


def decide(market: dict[str, Any], book: dict[str, Any], ts: float, level: float | None, level_at: float | None,
           reach: dict[str, dict[int, float]]) -> tuple[dict[str, Any] | None, str]:
    """The trade the rule makes on one reading of one book, or None, and in a word why.

    ``book`` is a row of the recorder: bid1, bid_qty1, ask1, ask_qty1.
    """
    left = float(market["end"]) - ts
    if not LAST <= left <= FIRST:
        return None, "outside the time window"
    if level is None or level_at is None or ts - level_at > MAX_AGE or ts < level_at:
        return None, "no fresh index level"
    g = gap(market, level)
    if g is None:
        return None, "cannot be read"
    distance, result = g
    age = ts - level_at
    horizon = left / 60.0 + age / 60.0 + 1.0
    r = reach_for(reach, market.get("coin", ""), horizon)
    if r is None:
        return None, "no reach for this coin and horizon"
    if distance <= r:
        return None, "within reach"
    if result == "no":
        price, shown = _f(book.get("bid1")), _f(book.get("bid_qty1"))
        if price is None or not shown or shown <= 0:
            return None, "out of reach, nobody bidding"
        if price > SELL_AT_MOST + 1e-9:
            return None, "out of reach, but the book disagrees"
        side = "sell"
    else:
        price, shown = _f(book.get("ask1")), _f(book.get("ask_qty1"))
        if price is None or not shown or shown <= 0:
            return None, "out of reach, nobody offering"
        if price < BUY_AT_LEAST - 1e-9:
            return None, "out of reach, but the book disagrees"
        side = "buy"
    qty = min(shown, CAP)
    fee = THETA * price * (1.0 - price) * qty
    locked = qty * ((1.0 - price) if side == "sell" else price)
    premium = qty * (price if side == "sell" else 1.0 - price) - fee
    return {"slug": market["slug"], "coin": market.get("coin", ""), "kind": market.get("kind", ""), "horizon": market.get("horizon", ""), "end": float(market["end"]),
            "ts": ts, "left": left, "side": side, "price": price, "shown": shown, "qty": qty, "fee": fee, "locked": locked, "premium": premium,
            "gap": distance, "reach": r, "level": level, "age": age}, "trade"


def pnl(trade: dict[str, Any], settle: float) -> float:
    """What a trade made once its market settled at ``settle`` (what "Yes" paid: 0, 1, or between)."""
    q, p = trade["qty"], trade["price"]
    return (q * (p - settle) if trade["side"] == "sell" else q * (settle - p)) - trade["fee"]


def small_account(trades: list[dict[str, Any]], money: float = 10_000.0) -> list[dict[str, Any]]:
    """The trades an account with ``money`` to lock at each settlement time takes: in the order found, until it is used up."""
    out: list[dict[str, Any]] = []
    left: dict[float, float] = {}
    for t in sorted(trades, key=lambda x: (x["end"], x["ts"], x["slug"])):
        room = left.get(t["end"], money)
        if room <= 1e-9:
            continue
        share = min(1.0, room / t["locked"]) if t["locked"] > 0 else 1.0
        left[t["end"]] = room - t["locked"] * share
        out.append({**t, "qty": t["qty"] * share, "fee": t["fee"] * share, "locked": t["locked"] * share, "premium": t["premium"] * share})
    return out


def _f(x: Any) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None
