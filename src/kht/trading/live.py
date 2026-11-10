"""Live broker: real orders through Polymarket's official Python SDK.

STATUS: written against ``polymarket-client`` 0.18 (method names and response
types were checked by introspecting the installed SDK) and exercised in tests
with a stand-in client, but **never run against a real account**. No
credentials were available when it was written and the machine it was written
on is in a region where Polymarket does not accept orders. Before trusting it
with money, place one minimum-size order by hand through this class and check
the fill, the balance and the position on polymarket.com.

Live trading is deliberately hard to switch on. All of these must hold:

1. the config says ``"mode": "live"``;
2. the environment has ``KHT_ENABLE_LIVE=yes-trade-real-money``;
3. ``POLYMARKET_PRIVATE_KEY`` and ``POLYMARKET_WALLET_ADDRESS`` are set
   (in the environment only: never in the repository, never in a config file);
4. Polymarket's geoblock endpoint says this machine may place orders
   (https://docs.polymarket.com/api-reference/geoblock). This check is a
   compliance rule, not an obstacle: do not route around it;
5. the account is not in closed-only mode.

Every order still passes through ``RiskManager`` first; this class adds its
own last-line cap on order size.
"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

from ..api import Polymarket
from .broker import Broker
from .fees import taker_fee
from .models import Fill, Intent, MarketInfo, Order, OrderKind, OrderStatus, Side
from .portfolio import Portfolio

ENABLE_ENV = "KHT_ENABLE_LIVE"
ENABLE_VALUE = "yes-trade-real-money"
EPS = 1e-9


class LiveTradingNotPermitted(RuntimeError):
    pass


def preflight(pm: Polymarket, env: dict[str, str] | None = None) -> None:
    """Raise unless every precondition for live trading holds."""
    env = os.environ if env is None else env
    if env.get(ENABLE_ENV) != ENABLE_VALUE:
        raise LiveTradingNotPermitted(f"live trading is off: set {ENABLE_ENV}={ENABLE_VALUE} to enable it")
    for key in ("POLYMARKET_PRIVATE_KEY", "POLYMARKET_WALLET_ADDRESS"):
        if not env.get(key):
            raise LiveTradingNotPermitted(f"missing credential {key} in the environment")
    geo = pm.geoblock()
    if geo.get("blocked", True):
        raise LiveTradingNotPermitted(
            f"Polymarket does not accept orders from this location ({geo.get('country')}-{geo.get('region')}); "
            "live trading must not run here")


def connect(env: dict[str, str] | None = None) -> Any:
    """Create the SDK's authenticated client from environment credentials."""
    env = os.environ if env is None else env
    from polymarket import SecureClient  # imported lazily: only needed for live trading

    return SecureClient.create(private_key=env["POLYMARKET_PRIVATE_KEY"], wallet=env["POLYMARKET_WALLET_ADDRESS"])


class LiveBroker(Broker):
    def __init__(
        self,
        client: Any,
        portfolio: Portfolio,
        orders: dict[str, Order] | None = None,
        max_order_usd: float = 25.0,
    ):
        self.client = client
        self.portfolio = portfolio
        self.orders: dict[str, Order] = orders or {}
        self.max_order_usd = max_order_usd
        if client.get_closed_only_mode():
            raise LiveTradingNotPermitted("the account is in closed-only mode: it cannot open positions")

    def open_orders(self) -> list[Order]:
        return [o for o in self.orders.values() if o.status == OrderStatus.OPEN]

    # --------------------------------------------------------------- place
    def place(self, intent: Intent, market: MarketInfo, now: float) -> tuple[Order, list[Fill]]:
        notional = intent.price * intent.size
        order = Order("", market.market_id, intent.token, intent.side, intent.kind, intent.price, intent.size,
                      created_ts=now, expires_ts=intent.expires_ts, reason=intent.reason, tag=intent.tag)
        if intent.side == Side.BUY and notional > self.max_order_usd + EPS:
            order.status = OrderStatus.REJECTED
            order.reason = f"live cap: order {notional:.2f} above {self.max_order_usd:.2f}"
            return order, []

        if intent.kind == OrderKind.MAKER:
            kwargs: dict[str, Any] = dict(token_id=intent.token, price=str(intent.price), size=str(intent.size),
                                          side=intent.side.value, post_only=True)
            if intent.expires_ts is not None:
                # GTD orders must expire at least 3 minutes out (docs: trading/place-orders)
                kwargs["expiration"] = int(max(intent.expires_ts, now + 240))
            resp = self.client.place_limit_order(**kwargs)
        elif intent.side == Side.BUY:
            # fill-and-kill: spend at most the notional, never pay above our limit
            resp = self.client.place_market_order(token_id=intent.token, side="BUY", amount=str(round(notional, 2)),
                                                  max_price=str(intent.price), order_type="FAK")
        else:
            resp = self.client.place_market_order(token_id=intent.token, side="SELL", shares=str(intent.size),
                                                  min_price=str(intent.price), order_type="FAK")

        if not getattr(resp, "ok", False):
            order.status = OrderStatus.REJECTED
            order.reason = f"exchange rejected: {getattr(resp, 'code', '?')} {getattr(resp, 'message', '')}".strip()
            return order, []

        order.order_id = str(resp.order_id)
        fills: list[Fill] = []
        making = float(Decimal(str(getattr(resp, "making_amount", 0) or 0)))
        taking = float(Decimal(str(getattr(resp, "taking_amount", 0) or 0)))
        # for a BUY we give dollars (making) and receive shares (taking); a SELL is the reverse
        shares, dollars = (taking, making) if intent.side == Side.BUY else (making, taking)
        if resp.status == "matched" and shares > EPS:
            px = dollars / shares
            fee = 0.0 if intent.kind == OrderKind.MAKER else taker_fee(shares, px, market.fee_rate, market.fee_exponent)
            fill = Fill(order.order_id, market.market_id, intent.token, intent.side, px, shares, fee, now,
                        maker=False, tag=intent.tag)
            self.portfolio.apply(fill)
            fills.append(fill)
            order.filled = shares
        if intent.kind == OrderKind.MAKER and resp.status in ("live", "delayed"):
            order.status = OrderStatus.OPEN
        else:
            order.status = OrderStatus.FILLED if order.remaining <= 1e-6 else OrderStatus.CANCELLED
        self.orders[order.order_id] = order
        return order, fills

    # -------------------------------------------------------------- cancel
    def cancel(self, order_id: str, now: float) -> bool:
        o = self.orders.get(order_id)
        if o is None or o.status != OrderStatus.OPEN:
            return False
        self.client.cancel_order(order_id=order_id)
        o.status = OrderStatus.CANCELLED
        return True

    def cancel_everything(self) -> None:
        """Emergency stop: ask the exchange to cancel every open order on the account."""
        self.client.cancel_all()
        for o in self.open_orders():
            o.status = OrderStatus.CANCELLED

    # ---------------------------------------------------------------- sync
    def sync(self, markets: dict[int, MarketInfo], now: float) -> list[Fill]:
        """Ask the exchange how much of each resting order has matched."""
        new_fills: list[Fill] = []
        for o in self.open_orders():
            remote = self.client.get_order(order_id=o.order_id)
            matched = float(remote.size_matched)
            delta = matched - o.filled
            if delta > 1e-6:
                fill = Fill(o.order_id, o.market_id, o.token, o.side, o.price, delta, 0.0, now, maker=True, tag=o.tag)
                self.portfolio.apply(fill)
                new_fills.append(fill)
                o.filled = matched
            status = str(remote.status).upper()
            if o.remaining <= 1e-6 or "MATCHED" in status:
                o.status = OrderStatus.FILLED
            elif "CANCEL" in status or "EXPIRE" in status:
                o.status = OrderStatus.CANCELLED
        return new_fills

    # ------------------------------------------------------- reconciliation
    def cash_on_exchange(self) -> float:
        """Collateral balance reported by the exchange, in dollars (6 decimals on-chain)."""
        bal = self.client.get_balance_allowance(asset_type="COLLATERAL")
        return float(bal.balance) / 1e6

    def to_dict(self) -> dict[str, Any]:
        return {"orders": {k: o.to_dict() for k, o in self.orders.items()}}

    @classmethod
    def from_dict(cls, client: Any, portfolio: Portfolio, d: dict[str, Any], **kw: Any) -> "LiveBroker":
        return cls(client, portfolio, orders={k: Order.from_dict(v) for k, v in d.get("orders", {}).items()}, **kw)
