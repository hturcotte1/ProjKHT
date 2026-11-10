"""The trading rule.

Everything the strategy believes is in two small, inspectable objects:

* ``EdgeModel`` — a calibration curve fitted on resolved markets that turns a
  quoted price into an estimated chance of paying out, by segment;
* ``StrategyConfig`` — which markets it may touch and how it sizes and exits.

``decide`` is a pure function of the current market snapshot and the account:
no network, no clock, no hidden state, so the same code runs in tests, in the
paper trader and live.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .fees import taker_fee_per_share
from .fills import round_to_tick
from .models import Intent, Order, OrderKind, Side
from .portfolio import Portfolio
from .universe import LiveMarket


def logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


@dataclass
class EdgeModel:
    """``P(outcome pays) = sigmoid(a + b * logit(price))`` per segment.

    ``b > 1`` means prices are compressed toward 50%: a 93c contract pays more
    often than 93% of the time. Segments fall back to the pooled fit.
    """

    pooled: tuple[float, float] = (0.0, 1.0)
    segments: dict[str, tuple[float, float]] = field(default_factory=dict)
    info: dict[str, Any] = field(default_factory=dict)

    def params(self, segment: str | list[str] | tuple[str, ...] | None = None) -> tuple[float, float]:
        """Parameters for the first matching segment key, most specific first."""
        keys = [segment] if isinstance(segment, str) else list(segment or [])
        for key in keys:
            if key in self.segments:
                return self.segments[key]
        return self.pooled

    def p_win(self, price: float, segment: str | list[str] | tuple[str, ...] | None = None) -> float:
        a, b = self.params(segment)
        return sigmoid(a + b * logit(price))

    def to_dict(self) -> dict[str, Any]:
        return {"pooled": list(self.pooled), "segments": {k: list(v) for k, v in self.segments.items()},
                "info": self.info}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EdgeModel":
        return cls(pooled=tuple(d.get("pooled", (0.0, 1.0))),
                   segments={k: tuple(v) for k, v in d.get("segments", {}).items()}, info=d.get("info", {}))

    @classmethod
    def load(cls, path: str | Path) -> "EdgeModel":
        return cls.from_dict(json.loads(Path(path).read_text()))

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + "\n")


def segment_keys(category: str, outcome0: str, outcome: int, neg_risk: bool) -> list[str]:
    """Segment keys for one side of one market, most specific first.

    The split the research supports (in both the holdout and the newer
    sample) is between a **stand-alone** yes/no market and one **leg of a
    multi-outcome event**: the underpricing of near-certain contracts shows up
    in the former and barely in the latter, where other traders can lock in
    arbitrage across the legs. The same function labels training rows and live
    candidates, so the model can never be applied to a different definition
    than it was fitted on.
    """
    kind = "multi" if neg_risk else "single"
    return [f"{category}|{kind}", f"*|{kind}", category]


@dataclass
class StrategyConfig:
    # --- which contracts qualify
    ask_lo: float = 0.90
    ask_hi: float = 0.97
    dte_lo: float = 3.0                 # scheduled days to the market's end date
    dte_hi: float = 60.0
    categories: tuple[str, ...] = ("politics", "geopolitics", "finance", "economics", "culture", "tech")
    min_volume: float = 100_000         # shares traded so far (same rule as research)
    max_volume: float | None = None     # skip markets that have traded this many shares or more (None = no limit)
    max_spread: float = 0.03
    min_edge: float = 0.01              # estimated profit per share after the fee
    single_only: bool = False           # skip legs of multi-outcome events (they are still logged)
    # Buy only the outcome named "No" of a Yes/No question (the other side is
    # still logged). At the same near-certain price "No" earned 3.6 points a
    # trade more than "Yes" across three universes (t = 4.4): the crowd is too
    # sure that things will happen. See docs/05_third_round.md.
    no_side_only: bool = False
    # Only buy outcomes whose traded price has stayed within quiet_range over
    # the last quiet_days days, in a market older than that (0 = no such
    # filter). See trading/quiet.py and docs/04_second_round.md.
    quiet_days: float = 0.0
    quiet_range: float = 0.03
    # Skip outcomes whose traded price has ranged more than busy_range over
    # the last busy_days days, in a market older than that (0 = no such
    # filter). The opposite end of the same measure: a favourite that has
    # just moved a long way earned about half as much in both rounds.
    busy_days: float = 0.0
    busy_range: float = 0.15
    # The rule was tested as "in the band at one day's close, bought the next
    # day if still in the band". The delay matters: it weeds out contracts that
    # are falling through the band. Live, a contract must also have been in the
    # band this many hours ago.
    confirm_hours: float = 18.0
    confirm_slack: float = 0.01         # the earlier price is a mid, the band is defined on the ask
    # wider band that is only *logged* for the forward test, never traded
    watch_lo: float = 0.90
    watch_hi: float = 0.99
    # --- how to trade them
    stake_usd: float = 20.0
    max_new_per_cycle: int = 5
    entry: str = "taker"                # "taker" (cross the spread) or "maker" (rest a bid)
    maker_ttl_hours: float = 12.0
    # With entry "maker": once a market's bids have gone unfilled for this long,
    # pay the ask instead (0 = never). In the thinner markets the bids that never
    # fill are the contracts that never dipped, and those were worth having.
    maker_fallback_hours: float = 0.0
    exit_dte: float | None = None       # sell this many scheduled days before the end; None = hold to resolution
    stop_bid: float | None = None       # sell if the bid falls to this level
    tag: str = "harvest"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["categories"] = list(self.categories)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StrategyConfig":
        d = dict(d)
        if "categories" in d:
            d["categories"] = tuple(d["categories"])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


def is_no_side(info: Any, outcome: int) -> bool:
    """True for the outcome named "No" of a market whose outcomes are named Yes and No."""
    return (outcome == 1 and str(info.outcome0).strip().lower() == "yes" and str(info.outcome1).strip().lower() == "no")


@dataclass
class Candidate:
    market: LiveMarket
    outcome: int
    ask: float
    bid: float
    dte: float
    p_win: float
    fee: float
    edge: float                         # p_win - ask - fee, per share
    daily_return: float                 # edge / ask / days: capital efficiency

    def describe(self) -> str:
        name = self.market.info.outcome0 if self.outcome == 0 else self.market.info.outcome1
        return (f"{self.market.question[:60]} | buy '{name}' at {self.ask:.3f}, est. {self.p_win:.3f}, "
                f"edge {100 * self.edge:.2f}c, {self.dte:.0f}d")


class HarvestStrategy:
    """Buy contracts the crowd underprices because they are boring: the
    near-certain side of markets where the other side is a longshot."""

    def __init__(self, config: StrategyConfig, model: EdgeModel):
        self.cfg = config
        self.model = model

    # ------------------------------------------------------------ candidates
    def candidates(self, markets: dict[int, LiveMarket], now: float) -> list[Candidate]:
        """Contracts the rule may buy: in the trading band with enough estimated edge."""
        return self.scan(markets, now, self.cfg.ask_lo, self.cfg.ask_hi, self.cfg.min_edge, self.cfg.single_only,
                         self.cfg.no_side_only)

    def watchlist(self, markets: dict[int, LiveMarket], now: float) -> list[Candidate]:
        """Everything in the wider logged band, whatever the model thinks of it."""
        return self.scan(markets, now, self.cfg.watch_lo, self.cfg.watch_hi, None, False)

    def band_of(self, ask: float) -> str:
        if ask <= self.cfg.ask_lo:
            return "below"
        return "core" if ask <= self.cfg.ask_hi else "above"

    def scan(self, markets: dict[int, LiveMarket], now: float, lo: float, hi: float,
             min_edge: float | None, single_only: bool = False, no_only: bool = False) -> list[Candidate]:
        cfg = self.cfg
        out: list[Candidate] = []
        for lm in markets.values():
            info = lm.info
            if lm.closed or not lm.accepting_orders or lm.volume < cfg.min_volume:
                continue
            if cfg.max_volume is not None and lm.volume >= cfg.max_volume:
                continue
            if single_only and info.neg_risk:
                continue
            if info.category not in cfg.categories:
                continue
            if not (info.end_ts == info.end_ts):          # NaN end date
                continue
            dte = (info.end_ts - now) / 86_400
            if not (cfg.dte_lo < dte <= cfg.dte_hi):
                continue
            for outcome in (0, 1):
                if no_only and not is_no_side(info, outcome):
                    continue
                ask, bid = lm.ask(outcome), lm.bid(outcome)
                if ask is None or bid is None or not (lo < ask <= hi):
                    continue
                if ask - bid > cfg.max_spread + 1e-9 or ask - bid < -1e-9:
                    continue
                p = self.model.p_win(ask, segment_keys(info.category, info.outcome0, outcome, info.neg_risk))
                fee = taker_fee_per_share(ask, info.fee_rate, info.fee_exponent) if cfg.entry == "taker" else 0.0
                edge = p - ask - fee
                if min_edge is not None and edge < min_edge:
                    continue
                out.append(Candidate(lm, outcome, ask, bid, dte, p, fee, edge, edge / ask / max(dte, 1.0)))
        out.sort(key=lambda c: c.daily_return, reverse=True)
        return out

    # ---------------------------------------------------------------- decide
    def decide(
        self,
        markets: dict[int, LiveMarket],
        portfolio: Portfolio,
        open_orders: list[Order],
        now: float,
        confirmed: set[tuple[int, int]] | None = None,
        max_new: int | None = None,
        cross: set[int] | None = None,
    ) -> list[Intent]:
        """Orders the strategy wants. ``confirmed`` is the set of (market id,
        outcome) that were also in the band ``confirm_hours`` ago; when given,
        nothing else is bought. Exits never need confirmation. ``max_new``
        overrides the per-cycle number of entries proposed (the engine asks for
        more than it will place, because the risk limits may refuse some).
        ``cross`` names markets in which a maker strategy has waited long
        enough and should pay the ask this time."""
        cfg = self.cfg
        intents: list[Intent] = []
        held_markets = {p.market_id for p in portfolio.positions.values()}
        working_markets = {o.market_id for o in open_orders}

        # exits first: they free capital and are never blocked by risk limits
        for token, pos in portfolio.positions.items():
            lm = markets.get(pos.market_id)
            if lm is None or lm.closed or pos.tag != cfg.tag:
                continue
            outcome = lm.info.outcome_of(token)
            bid = lm.bid(outcome)
            if bid is None:
                continue
            dte = (lm.info.end_ts - now) / 86_400 if lm.info.end_ts == lm.info.end_ts else float("inf")
            reason = None
            if cfg.exit_dte is not None and dte <= cfg.exit_dte:
                reason = f"time exit: {dte:.1f} days to scheduled end"
            elif cfg.stop_bid is not None and bid <= cfg.stop_bid:
                reason = f"stop: bid {bid:.3f} <= {cfg.stop_bid:.3f}"
            if reason and not any(o.token == token and o.side == Side.SELL for o in open_orders):
                intents.append(Intent("place", pos.market_id, token, Side.SELL, OrderKind.TAKER,
                                      round_to_tick(bid, lm.info.tick, Side.SELL), pos.shares,
                                      reason=reason, tag=cfg.tag))

        # entries
        limit = cfg.max_new_per_cycle if max_new is None else max_new
        placed = 0
        for c in self.candidates(markets, now):
            if placed >= limit:
                break
            info = c.market.info
            if info.market_id in held_markets or info.market_id in working_markets:
                continue
            if confirmed is not None and (info.market_id, c.outcome) not in confirmed:
                continue
            intent = self.entry_intent(c, now, cross=bool(cross) and info.market_id in cross)
            if intent is None:
                continue
            intents.append(intent)
            placed += 1
        return intents

    def entry_intent(self, c: Candidate, now: float, cross: bool = False) -> Intent | None:
        """The order that would open a position in this candidate, or None if
        the stake buys less than the market's minimum size. ``cross`` makes a
        maker strategy pay the ask for once."""
        cfg = self.cfg
        info = c.market.info
        if cfg.entry == "maker" and not cross:
            # join the best bid, as in the backtest: earn the spread, pay no fee
            price = round_to_tick(c.bid, info.tick, Side.BUY)
            kind, expires = OrderKind.MAKER, now + cfg.maker_ttl_hours * 3600
        else:
            price = round_to_tick(c.ask, info.tick, Side.SELL)   # limit exactly at the ask
            kind, expires = OrderKind.TAKER, None
        size = math.floor(cfg.stake_usd / price * 100) / 100
        if size < info.min_size:
            return None
        return Intent("place", info.market_id, info.token(c.outcome), Side.BUY, kind, price, size, expires_ts=expires,
                      reason=c.describe(), tag=cfg.tag,
                      meta={"edge": c.edge + c.fee, "p_win": c.p_win, "dte": c.dte})
