"""Plain data types shared by the backtester, the paper broker and the live broker.

Conventions
-----------
* A *token* is one outcome of a binary market; its price is a probability in (0, 1).
* All orders are expressed on a token: BUY spends cash for shares, SELL returns it.
  Going "short" an outcome is done by buying the opposite token, never by
  selling shares we do not hold.
* Money is USDC (pUSD on Polymarket); sizes are shares that pay 1.00 if the
  outcome happens.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderKind(str, Enum):
    MAKER = "MAKER"   # post-only resting limit order: never pays the taker fee
    TAKER = "TAKER"   # marketable limit (fill-and-kill): pays spread and fee


class OrderStatus(str, Enum):
    OPEN = "OPEN"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class MarketInfo:
    """Static description of a market, as needed to trade it."""

    market_id: int
    condition_id: str
    question: str
    token0: str
    token1: str
    outcome0: str
    outcome1: str
    event_id: int = -1
    category: str = "other"
    fee_rate: float = 0.0
    fee_exponent: float = 1.0
    tick: float = 0.01
    min_size: float = 5.0
    neg_risk: bool = False
    end_ts: float = float("nan")
    game_start_ts: float = float("nan")

    def token(self, outcome: int) -> str:
        return self.token0 if outcome == 0 else self.token1

    def outcome_of(self, token: str) -> int:
        if token == self.token0:
            return 0
        if token == self.token1:
            return 1
        raise KeyError(token)


@dataclass
class Quote:
    """Top of book for one token at one instant."""

    token: str
    ts: float
    bid: float | None
    ask: float | None
    bid_size: float = 0.0
    ask_size: float = 0.0

    @property
    def mid(self) -> float | None:
        if self.bid is None or self.ask is None:
            return None
        return 0.5 * (self.bid + self.ask)

    @property
    def spread(self) -> float | None:
        if self.bid is None or self.ask is None:
            return None
        return self.ask - self.bid


@dataclass
class Order:
    order_id: str
    market_id: int
    token: str
    side: Side
    kind: OrderKind
    price: float
    size: float
    created_ts: float
    expires_ts: float | None = None
    filled: float = 0.0
    status: OrderStatus = OrderStatus.OPEN
    # shares resting ahead of us at our price when the order was placed; a
    # maker order only fills once that much has traded at the level
    queue_ahead: float = 0.0
    reason: str = ""
    tag: str = ""

    @property
    def remaining(self) -> float:
        return max(0.0, self.size - self.filled)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["side"] = self.side.value
        d["kind"] = self.kind.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Order":
        d = dict(d)
        d["side"] = Side(d["side"])
        d["kind"] = OrderKind(d["kind"])
        d["status"] = OrderStatus(d["status"])
        return cls(**d)


@dataclass
class Fill:
    order_id: str
    market_id: int
    token: str
    side: Side
    price: float
    size: float
    fee: float
    ts: float
    maker: bool
    tag: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["side"] = self.side.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Fill":
        d = dict(d)
        d["side"] = Side(d["side"])
        return cls(**d)


@dataclass
class Position:
    market_id: int
    token: str
    shares: float = 0.0
    cost: float = 0.0          # cash paid for the shares currently held (incl. fees)
    realized: float = 0.0      # realised profit from shares already sold or settled
    opened_ts: float = 0.0
    tag: str = ""

    @property
    def avg_price(self) -> float:
        return self.cost / self.shares if self.shares > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Position":
        return cls(**d)


@dataclass
class TradePrint:
    """A taker trade observed on the public tape, in the traded token's terms."""

    ts: float
    token: str
    side: Side        # the taker's side on ``token``
    price: float
    size: float


@dataclass
class Intent:
    """What a strategy wants: place one order, or cancel one."""

    action: str                     # "place" | "cancel"
    market_id: int = -1
    token: str = ""
    side: Side = Side.BUY
    kind: OrderKind = OrderKind.MAKER
    price: float = 0.0
    size: float = 0.0
    expires_ts: float | None = None
    order_id: str = ""
    reason: str = ""
    tag: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
