"""The rule of test G1: small orders at the best prices of a single-market reward programme.

docs/13_round_six.md, section 4. Used by the scorer of ``kht us-top`` and by
nothing that places an order.

    While other people's orders make a book qualify for its reward, rest a
    small order at the best bid and one at the best offer. Never improve a
    price, never hold more than the order size either way.

Everything here works on one reading of one book: the two sides as lists of
(price, size), best first, as ``us_top.decode`` returns them.
"""

from __future__ import annotations

from typing import Any

TICK = 0.01
MAX_SPREAD_TICKS = 3      # best bid and best offer further apart than this: there is no market to stand in
SIZES = (25, 50, 100, 250, 500)
JUDGED = 100
MAX_CREDIT = 60.0         # seconds of reward one reading can stand for, at most
EPS = 1e-9

Side = list[tuple[float, float]]


def ticks(a: float, b: float, tick: float = TICK) -> int:
    return int(round(abs(a - b) / tick))


def reaches(levels: Side, target: float) -> float | None:
    """The price at which a side's size, added up from the best price, reaches the target; None if it never does."""
    cum = 0.0
    for px, qty in levels:
        cum += qty
        if cum >= target - EPS:
            return px
    return None


def qualifies(bids: Side, asks: Side, target: float, max_spread: float | None) -> bool:
    """Whether a book is paid at this moment, as the filed rules test it.

    Each side must hold the target size. Where the programme has a maximum
    spread, the two prices at which the sides reach the target may be at
    most twice that spread apart.
    """
    b, a = reaches(bids, target), reaches(asks, target)
    if b is None or a is None:
        return False
    return max_spread is None or (a - b) <= 2.0 * max_spread + EPS


def with_order(levels: Side, price: float | None, size: float, descending: bool) -> Side:
    """A side with ``size`` of ours added at ``price`` (which must be a price already there, or better or worse than all)."""
    if price is None or size <= EPS:
        return list(levels)
    out, placed = [], False
    for px, qty in levels:
        if not placed and abs(px - price) < EPS:
            out.append((px, qty + size))
            placed = True
        else:
            if not placed and ((px < price) if descending else (px > price)):
                out.append((price, size))
                placed = True
            out.append((px, qty))
    if not placed:
        out.append((price, size))
    return out


def share(levels: Side, price: float | None, size: float, target: float, discount: float, descending: bool, tick: float = TICK) -> float:
    """Our share of one side's score with ``size`` of ours resting at ``price``, as the filed rules score it.

    Every order from the best price down to the price where the target is
    reached counts, the whole of that last level included, each for
    discount ** (ticks from the best price) * size. A side that does not
    reach the target has no score.
    """
    if price is None or size <= EPS:
        return 0.0
    book = with_order(levels, price, size, descending)
    if not book:
        return 0.0
    best, cum, total, ours = book[0][0], 0.0, 0.0, 0.0
    for px, qty in book:
        w = discount ** ticks(px, best, tick)
        total += w * qty
        if abs(px - price) < EPS:
            ours += w * size
        cum += qty
        if cum >= target - EPS:
            return ours / total if total > 0 else 0.0
    return 0.0


def quotes(bids: Side, asks: Side, position: float, size: float, target: float, max_spread: float | None, state: str = "OPEN") -> dict[str, Any]:
    """The orders the rule rests on one reading: prices and sizes, or none.

    Nothing rests unless the market is open, the book as read qualifies
    without us, and its best prices are at most three ticks apart. The bid
    is cut by what is already held, the offer by what is already owed.
    """
    none = {"bid_px": None, "bid_qty": 0.0, "ask_px": None, "ask_qty": 0.0}
    if state != "OPEN" or not bids or not asks:
        return {**none, "why": "no market"}
    if not qualifies(bids, asks, target, max_spread):
        return {**none, "why": "the book does not qualify"}
    bid_px, ask_px = bids[0][0], asks[0][0]
    if ask_px <= bid_px + EPS or ticks(ask_px, bid_px) > MAX_SPREAD_TICKS:
        return {**none, "why": "best prices too far apart"}
    bid_qty = max(0.0, min(size, size - position))
    ask_qty = max(0.0, min(size, size + position))
    return {"bid_px": bid_px if bid_qty > EPS else None, "bid_qty": bid_qty, "ask_px": ask_px if ask_qty > EPS else None, "ask_qty": ask_qty, "why": "resting"}


LOW, HIGH = 0.01, 0.99    # the last tick at either end


def last_tick(bids: Side, asks: Side, bought: float, sold: float, target: float, max_spread: float | None, state: str = "OPEN") -> dict[str, Any]:
    """The order the rule of test Q1 rests on one reading: the target size at the last tick of a side nobody is standing on.

    A book with a maximum spread pays nobody while one side is short of the
    target size. When that is all that is missing, an order for the target
    size at 1 cent (or an offer at 99 cents) makes the book qualify. It can
    lose a cent a contract and no more. Nothing rests if the book qualifies
    as it is, if the order would not make it qualify, or once the account
    has traded the target size at that tick in this market. Like the rest
    of this module it is written for programmes that have a maximum spread,
    which every market the recorder reads has.
    """
    none = {"bid_px": None, "bid_qty": 0.0, "ask_px": None, "ask_qty": 0.0}
    if state != "OPEN":
        return {**none, "why": "no market"}
    if qualifies(bids, asks, target, max_spread):
        return {**none, "why": "the book qualifies without us"}
    if reaches(bids, target) is None and bought < target - EPS and (not asks or asks[0][0] > LOW + EPS):
        if qualifies(with_order(bids, LOW, target, True), asks, target, max_spread):
            return {**none, "bid_px": LOW, "bid_qty": target, "why": "resting"}
    if reaches(asks, target) is None and sold < target - EPS and (not bids or bids[0][0] < HIGH - EPS):
        if qualifies(bids, with_order(asks, HIGH, target, False), target, max_spread):
            return {**none, "ask_px": HIGH, "ask_qty": target, "why": "resting"}
    return {**none, "why": "an order at the last tick would not make it qualify"}


def shares(bids: Side, asks: Side, q: dict[str, Any], target: float, discount: float, max_spread: float | None) -> tuple[float, float]:
    """Our share of each side's score with the orders ``q`` in the book; (0, 0) if the book with them does not qualify."""
    if q["bid_px"] is None and q["ask_px"] is None:
        return 0.0, 0.0
    b = with_order(bids, q["bid_px"], q["bid_qty"], True)
    a = with_order(asks, q["ask_px"], q["ask_qty"], False)
    if not qualifies(b, a, target, max_spread):
        return 0.0, 0.0
    return (share(bids, q["bid_px"], q["bid_qty"], target, discount, True), share(asks, q["ask_px"], q["ask_qty"], target, discount, False))


def fills(q: dict[str, Any], prev: dict[str, Any], cur: dict[str, Any], cur_bids: Side, cur_asks: Side) -> tuple[float, float]:
    """Contracts of our bid and of our offer traded against between two readings.

    The exchange publishes no trades. A reading carries the running totals
    of contracts and dollars traded, the last trade and the day's lowest and
    highest trade with their times. If contracts traded since the earlier
    reading, and their average price, a newer last trade or a new low was at
    or below our bid, the bid is filled for as many contracts as traded, up
    to its size. Likewise the offer, with the high. If other people's
    offers now stand at our bid or below, the bid is filled for their size
    (the larger of the two amounts where both happen). This puts us first
    in line and sends all the trading through us.
    """
    def num(x: Any) -> float | None:
        try:
            v = float(x)
        except (TypeError, ValueError):
            return None
        return v if v == v else None

    t0 = num(prev.get("ts")) or 0.0
    v0, v1 = num(prev.get("traded")), num(cur.get("traded"))
    dv = (v1 - v0) if v0 is not None and v1 is not None else None
    if dv is not None and dv < -EPS:               # a total that starts again
        dv = v1
    traded = dv is not None and dv > EPS
    seen: list[float] = []
    if traded:
        n0, n1 = num(prev.get("notional")), num(cur.get("notional"))
        if n0 is not None and n1 is not None:
            v = (n1 - n0) / dv
            if 0.0 < v < 1.0:
                seen.append(v)
        for key in ("last", "low", "high"):
            px, at = num(cur.get(key)), num(cur.get(key + "_t"))
            if px is not None and at is not None and at > t0:
                seen.append(px)
    bid_fill = ask_fill = 0.0
    if q["bid_px"] is not None:
        by_trade = min(q["bid_qty"], dv) if traded and seen and min(seen) <= q["bid_px"] + EPS else 0.0
        through = sum(qty for px, qty in cur_asks if px <= q["bid_px"] + EPS)
        bid_fill = max(by_trade, min(q["bid_qty"], through))
    if q["ask_px"] is not None:
        by_trade = min(q["ask_qty"], dv) if traded and seen and max(seen) >= q["ask_px"] - EPS else 0.0
        through = sum(qty for px, qty in cur_bids if px >= q["ask_px"] - EPS)
        ask_fill = max(by_trade, min(q["ask_qty"], through))
    return bid_fill, ask_fill
