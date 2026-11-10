"""How orders fill. One implementation, used by the backtester and the paper broker.

Getting this wrong is the usual way a backtest lies, so the rules are spelled
out and deliberately pessimistic.

Taker orders
    Fill immediately against the visible book, level by level, never beyond the
    limit price. The taker fee applies.

Maker (resting, post-only) orders
    Fill only when the public tape shows someone actually trading into them:

    * a taker trade that prints *through* our price proves our level was
      swept, so the order fills in full at our price;
    * a taker trade exactly *at* our price first consumes the shares that were
      queued ahead of us when we joined the level, and only the remainder
      reaches us;
    * nothing else fills a maker order. In particular the mid moving past our
      price without a print does not count.

    Because Polymarket's book is mirrored (buying one outcome at ``x`` is the
    same trade as selling the other at ``1 - x``), prints in the opposite
    token are translated before the comparison.
"""

from __future__ import annotations

import math

from .fees import taker_fee
from .models import Fill, MarketInfo, Order, OrderStatus, Side, TradePrint

EPS = 1e-9


def in_token_frame(print_: TradePrint, token: str, market: MarketInfo) -> tuple[Side, float]:
    """Express a print as (taker side, price) on ``token``."""
    if print_.token == token:
        return print_.side, print_.price
    if print_.token not in (market.token0, market.token1):
        raise KeyError(f"print for token {print_.token} does not belong to market {market.market_id}")
    mirrored = Side.SELL if print_.side == Side.BUY else Side.BUY
    return mirrored, 1.0 - print_.price


def maker_fill(order: Order, print_: TradePrint, market: MarketInfo) -> Fill | None:
    """Apply one tape print to one resting order. Mutates the order; returns
    the resulting fill, if any."""
    if order.status != OrderStatus.OPEN or order.remaining <= EPS:
        return None
    if print_.ts < order.created_ts:
        return None
    if order.expires_ts is not None and print_.ts >= order.expires_ts:
        return None
    side, price = in_token_frame(print_, order.token, market)
    # a resting BUY is hit by taker SELLs at or below its price, and vice versa
    if order.side == Side.BUY:
        if side != Side.SELL or price > order.price + EPS:
            return None
        through = price < order.price - EPS
    else:
        if side != Side.BUY or price < order.price - EPS:
            return None
        through = price > order.price + EPS

    if through:
        qty = order.remaining
        order.queue_ahead = 0.0
    else:
        available = print_.size
        used_by_queue = min(order.queue_ahead, available)
        order.queue_ahead -= used_by_queue
        qty = min(order.remaining, available - used_by_queue)
    if qty <= EPS:
        return None
    order.filled += qty
    if order.remaining <= EPS:
        order.status = OrderStatus.FILLED
    return Fill(order.order_id, order.market_id, order.token, order.side, order.price, qty, 0.0,
                print_.ts, maker=True, tag=order.tag)


def taker_fill(
    order: Order,
    levels: list[tuple[float, float]],
    market: MarketInfo,
    ts: float,
) -> list[Fill]:
    """Fill a marketable order against book ``levels`` (price, size) of the
    opposite side, best first. Unfilled remainder is cancelled (fill-and-kill)."""
    fills: list[Fill] = []
    for price, size in levels:
        if order.remaining <= EPS:
            break
        if order.side == Side.BUY and price > order.price + EPS:
            break
        if order.side == Side.SELL and price < order.price - EPS:
            break
        qty = min(order.remaining, size)
        if qty <= EPS:
            continue
        fee = taker_fee(qty, price, market.fee_rate, market.fee_exponent)
        order.filled += qty
        fills.append(Fill(order.order_id, order.market_id, order.token, order.side, price, qty, fee,
                          ts, maker=False, tag=order.tag))
    order.status = OrderStatus.FILLED if order.remaining <= EPS else OrderStatus.CANCELLED
    return fills


def round_to_tick(price: float, tick: float, side: Side) -> float:
    """Round a limit price onto the tick grid without making it more aggressive:
    buys round down, sells round up."""
    steps = price / tick
    n = math.floor(steps + 1e-7) if side == Side.BUY else math.ceil(steps - 1e-7)
    return round(min(max(n * tick, tick), 1.0 - tick), 6)
