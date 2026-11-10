"""Strategy decisions and a full engine cycle against a scripted exchange."""

import json

import pytest

from kht.trading.engine import Engine, StateStore
from kht.trading.models import MarketInfo, OrderKind, Side
from kht.trading.portfolio import Portfolio
from kht.trading.risk import RiskLimits
from kht.trading.strategy import EdgeModel, HarvestStrategy, StrategyConfig, logit, sigmoid
from kht.trading.universe import LiveMarket

NOW = 1_800_000_000.0
DAY = 86_400


def live(mid, bid0, ask0, dte=20, category="politics", volume=500_000, fee=0.04, event=None, closed=False,
         final0=None, accepting=True):
    info = MarketInfo(mid, f"0x{mid}", f"Question {mid}?", f"T{mid}a", f"T{mid}b", "Yes", "No",
                      event_id=event if event is not None else mid, category=category, fee_rate=fee,
                      tick=0.01, min_size=5, end_ts=NOW + dte * DAY)
    return LiveMarket(info, bid0, ask0, volume, 1000.0, 5000.0, accepting, closed,
                      None if final0 is None else (0.0 if final0 == 1 else 1.0), final0, f"Question {mid}?")


MODEL = EdgeModel(pooled=(0.0, 1.3))     # compressed prices: 93c really pays ~96.6%
CFG = StrategyConfig(ask_lo=0.90, ask_hi=0.97, dte_lo=3, dte_hi=60, stake_usd=20, min_edge=0.01)


def test_edge_model_is_identity_at_slope_one_and_stretches_above():
    assert EdgeModel().p_win(0.93) == pytest.approx(0.93)
    assert MODEL.p_win(0.93) > 0.93 and MODEL.p_win(0.07) < 0.07
    assert MODEL.p_win(0.93) == pytest.approx(sigmoid(1.3 * logit(0.93)))
    assert EdgeModel(pooled=(0, 1.0), segments={"politics": (0, 1.5)}).p_win(0.9, "politics") > 0.9
    again = EdgeModel.from_dict(json.loads(json.dumps(MODEL.to_dict())))
    assert again.p_win(0.93) == MODEL.p_win(0.93)


def test_strategy_buys_the_expensive_side_whichever_outcome_it_is():
    s = HarvestStrategy(CFG, MODEL)
    mk = {1: live(1, 0.92, 0.93),            # Yes is the favourite: buy Yes at 0.93
          2: live(2, 0.06, 0.07)}            # No is the favourite: buy No at 1 - 0.06 = 0.94
    intents = s.decide(mk, Portfolio(1000), [], NOW)
    got = {i.market_id: i for i in intents}
    assert got[1].token == "T1a" and got[1].price == pytest.approx(0.93)
    assert got[2].token == "T2b" and got[2].price == pytest.approx(0.94)
    assert all(i.side == Side.BUY and i.kind == OrderKind.TAKER for i in intents)
    assert got[1].size == pytest.approx(21.5)          # $20 / 0.93, rounded down to 0.01 share


@pytest.mark.parametrize("market", [
    live(1, 0.50, 0.51),                               # not a favourite
    live(1, 0.975, 0.985),                             # above the price window
    live(1, 0.92, 0.93, dte=1),                        # too close to the end
    live(1, 0.92, 0.93, dte=200),                      # too far
    live(1, 0.92, 0.93, category="sports"),            # category not allowed
    live(1, 0.92, 0.93, volume=5_000),                 # has not traded enough
    live(1, 0.85, 0.93),                               # spread too wide
    live(1, 0.92, 0.93, accepting=False),
])
def test_strategy_skips_what_it_should(market):
    assert HarvestStrategy(CFG, MODEL).decide({1: market}, Portfolio(1000), [], NOW) == []


def test_no_edge_no_trade():
    fair = HarvestStrategy(CFG, EdgeModel(pooled=(0.0, 1.0)))     # prices are right -> fee makes edge negative
    assert fair.decide({1: live(1, 0.92, 0.93)}, Portfolio(1000), [], NOW) == []


def test_ranks_by_return_per_day_and_caps_new_orders():
    cfg = StrategyConfig(**{**CFG.to_dict(), "max_new_per_cycle": 1, "categories": ("politics",)})
    s = HarvestStrategy(cfg, MODEL)
    mk = {1: live(1, 0.92, 0.93, dte=50), 2: live(2, 0.92, 0.93, dte=5)}
    intents = s.decide(mk, Portfolio(1000), [], NOW)
    assert [i.market_id for i in intents] == [2]         # same edge, ten times faster


def test_time_exit_sells_at_the_bid():
    cfg = StrategyConfig(**{**CFG.to_dict(), "exit_dte": 3.0, "categories": ("politics",)})
    s = HarvestStrategy(cfg, MODEL)
    pf = Portfolio(1000)
    from kht.trading.models import Fill
    pf.apply(Fill("x", 1, "T1a", Side.BUY, 0.93, 20, 0.0, NOW, maker=False, tag="harvest"))
    intents = s.decide({1: live(1, 0.96, 0.97, dte=2)}, pf, [], NOW)
    assert len(intents) == 1 and intents[0].side == Side.SELL and intents[0].price == pytest.approx(0.96)


# -------------------------------------------------------------------- engine
class FakePM:
    """Just enough of kht.api.Polymarket for an engine cycle."""

    def __init__(self, markets):
        self.markets = markets
        self.tape = {}

    def book(self, token):
        for lm in self.markets.values():
            for outcome in (0, 1):
                if lm.info.token(outcome) == token:
                    return {"bids": [{"price": str(lm.bid(outcome)), "size": "5000"}],
                            "asks": [{"price": str(lm.ask(outcome)), "size": "5000"}]}
        raise KeyError(token)

    def iter_trades(self, condition, max_pages=None):
        return iter(self.tape.get(condition, []))


@pytest.fixture
def engine(tmp_path, monkeypatch):
    markets = {1: live(1, 0.92, 0.93, event=10), 2: live(2, 0.06, 0.07, event=10), 3: live(3, 0.50, 0.52)}
    pm = FakePM(markets)
    import kht.trading.engine as eng
    monkeypatch.setattr(eng, "scan_open", lambda pm_, min_volume: {k: v for k, v in pm_.markets.items() if not v.closed})
    monkeypatch.setattr(eng, "fetch_markets", lambda pm_, ids: {i: pm_.markets[i] for i in ids})
    limits = RiskLimits(bankroll=1000, max_position_usd=25, max_event_usd=30, max_order_usd=25)
    e = Engine(pm, StateStore(tmp_path), HarvestStrategy(CFG, MODEL), limits)
    return e, pm, tmp_path, limits


def test_cycle_buys_respects_event_cap_and_persists(engine):
    e, pm, path, limits = engine
    rep = e.run_cycle(NOW)
    # markets 1 and 2 share an event capped at $30: the second $20 order is blocked
    assert rep.placed == 1 and rep.rejected == 1
    assert rep.n_positions == 1
    assert rep.cash == pytest.approx(1000 - e.portfolio.invested())
    assert rep.equity < 1000            # marked at the bid, and the taker fee is gone
    assert (path / "state.json").exists() and (path / "fills.csv").exists() and (path / "equity.csv").exists()
    # a fresh engine picks up exactly where this one stopped
    e2 = Engine(pm, StateStore(path), HarvestStrategy(CFG, MODEL), limits)
    assert e2.portfolio.cash == pytest.approx(e.portfolio.cash)
    assert set(e2.portfolio.positions) == set(e.portfolio.positions)
    rep2 = e2.run_cycle(NOW + 600)
    assert rep2.placed == 0             # already holding; nothing new qualifies under the cap


def test_cycle_settles_resolved_markets(engine):
    e, pm, path, limits = engine
    e.run_cycle(NOW)
    token, pos = next(iter(e.portfolio.positions.items()))
    mid = pos.market_id
    won_final0 = 1.0 if token.endswith("a") else 0.0
    pm.markets[mid] = live(mid, None, None, event=10, closed=True, final0=won_final0, accepting=False)
    rep = e.run_cycle(NOW + DAY)
    assert rep.settled == 1 and mid not in {p.market_id for p in e.portfolio.positions.values()}
    assert e.portfolio.realized == pytest.approx(pos.shares * 1.0 - pos.cost)
    assert (path / "settlements.csv").exists()


def test_split_resolution_pays_half(engine):
    e, pm, path, limits = engine
    e.run_cycle(NOW)
    token, pos = next(iter(e.portfolio.positions.items()))
    pm.markets[pos.market_id] = live(pos.market_id, None, None, event=10, closed=True, final0=0.5, accepting=False)
    e.run_cycle(NOW + DAY)
    assert e.portfolio.realized == pytest.approx(pos.shares * 0.5 - pos.cost)


def test_kill_switch_stops_new_buying(engine):
    e, pm, path, limits = engine
    e.risk.state.halted = True
    e.risk.state.halt_reason = "test"
    rep = e.run_cycle(NOW)
    assert rep.halted and rep.placed == 0 and rep.n_positions == 0


def test_segment_lookup_prefers_the_most_specific_key():
    from kht.trading.strategy import segment_keys
    m = EdgeModel(pooled=(0.0, 1.0), segments={"politics|no_single": (0.5, 1.0), "*|no_single": (0.3, 1.0),
                                               "politics": (0.1, 1.0)})
    keys = segment_keys("politics", "Yes", 1, False)
    assert keys == ["politics|no_single", "*|no_single", "politics"]
    assert m.params(keys) == (0.5, 1.0)
    assert m.params(segment_keys("tech", "Yes", 1, False)) == (0.3, 1.0)          # falls back to the cross-category key
    assert m.params(segment_keys("politics", "Yes", 0, False)) == (0.1, 1.0)      # buying Yes is not the special corner
    assert m.params(segment_keys("politics", "Yes", 1, True)) == (0.1, 1.0)       # nor is a leg of a multi-outcome event
    assert m.params(segment_keys("weather", "Lakers", 1, False)) == (0.0, 1.0)    # nothing matches -> pooled


def test_theme_tags_keeps_narrow_tags_and_drops_broad_ones():
    from dataclasses import replace
    from kht.trading.universe import theme_tags
    mk = {}
    for i in range(100):
        lm = live(i, 0.5, 0.52)
        tags = ("politics",) + (("hormuz",) if i < 3 else ()) + (("unique-%d" % i,) if i == 50 else ())
        mk[i] = LiveMarket(replace(lm.info, tags=tags), lm.best_bid0, lm.best_ask0, lm.volume, lm.volume_24h,
                           lm.liquidity, lm.accepting_orders, lm.closed, lm.winner, lm.final0, lm.question)
    th = theme_tags(mk)
    assert th[0] == frozenset({"hormuz"})          # shared by 3 of 100: a story
    assert th[10] == frozenset()                   # 'politics' is on everything: a category
    assert th[50] == frozenset()                   # a tag on a single market groups nothing
