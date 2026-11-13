"""The rule of test L3: selling far brackets while the bids are there.

docs/11_crypto_us.md, section 13. Used by the scorer of the second
recorder and by nothing that places an order.

    Hours before a ladder of price brackets settles, on a bracket the
    price is not expected to end in: sell "Yes" to the best bid, and hold
    to settlement. Of all the brackets of one ladder at most one can pay.

It is L1's rule with three things changed, and it takes the rest from
``lasttick_rule`` without touching it: brackets only, a window of hours
and not minutes, and a yardstick made from where the price has ended
rather than from how far it went on the way.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from . import lasttick_rule as l1

THETA = l1.THETA                 # taker fee coefficient of a small account
FIRST = 330 * 60                 # a reading counts if taken between this long
LAST = 2 * 60                    # and this long before the bracket's end
MAX_AGE = l1.MAX_AGE             # an index level older than this is not used
CAP = l1.CAP                     # contracts a bracket, at most
SELL_AT_MOST = l1.SELL_AT_MOST   # a bid above this is not sold to: the book disagrees with the rule
STEP = 5                         # the reach is tabled every five minutes; a time ahead is rounded up to the next figure
HORIZONS = ("daily", "weekly")   # the ladders the test is about


def load(path: Path) -> tuple[dict[str, dict[int, float]], dict[str, float]]:
    """The reach table written by scripts/lasthours_reach.py, and the brake that goes with it."""
    raw = json.loads(Path(path).read_text())
    return {coin: {int(h): float(v) for h, v in row.items()} for coin, row in raw["reach"].items()}, {c: float(v) for c, v in raw["brake"].items()}


def reach_for(reach: dict[str, dict[int, float]], coin: str, minutes: float) -> float | None:
    """The reach for a time ahead of ``minutes``, rounded up to the next figure in the table. None if the table does not go that far."""
    h = max(STEP, int(math.ceil(minutes / STEP - 1e-9)) * STEP)
    return reach.get(coin, {}).get(h)


def decide(market: dict[str, Any], book: dict[str, Any], ts: float, level: float | None, level_at: float | None,
           reach: dict[str, dict[int, float]], brake: dict[str, float] | None = None,
           history: list[tuple[float, float]] | None = None) -> tuple[dict[str, Any] | None, str]:
    """The sale the rule makes on one reading of one bracket's book, or None, and in a word why."""
    if market.get("kind") != "range" or market.get("horizon") not in HORIZONS:
        return None, "not a bracket of a daily or weekly ladder"
    left = float(market["end"]) - ts
    if not LAST <= left <= FIRST:
        return None, "outside the time window"
    if level is None or level_at is None or ts - level_at > MAX_AGE or ts < level_at:
        return None, "no fresh index level"
    g = l1.gap(market, level)
    if g is None:
        return None, "cannot be read"
    distance, result = g
    if result == "yes":
        return None, "the index is in this bracket"
    age = ts - level_at
    ahead = left / 60.0 + age / 60.0 + 1.0
    r = reach_for(reach, market.get("coin", ""), ahead)
    if r is None:
        return None, "no reach for this coin and time ahead"
    if distance <= r:
        return None, "not far enough"
    if brake is not None:
        state = l1.brake_state(history, ts, brake.get(market.get("coin", "")))
        if state == "fast":
            return None, "far enough, but the index has been moving fast"
        if state == "unknown":
            return None, "far enough, too little index history"
    price, shown = l1._f(book.get("bid1")), l1._f(book.get("bid_qty1"))
    if price is None or not shown or shown <= 0:
        return None, "far enough, nobody bidding"
    if price > SELL_AT_MOST + 1e-9:
        return None, "far enough, but the book disagrees"
    qty = min(shown, CAP)
    fee = THETA * price * (1.0 - price) * qty
    return {"slug": market["slug"], "coin": market.get("coin", ""), "kind": "range", "horizon": market.get("horizon", ""), "end": float(market["end"]),
            "ts": ts, "left": left, "side": "sell", "price": price, "shown": shown, "qty": qty, "fee": fee, "locked": qty * (1.0 - price),
            "premium": qty * price - fee, "gap": distance, "reach": r, "ahead": ahead, "level": level, "age": age}, "trade"


pnl = l1.pnl                      # what a sale made once its bracket settled
small_account = l1.small_account  # the sales an account with a fixed sum for each settlement time takes, in the order found
