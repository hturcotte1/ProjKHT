"""Cash and position accounting.

One ledger for the backtester, the paper broker and (as a shadow copy) the
live broker. Positions are long-only in outcome tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Fill, Position, Side

EPS = 1e-9


@dataclass
class Portfolio:
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)   # by token
    realized: float = 0.0
    fees_paid: float = 0.0
    n_fills: int = 0

    def apply(self, fill: Fill) -> None:
        pos = self.positions.get(fill.token)
        notional = fill.price * fill.size
        if fill.side == Side.BUY:
            if pos is None:
                pos = Position(fill.market_id, fill.token, opened_ts=fill.ts, tag=fill.tag)
                self.positions[fill.token] = pos
            self.cash -= notional + fill.fee
            pos.shares += fill.size
            pos.cost += notional + fill.fee
        else:
            if pos is None or pos.shares + EPS < fill.size:
                raise ValueError(f"sell of {fill.size} exceeds holding in {fill.token}")
            avg = pos.avg_price
            proceeds = notional - fill.fee
            pnl = proceeds - avg * fill.size
            self.cash += proceeds
            pos.shares -= fill.size
            pos.cost -= avg * fill.size
            pos.realized += pnl
            self.realized += pnl
            if pos.shares <= EPS:
                del self.positions[fill.token]
        self.fees_paid += fill.fee
        self.n_fills += 1

    def settle(self, token: str, payoff: float) -> float:
        """Pay out a resolved position (payoff 1.0 or 0.0 per share). Returns the profit."""
        pos = self.positions.pop(token, None)
        if pos is None:
            return 0.0
        proceeds = pos.shares * payoff
        pnl = proceeds - pos.cost
        self.cash += proceeds
        self.realized += pnl
        return pnl

    def shares(self, token: str) -> float:
        pos = self.positions.get(token)
        return pos.shares if pos else 0.0

    def cost_in_market(self, market_id: int) -> float:
        return sum(p.cost for p in self.positions.values() if p.market_id == market_id)

    def invested(self) -> float:
        return sum(p.cost for p in self.positions.values())

    def equity(self, marks: dict[str, float]) -> float:
        """Cash plus positions valued at ``marks`` (falls back to cost when no mark)."""
        value = self.cash
        for token, pos in self.positions.items():
            mark = marks.get(token)
            value += pos.shares * mark if mark is not None else pos.cost
        return value

    def to_dict(self) -> dict[str, Any]:
        return {
            "cash": self.cash,
            "realized": self.realized,
            "fees_paid": self.fees_paid,
            "n_fills": self.n_fills,
            "positions": {t: p.to_dict() for t, p in self.positions.items()},
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Portfolio":
        return cls(
            cash=float(d["cash"]),
            positions={t: Position.from_dict(p) for t, p in d.get("positions", {}).items()},
            realized=float(d.get("realized", 0.0)),
            fees_paid=float(d.get("fees_paid", 0.0)),
            n_fills=int(d.get("n_fills", 0)),
        )
