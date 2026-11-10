"""One trading cycle, and the state it carries between cycles.

A cycle is: look at the market, bring the ledger up to date (fills,
resolutions), check the kill switch, ask the strategy what it wants, pass each
request through the risk limits, hand the survivors to the broker, write
everything down. It is designed to be run by a scheduler every few minutes to
hours; nothing is kept in memory between cycles.
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..api import Polymarket
from .broker import Broker, PaperBroker
from .models import Fill, MarketInfo, OrderStatus
from .portfolio import Portfolio
from .risk import RiskLimits, RiskManager, RiskState
from .strategy import EdgeModel, HarvestStrategy, StrategyConfig
from .universe import LiveMarket, fetch_markets, scan_open, theme_tags

STATE_VERSION = 1


@dataclass
class CycleReport:
    ts: float
    equity: float
    cash: float
    invested: float
    n_positions: int
    n_open_orders: int
    n_candidates: int
    new_fills: int
    settled: int
    placed: int
    rejected: int
    halted: bool
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class StateStore:
    """JSON + CSV files in one directory; small enough to commit to git."""

    def __init__(self, directory: str | Path):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    @property
    def state_path(self) -> Path:
        return self.dir / "state.json"

    def load(self) -> dict[str, Any] | None:
        if not self.state_path.exists():
            return None
        return json.loads(self.state_path.read_text())

    def save(self, state: dict[str, Any]) -> None:
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n")
        tmp.replace(self.state_path)

    def append_csv(self, name: str, row: dict[str, Any]) -> None:
        path = self.dir / name
        new = not path.exists()
        with path.open("a", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)

    def append_jsonl(self, name: str, obj: dict[str, Any]) -> None:
        with (self.dir / name).open("a") as fh:
            fh.write(json.dumps(obj, sort_keys=True) + "\n")


class Engine:
    def __init__(
        self,
        pm: Polymarket,
        store: StateStore,
        strategy: HarvestStrategy,
        limits: RiskLimits,
        mode: str = "paper",
    ):
        if mode not in ("paper", "live"):
            raise ValueError(f"unknown mode {mode!r}")
        self.pm = pm
        self.store = store
        self.strategy = strategy
        self.limits = limits
        self.mode = mode
        raw = store.load()
        if raw is not None and raw.get("mode", mode) != mode:
            raise ValueError(f"state in {store.dir} belongs to {raw.get('mode')!r} mode, not {mode!r}: "
                             "paper and live accounts must not share a state directory")
        self.portfolio = Portfolio(cash=limits.bankroll) if raw is None else Portfolio.from_dict(raw["portfolio"])
        self.broker: Broker = self._make_broker(raw)
        self.risk = RiskManager(limits) if raw is None else RiskManager(limits, RiskState(**raw["risk"]))
        self.market_names: dict[str, dict[str, Any]] = {} if raw is None else raw.get("market_names", {})
        self.started_ts = time.time() if raw is None else raw.get("started_ts", time.time())

    def _make_broker(self, raw: dict[str, Any] | None) -> Broker:
        saved = {} if raw is None else raw.get("broker", {})
        if self.mode == "paper":
            return PaperBroker.from_dict(self.pm, self.portfolio, saved)
        # live: every precondition is checked on every start, not just the first
        from .live import LiveBroker, connect, preflight

        preflight(self.pm)
        return LiveBroker.from_dict(connect(), self.portfolio, saved, max_order_usd=self.limits.max_order_usd)

    # ----------------------------------------------------------------- cycle
    def run_cycle(self, now: float | None = None) -> CycleReport:
        now = time.time() if now is None else now
        notes: list[str] = []

        markets = scan_open(self.pm, self.strategy.cfg.min_volume)
        # markets we are involved in may have closed and dropped out of the scan
        involved = {p.market_id for p in self.portfolio.positions.values()} | {
            o.market_id for o in self.broker.open_orders()}
        missing = sorted(involved - set(markets))
        if missing:
            markets.update(fetch_markets(self.pm, missing))
        infos: dict[int, MarketInfo] = {mid: lm.info for mid, lm in markets.items()}

        # 1. fills on resting orders
        fills = self.broker.sync(infos, now)
        for f in fills:
            self._log_fill(f, markets)

        # 2. resolutions
        settled = self._settle(markets, now, notes)

        # 3. cancel orders in markets that have closed
        for o in self.broker.open_orders():
            lm = markets.get(o.market_id)
            if lm is None or lm.closed or not lm.accepting_orders:
                self.broker.cancel(o.order_id, now)

        # 4. mark to the bid (what we could actually sell for) and check limits
        marks = self._marks(markets)
        equity = self.portfolio.equity(marks)
        self.risk.update(equity, now)
        if self.risk.state.halted:
            notes.append(f"HALTED: {self.risk.state.halt_reason}")
            for o in self.broker.open_orders():
                if o.side.value == "BUY":
                    self.broker.cancel(o.order_id, now)

        # 5. strategy -> risk -> broker
        candidates = self.strategy.candidates(markets, now)
        intents = self.strategy.decide(markets, self.portfolio, self.broker.open_orders(), now)
        market_event = {mid: lm.info.event_id for mid, lm in markets.items()}
        themes = theme_tags(markets)
        # a held market that has dropped out of the scan keeps the themes it was bought under
        for token, pos in self.portfolio.positions.items():
            saved = self.market_names.get(token, {}).get("themes")
            if saved and not themes.get(pos.market_id):
                themes[pos.market_id] = frozenset(saved)
        placed = rejected = 0
        for it in intents:
            info = infos[it.market_id]
            ok, why = self.risk.check(it, info, self.portfolio, self.broker.open_orders(), market_event, themes)
            if not ok:
                rejected += 1
                self.store.append_jsonl("decisions.jsonl", {"ts": now, "action": "blocked", "why": why,
                                                            "market_id": it.market_id, "reason": it.reason})
                continue
            order, new_fills = self.broker.place(it, info, now)
            self._remember(markets[it.market_id], it.token, themes.get(it.market_id, frozenset()))
            self.store.append_jsonl("decisions.jsonl", {
                "ts": now, "action": "order", "order_id": order.order_id, "status": order.status.value,
                "market_id": it.market_id, "side": it.side.value, "kind": it.kind.value, "price": it.price,
                "size": it.size, "filled": order.filled, "reason": it.reason, **{k: v for k, v in it.meta.items()}})
            if order.status != OrderStatus.REJECTED:
                placed += 1
            for f in new_fills:
                self._log_fill(f, markets)
            fills.extend(new_fills)

        # 6. write everything down
        marks = self._marks(markets)
        equity = self.portfolio.equity(marks)
        report = CycleReport(
            ts=now, equity=equity, cash=self.portfolio.cash, invested=self.portfolio.invested(),
            n_positions=len(self.portfolio.positions), n_open_orders=len(self.broker.open_orders()),
            n_candidates=len(candidates), new_fills=len(fills), settled=settled, placed=placed,
            rejected=rejected, halted=self.risk.state.halted, notes=notes)
        self.store.append_csv("equity.csv", {
            "ts": int(now), "equity": round(equity, 4), "cash": round(self.portfolio.cash, 4),
            "invested": round(self.portfolio.invested(), 4), "positions": len(self.portfolio.positions),
            "open_orders": len(self.broker.open_orders()), "realized": round(self.portfolio.realized, 4),
            "fees": round(self.portfolio.fees_paid, 4), "candidates": len(candidates)})
        self.last_marks = marks
        self.save()
        return report

    # ------------------------------------------------------------- internals
    def _marks(self, markets: dict[int, LiveMarket]) -> dict[str, float]:
        marks: dict[str, float] = {}
        for token, pos in self.portfolio.positions.items():
            lm = markets.get(pos.market_id)
            if lm is None:
                continue
            bid = lm.bid(lm.info.outcome_of(token))
            if bid is not None:
                marks[token] = bid
        return marks

    def _settle(self, markets: dict[int, LiveMarket], now: float, notes: list[str]) -> int:
        n = 0
        for token, pos in list(self.portfolio.positions.items()):
            lm = markets.get(pos.market_id)
            if lm is None or not lm.closed or lm.final0 is None:
                continue
            if lm.final0 not in (0.0, 1.0, 0.5):
                continue                     # closed but not finally resolved yet
            payoff = lm.final0 if lm.info.outcome_of(token) == 0 else 1.0 - lm.final0
            pnl = self.portfolio.settle(token, payoff)
            n += 1
            notes.append(f"settled {lm.question[:50]}: payoff {payoff:g}, pnl {pnl:+.2f}")
            self.store.append_csv("settlements.csv", {
                "ts": int(now), "market_id": pos.market_id, "question": lm.question[:120], "token": token,
                "shares": round(pos.shares, 4), "cost": round(pos.cost, 4), "payoff": payoff, "pnl": round(pnl, 4)})
        return n

    def _remember(self, lm: LiveMarket, token: str, themes: frozenset[str] = frozenset()) -> None:
        outcome = lm.info.outcome_of(token)
        self.market_names[token] = {
            "market_id": lm.info.market_id, "question": lm.question,
            "outcome": lm.info.outcome0 if outcome == 0 else lm.info.outcome1,
            "end_ts": lm.info.end_ts, "category": lm.info.category, "themes": sorted(themes)}

    def _log_fill(self, f: Fill, markets: dict[int, LiveMarket]) -> None:
        lm = markets.get(f.market_id)
        self.store.append_csv("fills.csv", {
            "ts": int(f.ts), "order_id": f.order_id, "market_id": f.market_id,
            "question": (lm.question[:120] if lm else ""), "token": f.token, "side": f.side.value,
            "price": f.price, "size": round(f.size, 4), "fee": round(f.fee, 5), "maker": f.maker, "tag": f.tag})

    def save(self) -> None:
        self.store.save({
            "version": STATE_VERSION, "mode": self.mode, "started_ts": self.started_ts,
            "saved_ts": time.time(), "portfolio": self.portfolio.to_dict(),
            "broker": self.broker.to_dict(), "risk": self.risk.state.to_dict(),
            "limits": self.limits.to_dict(), "strategy": self.strategy.cfg.to_dict(),
            "model": self.strategy.model.to_dict(), "market_names": self.market_names,
            "marks": getattr(self, "last_marks", {}),
        })


def build_engine(pm: Polymarket, state_dir: str | Path, config_path: str | Path) -> Engine:
    """Assemble an engine from a JSON config file (strategy, risk limits, model path)."""
    cfg = json.loads(Path(config_path).read_text())
    strategy_cfg = StrategyConfig.from_dict(cfg.get("strategy", {}))
    limits = RiskLimits(**cfg.get("risk", {}))
    model_path = Path(config_path).parent / cfg.get("model", "model.json")
    model = EdgeModel.load(model_path) if model_path.exists() else EdgeModel()
    return Engine(pm, StateStore(state_dir), HarvestStrategy(strategy_cfg, model), limits, mode=cfg.get("mode", "paper"))
