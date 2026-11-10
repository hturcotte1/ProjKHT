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
SHADOW_RECHECK_SECONDS = 6 * 3600


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
        # signals already written to the forward-test log (see _log_shadow)
        self.shadow_seen: set[str] = set() if raw is None else {str(x) for x in raw.get("shadow_seen", [])}
        # signals that were not yet a day old when last checked, and when that was
        self.shadow_pending: dict[str, float] = {} if raw is None else dict(raw.get("shadow_pending", {}))
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
        market_event = {mid: lm.info.event_id for mid, lm in markets.items()}
        themes = self._sticky_themes(markets, theme_tags(markets, max_share=self.limits.theme_max_share))
        max_new = self.strategy.cfg.max_new_per_cycle
        # Only the best-ranked few can be bought this cycle, so only they need a
        # history lookup; and only candidates the limits would accept are worth
        # one. Without that screen, a story that is already at its cap can fill
        # the whole shortlist every cycle and the account never reaches the
        # next valid candidate.
        busy = {p.market_id for p in self.portfolio.positions.values()} | {o.market_id for o in self.broker.open_orders()}
        shortlist = []
        screened: dict[str, int] = {}
        for c in candidates:
            if len(shortlist) >= 6 * max_new:
                break
            if c.market.info.market_id in busy:
                continue
            probe = self.strategy.entry_intent(c, now)
            if probe is None:
                continue
            ok, why = self.risk.check(probe, c.market.info, self.portfolio, self.broker.open_orders(),
                                      market_event, themes)
            if ok:
                shortlist.append(c)
            else:
                key = why.split(" exposure")[0].split(":")[0]       # "theme 'iran'", "event", "halted", ...
                screened[key] = screened.get(key, 0) + 1
        if screened:
            # one line per cycle rather than one per candidate: the same few dozen would repeat every three hours
            self.store.append_jsonl("decisions.jsonl", {"ts": now, "action": "screened", "count": sum(screened.values()),
                                                        "by_limit": screened})
        confirmed = self._confirmed(shortlist, now)
        self._log_shadow(self.strategy.watchlist(markets, now), now)
        intents = self.strategy.decide(markets, self.portfolio, self.broker.open_orders(), now, confirmed,
                                       max_new=len(shortlist))
        placed = rejected = opened = 0
        for it in intents:
            entry = it.action == "place" and it.side.value == "BUY"
            if entry and opened >= max_new:
                continue                     # the per-cycle budget counts orders placed, not orders proposed
            info = infos[it.market_id]
            ok, why = self.risk.check(it, info, self.portfolio, self.broker.open_orders(), market_event, themes)
            if not ok:
                rejected += 1
                self.store.append_jsonl("decisions.jsonl", {"ts": now, "action": "blocked", "why": why,
                                                            "market_id": it.market_id, "reason": it.reason})
                continue
            try:
                order, new_fills = self.broker.place(it, info, now)
            except Exception as exc:  # noqa: BLE001 - one failed order must not abort the cycle
                rejected += 1
                notes.append(f"order failed for market {it.market_id}: {exc!r}"[:200])
                self.store.append_jsonl("decisions.jsonl", {"ts": now, "action": "error", "why": repr(exc)[:300],
                                                            "market_id": it.market_id, "reason": it.reason})
                continue
            self._remember(markets[it.market_id], it.token, themes.get(it.market_id, frozenset()))
            # Persist straight away: if anything later in the cycle fails, the
            # record of an order that has already been sent must survive.
            self.save()
            self.store.append_jsonl("decisions.jsonl", {
                "ts": now, "action": "order", "order_id": order.order_id, "status": order.status.value,
                "market_id": it.market_id, "side": it.side.value, "kind": it.kind.value, "price": it.price,
                "size": it.size, "filled": order.filled, "reason": it.reason, **{k: v for k, v in it.meta.items()}})
            if order.status != OrderStatus.REJECTED:
                placed += 1
                opened += int(entry)
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

    def _was_in_band(self, c: Any, lo: float, hi: float, now: float) -> bool | None:
        """Was this contract already in (lo, hi] ``confirm_hours`` ago?  None = could not tell."""
        cfg = self.strategy.cfg
        key = (c.market.info.market_id, c.outcome)
        cache = self._history_cache
        if key not in cache:
            try:
                cache[key] = self.pm.price_as_of(c.market.info.token(c.outcome), now - cfg.confirm_hours * 3600)
            except Exception:  # noqa: BLE001 - no history means no confirmation, not a crash
                cache[key] = None
        then = cache[key]
        if then is None:
            return None
        return lo - cfg.confirm_slack < then <= hi + 0.005

    def _confirmed(self, candidates: list[Any], now: float) -> set[tuple[int, int]]:
        """Tradable candidates that were also in the trading band a day ago."""
        self._history_cache: dict[tuple[int, int], float | None] = {}
        cfg = self.strategy.cfg
        if cfg.confirm_hours <= 0:
            return {(c.market.info.market_id, c.outcome) for c in candidates}
        return {(c.market.info.market_id, c.outcome) for c in candidates
                if self._was_in_band(c, cfg.ask_lo, cfg.ask_hi, now)}

    def _log_shadow(self, watch: list[Any], now: float) -> None:
        """Forward-test log: every signal the first time it appears, whether or
        not there is capital to trade it, and including the price bands that
        did not pass the historical test.

        The account can only hold a few dozen positions, so on its own it would
        take a long time to say anything statistically. Scoring *all* signals
        once their markets resolve (``kht shadow``) tests the rules on live,
        never-before-seen data many times faster. Each signal is logged once
        per band, at the moment it satisfies the same next-day confirmation as
        a real trade.
        """
        cfg = self.strategy.cfg
        bands = {"below": (cfg.watch_lo, cfg.ask_lo), "core": (cfg.ask_lo, cfg.ask_hi), "above": (cfg.ask_hi, cfg.watch_hi)}
        for c in watch:
            info = c.market.info
            band = self.strategy.band_of(c.ask)
            key = f"{info.market_id}:{band}"
            if key in self.shadow_seen:
                continue
            lo, hi = bands[band]
            if cfg.confirm_hours > 0:
                # a signal that failed the wait is looked up again only after a few hours
                if now - self.shadow_pending.get(key, 0.0) < SHADOW_RECHECK_SECONDS:
                    continue
                if not self._was_in_band(c, lo, hi, now):
                    self.shadow_pending[key] = now
                    continue
            self.shadow_pending.pop(key, None)
            self.shadow_seen.add(key)
            self.store.append_csv("shadow.csv", {
                "ts": int(now), "market_id": info.market_id, "band": band, "token": info.token(c.outcome),
                "outcome": c.outcome, "outcome_name": info.outcome0 if c.outcome == 0 else info.outcome1,
                "question": c.market.question[:140], "category": info.category, "event_id": info.event_id,
                "neg_risk": int(info.neg_risk), "ask": round(c.ask, 4), "bid": round(c.bid, 4),
                "fee_ps": round(c.fee, 5), "p_model": round(c.p_win, 4), "edge": round(c.edge, 4),
                "tradable": int(band == "core" and c.edge >= cfg.min_edge
                                and not (cfg.single_only and info.neg_risk)),
                "dte": round(c.dte, 2), "end_ts": int(info.end_ts)})

    def _sticky_themes(self, markets: dict[int, LiveMarket],
                       themes: dict[int, frozenset[str]]) -> dict[int, frozenset[str]]:
        """Keep a story capped for as long as the account is exposed to it.

        Whether a tag counts as a theme is recomputed every cycle from its
        share of open markets, and a held market that has closed is re-read
        without its tags. Left alone, the per-theme cap would lapse exactly
        when a story grows past the share that defines a theme, or when its
        markets start closing. So every position and resting order keeps the
        themes it was bought under, and those tags stay themes for any other
        market that carries them.
        """
        involved = {token: pos.market_id for token, pos in self.portfolio.positions.items()}
        involved.update({o.token: o.market_id for o in self.broker.open_orders()})
        held: set[str] = set()
        for token, market_id in involved.items():
            saved = frozenset(self.market_names.get(token, {}).get("themes") or ())
            if saved:
                themes[market_id] = themes.get(market_id, frozenset()) | saved
                held |= saved
        if held:
            for market_id, lm in markets.items():
                extra = held.intersection(lm.info.tags)
                if extra:
                    themes[market_id] = themes.get(market_id, frozenset()) | extra
        return themes

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
            "shadow_seen": sorted(self.shadow_seen),
            # forget pending checks older than two weeks so the file cannot grow without bound
            "shadow_pending": {k: v for k, v in self.shadow_pending.items() if time.time() - v < 14 * 86_400},
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
