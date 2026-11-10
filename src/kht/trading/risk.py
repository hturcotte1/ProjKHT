"""Hard limits that sit between any strategy and any broker.

The strategy proposes; this module disposes. Every order passes ``check``
before it reaches a broker, in backtest, paper and live modes alike, and the
kill switch is evaluated every cycle. Limits are intentionally simple so that
they can be audited by reading this file.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .models import Intent, MarketInfo, Order, OrderKind, Side
from .portfolio import Portfolio


@dataclass
class RiskLimits:
    bankroll: float = 1_000.0            # capital the system is allowed to treat as its own
    max_position_usd: float = 25.0       # cost basis + resting buys, per market
    max_event_usd: float = 50.0          # the same, summed over markets of one event
    max_total_exposure_frac: float = 0.60  # of bankroll, positions + resting buys
    max_open_orders: int = 60
    max_order_usd: float = 25.0
    min_price: float = 0.03              # never quote in the lottery-ticket tails
    max_price: float = 0.97
    daily_loss_limit_usd: float = 50.0   # equity drop since the day's start that halts trading
    max_drawdown_usd: float = 150.0      # equity drop from the high-water mark that halts trading

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RiskState:
    halted: bool = False
    halt_reason: str = ""
    day: int = -1
    day_start_equity: float = 0.0
    high_water: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RiskManager:
    def __init__(self, limits: RiskLimits, state: RiskState | None = None):
        self.limits = limits
        self.state = state or RiskState()

    # ----------------------------------------------------------- kill switch
    def update(self, equity: float, now_ts: float) -> None:
        """Roll the trading day and trip the kill switch if a loss limit is hit.
        Once halted, trading stays halted until a human resets it."""
        day = int(now_ts // 86_400)
        if day != self.state.day:
            self.state.day = day
            self.state.day_start_equity = equity
        self.state.high_water = max(self.state.high_water, equity)
        if self.state.halted:
            return
        if self.state.day_start_equity - equity >= self.limits.daily_loss_limit_usd:
            self._halt(f"daily loss limit: equity {equity:.2f} vs day start {self.state.day_start_equity:.2f}")
        elif self.state.high_water - equity >= self.limits.max_drawdown_usd:
            self._halt(f"max drawdown: equity {equity:.2f} vs high-water {self.state.high_water:.2f}")

    def _halt(self, reason: str) -> None:
        self.state.halted = True
        self.state.halt_reason = reason

    def reset_halt(self) -> None:
        self.state.halted = False
        self.state.halt_reason = ""

    # -------------------------------------------------------------- pre-trade
    def check(
        self,
        intent: Intent,
        market: MarketInfo,
        portfolio: Portfolio,
        open_orders: list[Order],
        market_event: dict[int, int] | None = None,
    ) -> tuple[bool, str]:
        """Return (allowed, reason). Sells and cancels that reduce risk are
        always allowed, even when halted."""
        lim = self.limits
        if intent.action == "cancel":
            return True, ""
        if intent.size <= 0 or not (0.0 < intent.price < 1.0):
            return False, "bad price or size"
        if intent.size + 1e-9 < market.min_size:
            return False, f"size {intent.size:g} below market minimum {market.min_size:g}"
        if intent.side == Side.SELL:
            held = portfolio.shares(intent.token)
            resting = sum(o.remaining for o in open_orders if o.token == intent.token and o.side == Side.SELL)
            if intent.size > held - resting + 1e-9:
                return False, "sell exceeds free holding"
            return True, ""

        # --- everything below is a BUY, i.e. adds risk
        if self.state.halted:
            return False, f"halted: {self.state.halt_reason}"
        if not (lim.min_price <= intent.price <= lim.max_price):
            return False, f"price {intent.price:.3f} outside [{lim.min_price}, {lim.max_price}]"
        notional = intent.price * intent.size
        if notional > lim.max_order_usd + 1e-9:
            return False, f"order {notional:.2f} above per-order cap {lim.max_order_usd:.2f}"
        if len(open_orders) >= lim.max_open_orders:
            return False, "too many open orders"

        def resting_buys(pred) -> float:
            return sum(o.price * o.remaining for o in open_orders if o.side == Side.BUY and pred(o))

        in_market = portfolio.cost_in_market(market.market_id) + resting_buys(lambda o: o.market_id == market.market_id)
        if in_market + notional > lim.max_position_usd + 1e-9:
            return False, f"market exposure {in_market + notional:.2f} above cap {lim.max_position_usd:.2f}"

        if market.event_id >= 0 and market_event:
            same = {m for m, e in market_event.items() if e == market.event_id}
            in_event = sum(p.cost for p in portfolio.positions.values() if p.market_id in same)
            in_event += resting_buys(lambda o: o.market_id in same)
            if in_event + notional > lim.max_event_usd + 1e-9:
                return False, f"event exposure {in_event + notional:.2f} above cap {lim.max_event_usd:.2f}"

        total = portfolio.invested() + resting_buys(lambda o: True)
        if total + notional > lim.max_total_exposure_frac * lim.bankroll + 1e-9:
            return False, "total exposure cap"
        free_cash = portfolio.cash - resting_buys(lambda o: True)
        if notional > free_cash + 1e-9:
            return False, "insufficient free cash"
        if intent.kind == OrderKind.TAKER and market.fee_rate > 0 and intent.meta.get("edge") is not None:
            # a taker order must clear its own fee; strategies report expected edge per share
            from .fees import taker_fee_per_share

            if intent.meta["edge"] <= taker_fee_per_share(intent.price, market.fee_rate, market.fee_exponent):
                return False, "expected edge does not cover the taker fee"
        return True, ""
