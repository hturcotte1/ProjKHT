"""Broker interface and the paper broker.

The paper broker trades against *live* Polymarket data without sending
anything to the exchange:

* taker orders fill against the order book as it stands when they are placed;
* resting (maker) orders fill only when later prints on the public trade tape
  trade into them, using the same rules as the backtester (``fills.py``).

That makes paper results directly comparable to backtest results, and keeps
both honest about the one thing a simulator cannot know: whether a resting
order would really have been reached.
"""

from __future__ import annotations

import itertools
import time
from abc import ABC, abstractmethod
from typing import Any

from ..api import Polymarket
from .fills import maker_fill, taker_fill
from .models import Fill, Intent, MarketInfo, Order, OrderKind, OrderStatus, Quote, Side, TradePrint
from .portfolio import Portfolio

EPS = 1e-9


def quote_from_book(token: str, book: dict[str, Any], ts: float) -> Quote:
    bids = [(float(l["price"]), float(l["size"])) for l in book.get("bids") or []]
    asks = [(float(l["price"]), float(l["size"])) for l in book.get("asks") or []]
    bid = max(bids, default=None)
    ask = min(asks, default=None)
    return Quote(token, ts, bid[0] if bid else None, ask[0] if ask else None,
                 bid[1] if bid else 0.0, ask[1] if ask else 0.0)


def book_levels(book: dict[str, Any], side: Side) -> list[tuple[float, float]]:
    """Levels a taker order of ``side`` would consume, best first."""
    if side == Side.BUY:
        return sorted(((float(l["price"]), float(l["size"])) for l in book.get("asks") or []))
    return sorted(((float(l["price"]), float(l["size"])) for l in book.get("bids") or []), reverse=True)


def size_at_price(book: dict[str, Any], side: Side, price: float) -> float:
    """Shares already resting at ``price`` on our side of the book."""
    levels = book.get("bids") if side == Side.BUY else book.get("asks")
    return sum(float(l["size"]) for l in levels or [] if abs(float(l["price"]) - price) < 1e-9)


class Broker(ABC):
    """What the engine needs from an execution venue."""

    portfolio: Portfolio

    @abstractmethod
    def place(self, intent: Intent, market: MarketInfo, now: float) -> tuple[Order, list[Fill]]: ...

    @abstractmethod
    def cancel(self, order_id: str, now: float) -> bool: ...

    @abstractmethod
    def open_orders(self) -> list[Order]: ...

    @abstractmethod
    def sync(self, markets: dict[int, MarketInfo], now: float) -> list[Fill]:
        """Bring fills and order states up to date; return new fills."""


class PaperBroker(Broker):
    def __init__(
        self,
        pm: Polymarket,
        portfolio: Portfolio,
        orders: dict[str, Order] | None = None,
        last_print_ts: dict[int, float] | None = None,
        next_id: int = 1,
        taker_slippage_ticks: int = 0,
    ):
        self.pm = pm
        self.portfolio = portfolio
        self.orders: dict[str, Order] = orders or {}
        self.last_print_ts: dict[int, float] = last_print_ts or {}
        self._ids = itertools.count(next_id)
        self._next_id = next_id
        self.taker_slippage_ticks = taker_slippage_ticks

    # ------------------------------------------------------------- helpers
    def _new_id(self) -> str:
        self._next_id = next(self._ids)
        return f"paper-{self._next_id}"

    def open_orders(self) -> list[Order]:
        return [o for o in self.orders.values() if o.status == OrderStatus.OPEN]

    # --------------------------------------------------------------- place
    def place(self, intent: Intent, market: MarketInfo, now: float) -> tuple[Order, list[Fill]]:
        book = self.pm.book(intent.token)
        order = Order(self._new_id(), market.market_id, intent.token, intent.side, intent.kind,
                      intent.price, intent.size, created_ts=now, expires_ts=intent.expires_ts,
                      reason=intent.reason, tag=intent.tag)
        q = quote_from_book(intent.token, book, now)
        if intent.kind == OrderKind.MAKER:
            # post-only: an order that would trade immediately is rejected, as on the exchange
            crosses = (intent.side == Side.BUY and q.ask is not None and intent.price >= q.ask - EPS) or (
                intent.side == Side.SELL and q.bid is not None and intent.price <= q.bid + EPS)
            if crosses:
                order.status = OrderStatus.REJECTED
                order.reason = (order.reason + " | rejected: post-only order would cross").strip(" |")
                return order, []
            order.queue_ahead = size_at_price(book, intent.side, intent.price)
            self.orders[order.order_id] = order
            self.last_print_ts.setdefault(market.market_id, now)
            return order, []
        # taker
        levels = book_levels(book, intent.side)
        if self.taker_slippage_ticks and levels:
            # pessimism knob: pretend the first level(s) vanished before we arrived
            levels = levels[self.taker_slippage_ticks:]
        fills = taker_fill(order, levels, market, now)
        for f in fills:
            self.portfolio.apply(f)
        self.orders[order.order_id] = order
        return order, fills

    # -------------------------------------------------------------- cancel
    def cancel(self, order_id: str, now: float) -> bool:
        o = self.orders.get(order_id)
        if o is None or o.status != OrderStatus.OPEN:
            return False
        o.status = OrderStatus.CANCELLED
        return True

    # ---------------------------------------------------------------- sync
    def sync(self, markets: dict[int, MarketInfo], now: float) -> list[Fill]:
        """Replay tape prints since the last sync against resting orders."""
        new_fills: list[Fill] = []
        by_market: dict[int, list[Order]] = {}
        for o in self.open_orders():
            by_market.setdefault(o.market_id, []).append(o)
        for market_id, orders in by_market.items():
            market = markets.get(market_id)
            if market is None:
                continue
            since = self.last_print_ts.get(market_id, min(o.created_ts for o in orders))
            prints = self._prints_since(market, since)
            for p in prints:
                for o in sorted(orders, key=lambda x: x.created_ts):
                    if o.status != OrderStatus.OPEN:
                        continue
                    f = maker_fill(o, p, market)
                    if f is not None:
                        # never sell shares the ledger does not hold
                        if f.side == Side.SELL and self.portfolio.shares(f.token) + EPS < f.size:
                            o.filled -= f.size
                            o.status = OrderStatus.CANCELLED
                            continue
                        self.portfolio.apply(f)
                        new_fills.append(f)
            if prints:
                self.last_print_ts[market_id] = max(p.ts for p in prints)
        for o in self.open_orders():
            if o.expires_ts is not None and now >= o.expires_ts:
                o.status = OrderStatus.CANCELLED
                o.reason = (o.reason + " | expired").strip(" |")
        return new_fills

    def _prints_since(self, market: MarketInfo, since: float, max_pages: int = 5) -> list[TradePrint]:
        out: list[TradePrint] = []
        for t in self.pm.iter_trades(condition=market.condition_id, max_pages=max_pages):
            ts = float(t["timestamp"])
            if ts <= since:
                break
            token = str(t.get("token_id") or market.token(int(t.get("outcome_index", 0))))
            out.append(TradePrint(ts, token, Side(t["side"]), float(t["price"]), float(t["size"])))
        out.sort(key=lambda p: p.ts)
        return out

    # --------------------------------------------------------------- state
    def to_dict(self) -> dict[str, Any]:
        # closed orders are kept for a while for the report, then dropped
        keep = {k: o for k, o in self.orders.items()
                if o.status == OrderStatus.OPEN or o.created_ts > time.time() - 3 * 86_400}
        return {
            "orders": {k: o.to_dict() for k, o in keep.items()},
            "last_print_ts": {str(k): v for k, v in self.last_print_ts.items()},
            "next_id": self._next_id + 1,
        }

    @classmethod
    def from_dict(cls, pm: Polymarket, portfolio: Portfolio, d: dict[str, Any], **kw: Any) -> "PaperBroker":
        return cls(
            pm, portfolio,
            orders={k: Order.from_dict(v) for k, v in d.get("orders", {}).items()},
            last_print_ts={int(k): float(v) for k, v in d.get("last_print_ts", {}).items()},
            next_id=int(d.get("next_id", 1)),
            **kw,
        )
