"""The rule of test L2: selling every bracket of a ladder at once.

docs/11_crypto_us.md, section 12. Used by the scorer of the live recorder
and by nothing that places an order.

    A ladder of brackets pays $1 on exactly one of them. Whoever has sold
    Q contracts of "Yes" in every bracket pays out Q, whatever the price
    does. If the bids of all the brackets bring in more than Q and the
    fees, the difference is kept whichever bracket pays.

Everything here is arithmetic on recorded bids. Sizes are in hundredths of
a contract, which is what the exchange trades in.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

THETA = 0.095             # taker fee coefficient of a small account
MONEY = 10_000.0          # the paper account, for each settlement time
GRID = 120                # a ladder is read every two minutes, counted back from its end,
FIRST = 330 * 60          # from five and a half hours before it
LAST = 2 * 60             # to two minutes before it
FRESH = 240               # a recorded book older than this is not used at a reading
PATIENT = 25.0            # what a sale has to lock, in dollars,
LATE = 30 * 60            # until this long before the end;
ENOUGH = 10.0             # from then on this is enough
LEVELS = 3                # bid levels the recorder writes down
COINS = ("btc", "eth", "sol", "xrp")          # the order in which ladders read at the same moment are served
HORIZONS = ("daily", "weekly")                # the ladders the test is about, daily first

Levels = list[tuple[float, float]]            # bids of one bracket, best first: (price, contracts)


def fee(qty: float, price: float) -> float:
    """The taker fee on one fill, rounded to the cent with halves to the even cent, as the exchange publishes it."""
    if qty <= 0 or not 0.0 < price < 1.0:
        return 0.0
    raw = Decimal(repr(THETA)) * Decimal(repr(round(qty, 2))) * Decimal(repr(round(price, 4))) * (1 - Decimal(repr(round(price, 4))))
    return float(raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))


def bids(row: dict[str, Any]) -> Levels:
    """The bids of a recorded book row, best first: at 1 cent or more, with a size."""
    out: Levels = []
    for i in range(1, LEVELS + 1):
        px, qty = _f(row.get(f"bid{i}")), _f(row.get(f"bid_qty{i}"))
        if px is not None and qty is not None and px >= 0.01 - 1e-9 and px < 1.0 and qty >= 0.01:
            out.append((round(px, 4), math.floor(qty * 100 + 1e-6) / 100))
    return sorted(out, reverse=True)


def sell(levels: Levels, q: float) -> dict[str, float]:
    """Selling up to ``q`` contracts into one bracket's bids, from the best down: each level one fill."""
    sold = money = fees = margin = 0.0
    for px, qty in levels:
        take = round(min(qty, q - sold), 2)
        if take <= 0:
            break
        sold = round(sold + take, 2)
        money += take * px
        fees += fee(take, px)
        margin += take * (1.0 - px)                      # a contract sold locks $1 less its price until the ladder settles
    return {"sold": sold, "money": money, "fees": fees, "margin": margin}


def sale(books: dict[str, Levels], q: float) -> dict[str, Any]:
    """A sale of size ``q`` in every bracket that has a bid, and what it locks."""
    legs = {slug: leg for slug, leg in ((s, sell(lv, q)) for s, lv in sorted(books.items())) if leg["sold"] > 0}
    money = sum(leg["money"] for leg in legs.values())
    fees = sum(leg["fees"] for leg in legs.values())
    most = max((leg["sold"] for leg in legs.values()), default=0.0)    # the most that can have to be paid: one bracket pays
    return {"q": q, "legs": legs, "money": money, "fees": fees, "margin": sum(leg["margin"] for leg in legs.values()),
            "pays_at_most": most, "locks": money - fees - most}


def sizes(books: dict[str, Levels]) -> list[float]:
    """The sizes at which some bracket's recorded bids run out, smallest first."""
    out = set()
    for levels in books.values():
        total = 0.0
        for _, qty in levels:
            total = round(total + qty, 2)
            out.add(total)
    return sorted(out)


def largest(books: dict[str, Levels], room: float, top: float) -> float:
    """The largest size up to ``top`` whose sale locks no more money than ``room``, to a hundredth of a contract."""
    if sale(books, top)["margin"] <= room + 1e-9:
        return top
    lo, hi = 0, int(round(top * 100))                    # hundredths: lo fits, hi does not
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if sale(books, mid / 100)["margin"] <= room + 1e-9:
            lo = mid
        else:
            hi = mid
    return lo / 100


def best(books: dict[str, Levels], room: float = MONEY) -> dict[str, Any] | None:
    """The sale that locks the most with ``room`` of money; of two that lock the same, the smaller. None if nothing can be sold."""
    tries = sizes(books)
    if not tries or room <= 0:
        return None
    cap = largest(books, room, tries[-1])
    found = None
    for q in sorted({t for t in tries if t <= cap + 1e-9} | ({cap} if cap > 0 else set())):
        s = sale(books, q)
        if found is None or s["locks"] > found["locks"] + 1e-9:
            found = s
    return found


def least(left: float) -> float:
    """What a sale has to lock at a reading ``left`` seconds before the ladder's end."""
    return ENOUGH if left <= LATE + 1e-9 else PATIENT


def decide(books: dict[str, Levels], left: float, room: float = MONEY) -> dict[str, Any] | None:
    """The sale the rule makes at one reading of a ladder that has not been sold yet, or None."""
    if not LAST - 1e-9 <= left <= FIRST + 1e-9:
        return None
    s = best(books, room)
    return s if s is not None and s["locks"] >= least(left) - 1e-9 else None


def top_up(books: dict[str, Levels], position: dict[str, Any], room: float) -> dict[str, dict[str, float]]:
    """Brackets never sold that have a bid now: each sold once, up to the size of the sale, as far as the money goes."""
    out: dict[str, dict[str, float]] = {}
    for slug, levels in sorted(books.items()):
        if slug in position["legs"] or not levels or room <= 1e-9:
            continue
        q = largest({slug: levels}, room, position["q"])
        leg = sell(levels, q)
        if leg["sold"] > 0:
            out[slug] = leg
            room -= leg["margin"]
    return out


def add(position: dict[str, Any], legs: dict[str, dict[str, float]]) -> None:
    """Add later legs to a position. They cannot raise what is paid: none is larger than the sale."""
    position["legs"].update(legs)
    for key in ("money", "fees", "margin"):
        position[key] += sum(leg[key] for leg in legs.values())
    position["pays_at_most"] = max(leg["sold"] for leg in position["legs"].values())
    position["locks"] = position["money"] - position["fees"] - position["pays_at_most"]


def result(position: dict[str, Any], paid: dict[str, float]) -> float:
    """What a position made, given what "Yes" paid in each bracket (1 in the one that paid, 0 in the others)."""
    return position["money"] - position["fees"] - sum(leg["sold"] * float(paid.get(slug, 0.0)) for slug, leg in position["legs"].items())


def readings(end: float) -> list[float]:
    """The moments at which a ladder ending at ``end`` is read, earliest first."""
    return [end - k * GRID for k in range(FIRST // GRID, LAST // GRID - 1, -1)]


def _f(x: Any) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None
