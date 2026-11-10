"""Live market universe: what is open and tradable right now.

The same inclusion rule is used live as in research, because a backtest only
says something about the markets it was run on: a binary market that has
already traded a minimum number of shares (known today, not in hindsight).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..api import Polymarket
from ..data.markets import flatten_market
from .models import MarketInfo


@dataclass
class LiveMarket:
    """A market plus its latest top-of-book for outcome 0, as listed by Gamma."""

    info: MarketInfo
    best_bid0: float | None
    best_ask0: float | None
    volume: float
    volume_24h: float
    liquidity: float
    accepting_orders: bool
    closed: bool
    winner: float | None       # 0.0 / 1.0 once resolved, else None
    final0: float | None       # final price of outcome 0 once closed (0, 1, or 0.5 for a split)
    question: str = ""

    def ask(self, outcome: int) -> float | None:
        """Price to buy ``outcome`` now, using the mirrored book."""
        if outcome == 0:
            return self.best_ask0
        return None if self.best_bid0 is None else 1.0 - self.best_bid0

    def bid(self, outcome: int) -> float | None:
        if outcome == 0:
            return self.best_bid0
        return None if self.best_ask0 is None else 1.0 - self.best_ask0


def to_live(row: dict[str, Any]) -> LiveMarket:
    def num(x: Any) -> float | None:
        return float(x) if x is not None and x == x else None

    info = MarketInfo(
        market_id=int(row["market_id"]), condition_id=row["condition_id"], question=row["question"] or "",
        token0=row["token0"], token1=row["token1"], outcome0=row["outcome0"], outcome1=row["outcome1"],
        event_id=int(row["event_id"]), category=row["category"], fee_rate=float(row["fee_rate"] or 0.0),
        tick=float(row["tick"] or 0.01), min_size=float(row["min_size"] or 5.0), neg_risk=bool(row["neg_risk"]),
        end_ts=float(row["end_ts"]), game_start_ts=float(row["game_start_ts"]),
        tags=tuple(t for t in str(row.get("tags") or "").split("|") if t),
    )
    winner = num(row.get("winner"))
    final0 = num(row.get("final0")) if row.get("closed") else None
    return LiveMarket(
        info=info, best_bid0=num(row.get("best_bid")), best_ask0=num(row.get("best_ask")),
        volume=float(row.get("volume") or 0.0), volume_24h=float(row.get("volume_24h") or 0.0),
        liquidity=float(row.get("liquidity") or 0.0), accepting_orders=bool(row.get("accepting_orders")),
        closed=bool(row.get("closed")), winner=winner, final0=final0, question=row["question"] or "",
    )


def scan_open(pm: Polymarket, min_volume: float = 100_000) -> dict[int, LiveMarket]:
    """All open binary markets that have traded at least ``min_volume`` shares."""
    out: dict[int, LiveMarket] = {}
    for m in pm.iter_markets(closed=False, volume_num_min=min_volume, include_tag=True):
        row = flatten_market(m)
        if row is None:
            continue
        out[int(row["market_id"])] = to_live(row)
    return out


def fetch_markets(pm: Polymarket, market_ids: list[int]) -> dict[int, LiveMarket]:
    """Current state of specific markets, open or closed (used to settle positions)."""
    out: dict[int, LiveMarket] = {}
    for mid in market_ids:
        try:
            m = pm.market_by_id(mid)
        except Exception:  # noqa: BLE001 - a market that cannot be read now is retried next cycle
            continue
        # /markets/{id} does not embed tags; category is not needed for settlement
        row = flatten_market(m)
        if row is not None:
            out[int(row["market_id"])] = to_live(row)
    return out


# Tags Polymarket uses for its own plumbing (reward tiers, display flags). They
# group markets that have nothing in common, so they are never themes.
OPERATIONAL_TAG_PREFIXES = ("earn-", "rewards-", "hide-", "show-")
OPERATIONAL_TAGS = {"recurring", "games", "monthly", "weekly", "daily", "hit-price", "up-or-down"}


def is_operational_tag(tag: str) -> bool:
    return tag in OPERATIONAL_TAGS or tag.startswith(OPERATIONAL_TAG_PREFIXES)


def theme_tags(markets: dict[int, LiveMarket], max_share: float = 0.03, min_markets: int = 2) -> dict[int, frozenset[str]]:
    """Narrow tags per market: the ones that identify a *story* (a conflict, an
    election, a commodity) rather than a broad category.

    Several markets about one story tend to resolve together, so exposure is
    capped per theme as well as per event. A tag counts as a theme if it is
    shared by at least ``min_markets`` markets but by no more than
    ``max_share`` of all markets scanned.
    """
    counts: dict[str, int] = {}
    for lm in markets.values():
        for tag in set(lm.info.tags):
            counts[tag] = counts.get(tag, 0) + 1
    limit = max(min_markets, max_share * max(len(markets), 1))
    themes = {tag for tag, n in counts.items() if min_markets <= n <= limit and not is_operational_tag(tag)}
    return {mid: frozenset(set(lm.info.tags) & themes) for mid, lm in markets.items()}
