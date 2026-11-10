"""Has an outcome's price gone quiet?

The second round of research found that near-certain contracts which have
barely moved for a week lose far less often than others at the same price
(docs/04_second_round.md). The measure is the one the backtest used: the
highest minus the lowest price at which the outcome *traded* over the last
few days, read from the public trade feed, with trades in the other outcome
counted at one minus their price.

Nothing here decides anything. The engine uses it as a filter when a
strategy asks for one, and records it beside every forward-test signal so
that the finding can be checked on new data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import MarketInfo

PAGE = 1000
MAX_PAGES = 20          # 20,000 prints in the window: a market that busy is not quiet


@dataclass(frozen=True)
class Quietness:
    range: float | None     # highest minus lowest traded price in the window; None if nothing traded in it
    prints: int             # taker prints in the window
    seasoned: bool          # the market had already traded before the window began
    complete: bool          # False if the feed was cut off before the start of the window was reached

    def is_quiet(self, max_range: float) -> bool:
        """Traded in the window, never more than ``max_range`` apart, in a market older than the window."""
        return self.complete and self.seasoned and self.range is not None and self.range <= max_range + 1e-9

    def to_dict(self) -> dict[str, Any]:
        return {"range": None if self.range is None else round(self.range, 4), "prints": self.prints,
                "seasoned": int(self.seasoned), "complete": int(self.complete)}


def traded_range(pm: Any, market: MarketInfo, outcome: int, as_of: float, days: float,
                 max_pages: int = MAX_PAGES) -> Quietness:
    """Range of prices at which ``outcome`` traded in the ``days`` days up to ``as_of``.

    The feed comes newest first. Trades after ``as_of`` are skipped, so the
    same function serves a live check (``as_of`` is now) and a look back at a
    signal logged earlier.
    """
    start = as_of - days * 86_400
    token = market.token(outcome)
    hi, lo, n = float("-inf"), float("inf"), 0
    seasoned = False
    seen = 0
    for t in pm.iter_trades(condition=market.condition_id, page_size=PAGE, max_pages=max_pages):
        seen += 1
        ts = float(t["timestamp"])
        if ts > as_of:
            continue
        if ts < start:
            seasoned = True
            break
        traded = str(t.get("token_id") or market.token(int(t.get("outcome_index", 0))))
        price = float(t["price"])
        p = price if traded == token else 1.0 - price
        hi, lo, n = max(hi, p), min(lo, p), n + 1
    # reaching an older trade proves the read is complete; so does running out of trades before the page limit
    complete = seasoned or seen < PAGE * max_pages
    return Quietness(range=(hi - lo) if n else None, prints=n, seasoned=seasoned, complete=complete)
