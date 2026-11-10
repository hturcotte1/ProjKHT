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

    def iter_trades(self, condition, page_size=1000, max_pages=None):
        self.tape_reads = getattr(self, "tape_reads", 0) + 1
        return iter(sorted(self.tape.get(condition, []), key=lambda t: -t["timestamp"]))

    history = None      # token -> mid a day ago; default: the same as now

    def price_as_of(self, token, ts):
        if self.history is not None and token in self.history:
            return self.history[token]
        for lm in self.markets.values():
            for outcome in (0, 1):
                if lm.info.token(outcome) == token:
                    return 0.5 * (lm.bid(outcome) + lm.ask(outcome))
        return None


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


def test_settlement_accepts_rounding_dust_but_not_a_last_quote(engine):
    e, pm, path, limits = engine
    e.run_cycle(NOW)
    token, pos = next(iter(e.portfolio.positions.items()))
    mid = pos.market_id
    won = 1.0 if token.endswith("a") else 0.0
    # closed, but still showing its last quote rather than a result: nothing to settle yet
    last_quote = live(mid, None, None, event=10, closed=True, final0=1.0, accepting=False)
    last_quote.final0 = 0.9995 if won == 1.0 else 0.0005
    pm.markets[mid] = last_quote
    assert e.run_cycle(NOW + DAY).settled == 0 and token in e.portfolio.positions
    # resolved, reported with rounding dust instead of an exact 1 or 0
    dusty = live(mid, None, None, event=10, closed=True, final0=1.0, accepting=False)
    dusty.final0 = 0.999999 if won == 1.0 else 0.000001
    pm.markets[mid] = dusty
    assert e.run_cycle(NOW + 2 * DAY).settled == 1
    assert e.portfolio.realized == pytest.approx(pos.shares * 1.0 - pos.cost)


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


def test_an_empty_side_of_the_book_is_not_a_price():
    # Gamma reports an ask of 1 for outcome 0 when nobody offers it
    assert live(1, 0.02, 1.0).bid(1) is None           # outcome 0 is cheap and unoffered: the book is empty there
    assert live(1, None, 1.0).bid(1) is None           # nothing on either side
    assert live(1, 0.995, 1.0).bid(1) == pytest.approx(0.0)   # outcome 0 really is near-certain: the other is worthless
    assert live(1, None, 0.002).bid(1) == pytest.approx(0.998)  # the ordinary case for a winning "No"
    assert live(1, 0.02, 0.03).bid(1) == pytest.approx(0.97)


def test_an_empty_book_does_not_trip_the_kill_switch_but_a_collapse_does(tmp_path, monkeypatch):
    markets = {2: live(2, 0.03, 0.04)}                 # "No" is the favourite at 0.97
    pm = FakePM(markets)
    import kht.trading.engine as eng
    monkeypatch.setattr(eng, "scan_open", lambda pm_, min_volume: {k: v for k, v in pm_.markets.items() if not v.closed})
    monkeypatch.setattr(eng, "fetch_markets", lambda pm_, ids: {i: pm_.markets[i] for i in ids})
    limits = RiskLimits(bankroll=1000, max_position_usd=25, max_event_usd=30, max_order_usd=25, daily_loss_limit_usd=10)
    e = Engine(pm, StateStore(tmp_path), HarvestStrategy(CFG, MODEL), limits)
    assert e.run_cycle(NOW).n_positions == 1
    # the book empties: no bid for "No" is not the same as "No" being worth nothing
    pm.markets[2] = live(2, 0.02, 1.0)
    rep = e.run_cycle(NOW + 600)
    assert not rep.halted and rep.equity == pytest.approx(1000, abs=1.0)
    # a real collapse, with outcome 0 now bid at 0.90, is a real loss and must halt buying
    pm.markets[2] = live(2, 0.90, 0.92)
    rep = e.run_cycle(NOW + 1200)
    assert rep.halted and rep.equity < 990


def test_a_story_stays_capped_after_it_outgrows_the_definition_of_a_theme(tmp_path, monkeypatch):
    from dataclasses import replace

    def tagged(lm, *tags):
        return LiveMarket(replace(lm.info, tags=tags), lm.best_bid0, lm.best_ask0, lm.volume, lm.volume_24h,
                          lm.liquidity, lm.accepting_orders, lm.closed, lm.winner, lm.final0, lm.question)

    # forty quiet markets, and one story ("hormuz") on two of them: a theme by any definition
    markets = {i: tagged(live(i, 0.50, 0.52), "politics") for i in range(100, 140)}
    markets[1] = tagged(live(1, 0.92, 0.93), "politics", "hormuz")
    markets[2] = tagged(live(2, 0.50, 0.52), "politics", "hormuz")
    pm = FakePM(markets)
    import kht.trading.engine as eng
    monkeypatch.setattr(eng, "scan_open", lambda pm_, min_volume: {k: v for k, v in pm_.markets.items() if not v.closed})
    monkeypatch.setattr(eng, "fetch_markets", lambda pm_, ids: {i: pm_.markets[i] for i in ids})
    limits = RiskLimits(bankroll=1000, max_position_usd=25, max_event_usd=25, max_theme_usd=30, max_order_usd=25)
    e = Engine(pm, StateStore(tmp_path), HarvestStrategy(CFG, MODEL), limits)
    assert e.run_cycle(NOW).placed == 1                       # market 1, bought under the theme "hormuz"
    # the story spreads: now thirty of the open markets carry the tag, far more than a tenth of them
    for i in range(100, 130):
        pm.markets[i] = tagged(live(i, 0.50, 0.52), "politics", "hormuz")
    pm.markets[3] = tagged(live(3, 0.92, 0.93), "politics", "hormuz")   # a new candidate about the same story
    from kht.trading.universe import theme_tags
    assert theme_tags(pm.markets)[3] == frozenset()            # by share alone it is no longer a theme
    rep = e.run_cycle(NOW + 600)
    assert rep.placed == 0 and rep.n_positions == 1            # but the account is exposed to it, so the cap holds
    last = [json.loads(l) for l in (tmp_path / "decisions.jsonl").read_text().splitlines()][-1]
    assert last["action"] == "screened" and last["by_limit"] == {"theme 'hormuz'": 1}


def test_a_story_that_becomes_a_theme_while_held_stays_capped(tmp_path, monkeypatch):
    from dataclasses import replace
    from kht.trading.universe import theme_tags

    def tagged(lm, *tags):
        return LiveMarket(replace(lm.info, tags=tags), lm.best_bid0, lm.best_ask0, lm.volume, lm.volume_24h,
                          lm.liquidity, lm.accepting_orders, lm.closed, lm.winner, lm.final0, lm.question)

    # At purchase the tag is on every market: a category, not a theme, so nothing is saved with the position.
    markets = {i: tagged(live(i, 0.50, 0.52), "politics", "hormuz") for i in range(100, 140)}
    markets[1] = tagged(live(1, 0.92, 0.93), "politics", "hormuz")
    pm = FakePM(markets)
    import kht.trading.engine as eng
    monkeypatch.setattr(eng, "scan_open", lambda pm_, min_volume: {k: v for k, v in pm_.markets.items() if not v.closed})
    monkeypatch.setattr(eng, "fetch_markets", lambda pm_, ids: {i: pm_.markets[i] for i in ids})
    limits = RiskLimits(bankroll=1000, max_position_usd=25, max_event_usd=25, max_theme_usd=30, max_order_usd=25)
    e = Engine(pm, StateStore(tmp_path), HarvestStrategy(CFG, MODEL), limits)
    assert e.run_cycle(NOW).placed == 1
    token = next(iter(e.portfolio.positions))
    assert e.market_names[token]["themes"] == []

    # The tag narrows to two markets. Now it is a theme, and the position takes note of it.
    for i in range(100, 140):
        pm.markets[i] = tagged(live(i, 0.50, 0.52), "politics")
    pm.markets[2] = tagged(live(2, 0.50, 0.52), "politics", "hormuz")
    e.run_cycle(NOW + 600)
    assert e.market_names[token]["themes"] == ["hormuz"]
    assert json.loads((tmp_path / "state.json").read_text())["market_names"][token]["themes"] == ["hormuz"]

    # It spreads again, past a tenth of all markets, and a new candidate about the same story appears.
    for i in range(100, 130):
        pm.markets[i] = tagged(live(i, 0.50, 0.52), "politics", "hormuz")
    pm.markets[3] = tagged(live(3, 0.92, 0.93), "politics", "hormuz")
    assert theme_tags(pm.markets)[3] == frozenset()            # by share alone it is not a theme
    rep = Engine(pm, StateStore(tmp_path), HarvestStrategy(CFG, MODEL), limits).run_cycle(NOW + 1200)   # a fresh process
    assert rep.placed == 0 and rep.n_positions == 1
    last = [json.loads(l) for l in (tmp_path / "decisions.jsonl").read_text().splitlines()][-1]
    assert last["action"] == "screened" and last["by_limit"] == {"theme 'hormuz'": 1}


def test_candidates_blocked_by_a_cap_do_not_use_up_the_cycle(tmp_path, monkeypatch):
    from dataclasses import replace

    def tagged(lm, *tags):
        return LiveMarket(replace(lm.info, tags=tags), lm.best_bid0, lm.best_ask0, lm.volume, lm.volume_24h,
                          lm.liquidity, lm.accepting_orders, lm.closed, lm.winner, lm.final0, lm.question)

    # quiet background, three markets about one story that rank first (they end soonest), one unrelated market
    markets = {i: tagged(live(i, 0.50, 0.52), "politics") for i in range(100, 140)}
    for i in (1, 2, 3):
        markets[i] = tagged(live(i, 0.92, 0.93, dte=5), "politics", "hormuz")
    markets[4] = tagged(live(4, 0.92, 0.93, dte=40), "politics")
    pm = FakePM(markets)
    import kht.trading.engine as eng
    monkeypatch.setattr(eng, "scan_open", lambda pm_, min_volume: {k: v for k, v in pm_.markets.items() if not v.closed})
    monkeypatch.setattr(eng, "fetch_markets", lambda pm_, ids: {i: pm_.markets[i] for i in ids})
    limits = RiskLimits(bankroll=1000, max_position_usd=25, max_event_usd=25, max_theme_usd=30, max_order_usd=25)
    cfg = replace(CFG, max_new_per_cycle=1)
    e = Engine(pm, StateStore(tmp_path), HarvestStrategy(cfg, MODEL), limits)
    assert e.run_cycle(NOW).placed == 1                     # one order per cycle: the best of the story
    held = {p.market_id for p in e.portfolio.positions.values()}
    assert held <= {1, 2, 3}
    # the story is now at its cap. The next cycle must move on to market 4, not spend itself on the story again
    rep = e.run_cycle(NOW + 600)
    assert rep.placed == 1
    assert {p.market_id for p in e.portfolio.positions.values()} == held | {4}
    # and the cap still held: nothing else about the story was bought
    assert e.run_cycle(NOW + 1200).placed == 0


def test_segment_lookup_prefers_the_most_specific_key():
    from kht.trading.strategy import segment_keys
    m = EdgeModel(pooled=(0.0, 1.0), segments={"politics|single": (0.5, 1.0), "*|single": (0.3, 1.0),
                                               "politics": (0.1, 1.0)})
    keys = segment_keys("politics", "Yes", 1, False)
    assert keys == ["politics|single", "*|single", "politics"]
    assert m.params(keys) == (0.5, 1.0)
    assert m.params(segment_keys("tech", "Yes", 0, False)) == (0.3, 1.0)          # falls back to the cross-category key
    assert m.params(segment_keys("politics", "Yes", 1, True)) == (0.1, 1.0)       # a leg of a multi-outcome event
    assert m.params(segment_keys("weather", "Lakers", 1, True)) == (0.0, 1.0)     # nothing matches -> pooled


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
    assert theme_tags(mk, max_share=0.02)[0] == frozenset()   # a stricter share stops calling it a theme
    assert th[50] == frozenset()                   # a tag on a single market groups nothing


def test_plumbing_tags_are_never_themes():
    from dataclasses import replace
    from kht.trading.universe import theme_tags
    mk = {}
    for i in range(100):
        lm = live(i, 0.5, 0.52)
        # each of these is on 3 markets in 100, which would make a story of it
        tags = ("politics",) + (("yearly", "monthly", "earn-4", "hide-from-new", "parent-for-derivative", "hormuz") if i < 3 else ())
        mk[i] = LiveMarket(replace(lm.info, tags=tags), lm.best_bid0, lm.best_ask0, lm.volume, lm.volume_24h,
                           lm.liquidity, lm.accepting_orders, lm.closed, lm.winner, lm.final0, lm.question)
    assert theme_tags(mk)[0] == frozenset({"hormuz"})


def test_forward_test_log_records_each_signal_once_and_scores_resolutions(engine):
    import csv
    from kht.trading.report import score_shadow
    e, pm, path, limits = engine
    e.run_cycle(NOW)
    e.run_cycle(NOW + 600)                                    # same candidates again
    rows = list(csv.DictReader((path / "shadow.csv").open()))
    assert sorted(int(r["market_id"]) for r in rows) == [1, 2]   # both signals logged, although only one was bought
    assert {r["band"] for r in rows} == {"core"} and {r["tradable"] for r in rows} == {"1"}
    # market 1 resolves Yes (we logged buying Yes -> win); market 2 resolves Yes (we logged buying No -> loss)
    resolved = {1: live(1, None, None, event=10, closed=True, final0=1.0, accepting=False),
                2: live(2, None, None, event=10, closed=True, final0=1.0, accepting=False)}
    res = score_shadow(path, resolved)
    assert res["signals"] == 2 and res["resolved"] == 2 and res["win_rate"] == 0.5
    rets = sorted(x["ret"] for x in res["rows"])
    assert rets[0] == pytest.approx(-1.0) and rets[1] > 0
    assert res["events"] == 1                                  # one event: no standard error is claimed
    assert "t" not in res


def test_forward_test_scores_the_traded_rule_apart_from_legs_and_accepts_rounding_dust(tmp_path):
    import csv
    from kht.trading.report import score_shadow
    cols = ["ts", "market_id", "band", "outcome", "question", "event_id", "neg_risk", "ask", "fee_ps", "p_model",
            "tradable", "end_ts"]
    rows = [  # market, band, leg?, the stale flag deliberately disagrees with what the rule trades today
        (1, "core", 0, 0), (2, "core", 0, 0), (3, "core", 1, 1), (4, "above", 0, 0)]
    with (tmp_path / "shadow.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for mid, band, leg, stale in rows:
            w.writerow({"ts": int(NOW), "market_id": mid, "band": band, "outcome": 0, "question": f"Q{mid}",
                        "event_id": mid, "neg_risk": leg, "ask": 0.96, "fee_ps": 0.0, "p_model": 0.97,
                        "tradable": stale, "end_ts": int(NOW)})
    dusty = live(1, None, None, closed=True, final0=1.0, accepting=False)
    dusty.final0 = 0.999999                                   # resolved, reported with rounding dust
    pending = live(2, None, None, closed=True, final0=1.0, accepting=False)
    pending.final0 = 0.9995                                   # closed, still showing a last quote
    markets = {1: dusty, 2: pending,
               3: live(3, None, None, closed=True, final0=0.0, accepting=False),
               4: live(4, None, None, closed=True, final0=1.0, accepting=False)}
    traded = score_shadow(tmp_path, markets, "core", legs=False)
    assert traded["signals"] == 2 and traded["resolved"] == 1 and traded["win_rate"] == 1.0
    legs = score_shadow(tmp_path, markets, "core", legs=True)
    assert legs["signals"] == 1 and legs["resolved"] == 1 and legs["win_rate"] == 0.0
    assert score_shadow(tmp_path, markets, "core")["signals"] == 3
    assert score_shadow(tmp_path, markets, "above")["resolved"] == 1


def test_one_failing_order_does_not_abort_the_cycle_or_lose_state(engine, monkeypatch):
    e, pm, path, limits = engine
    real_book = pm.book
    calls = {"n": 0}

    def flaky(token):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectionError("network down")
        return real_book(token)

    monkeypatch.setattr(pm, "book", flaky)
    # give the two candidates separate events so that both orders are attempted
    pm.markets[2] = live(2, 0.06, 0.07, event=11)
    rep = e.run_cycle(NOW)
    assert rep.placed == 1 and rep.rejected == 1
    assert any("order failed" in n for n in rep.notes)
    assert (path / "state.json").exists() and rep.n_positions == 1


def test_no_purchase_unless_the_contract_was_already_in_the_band_a_day_ago(engine):
    """The tested rule buys the day after the signal. A contract that has just
    arrived in the band (here: it was at 0.80 yesterday) must wait."""
    e, pm, path, limits = engine
    pm.history = {"T1a": 0.80, "T2b": 0.80}
    rep = e.run_cycle(NOW)
    assert rep.n_candidates == 2 and rep.placed == 0 and rep.n_positions == 0
    assert not (path / "shadow.csv").exists()               # an unconfirmed signal is not logged either
    pm.history = {"T1a": 0.925, "T2b": 0.80}                # market 1 has now been in the band for a day
    rep = e.run_cycle(NOW + DAY)
    assert rep.placed == 1 and {p.market_id for p in e.portfolio.positions.values()} == {1}


def test_missing_history_means_no_trade_not_a_crash(engine):
    e, pm, path, limits = engine
    pm.price_as_of = lambda token, ts: (_ for _ in ()).throw(ConnectionError("down"))
    rep = e.run_cycle(NOW)
    assert rep.placed == 0 and rep.n_positions == 0


def test_bands_outside_the_traded_one_are_logged_but_never_bought(engine):
    import csv
    e, pm, path, limits = engine
    cfg = StrategyConfig(**{**CFG.to_dict(), "ask_lo": 0.95, "ask_hi": 0.98, "watch_lo": 0.90, "watch_hi": 0.99,
                            "min_edge": 0.0})
    e.strategy = HarvestStrategy(cfg, MODEL)
    pm.markets = {1: live(1, 0.92, 0.93, event=10),         # below the traded band: watch only
                  2: live(2, 0.955, 0.965, event=11),       # in the traded band
                  3: live(3, 0.98, 0.985, event=12)}        # above it: watch only
    rep = e.run_cycle(NOW)
    assert {p.market_id for p in e.portfolio.positions.values()} == {2}
    rows = {int(r["market_id"]): r for r in csv.DictReader((path / "shadow.csv").open())}
    assert (rows[1]["band"], rows[2]["band"], rows[3]["band"]) == ("below", "core", "above")
    assert (rows[1]["tradable"], rows[2]["tradable"], rows[3]["tradable"]) == ("0", "1", "0")


def test_single_only_skips_legs_of_multi_outcome_events_but_still_watches_them():
    from dataclasses import replace
    cfg = StrategyConfig(**{**CFG.to_dict(), "single_only": True})
    s = HarvestStrategy(cfg, MODEL)
    leg = live(1, 0.92, 0.93)
    leg = LiveMarket(replace(leg.info, neg_risk=True), leg.best_bid0, leg.best_ask0, leg.volume, leg.volume_24h,
                     leg.liquidity, leg.accepting_orders, leg.closed, leg.winner, leg.final0, leg.question)
    markets = {1: leg, 2: live(2, 0.92, 0.93)}
    assert [c.market.info.market_id for c in s.candidates(markets, NOW)] == [2]
    assert sorted(c.market.info.market_id for c in s.watchlist(markets, NOW)) == [1, 2]


def test_unconfirmed_signals_are_not_looked_up_again_every_cycle(engine):
    e, pm, path, limits = engine
    pm.markets[4] = live(4, 0.975, 0.98, event=14)     # above the traded band: only ever logged
    calls = []
    pm.history = {"T1a": 0.80, "T2b": 0.80, "T4a": 0.80}   # none was in its band a day ago
    real = pm.price_as_of

    def counting(token, ts):
        calls.append(token)
        return real(token, ts)

    pm.price_as_of = counting
    e.run_cycle(NOW)
    assert sorted(calls) == ["T1a", "T2b", "T4a"]
    calls.clear()
    e.run_cycle(NOW + 600)                              # ten minutes later
    # tradable candidates are re-checked every cycle; the log-only signal is not
    assert sorted(calls) == ["T1a", "T2b"]
    calls.clear()
    e.run_cycle(NOW + 7 * 3600)                         # after the re-check interval it is looked up again
    assert "T4a" in calls


# ------------------------------------------------------------------ quietness
def print_(days_ago, token, price, now=NOW):
    return {"timestamp": now - days_ago * DAY, "token_id": token, "price": price, "side": "BUY", "size": 10}


def quiet_engine(tmp_path, monkeypatch, markets, tape, **cfg):
    pm = FakePM(markets)
    pm.tape = tape
    import kht.trading.engine as eng
    monkeypatch.setattr(eng, "scan_open", lambda pm_, min_volume: {k: v for k, v in pm_.markets.items() if not v.closed})
    monkeypatch.setattr(eng, "fetch_markets", lambda pm_, ids: {i: pm_.markets[i] for i in ids})
    config = StrategyConfig(**{**CFG.to_dict(), "categories": ("politics",), **cfg})
    limits = RiskLimits(bankroll=1000, max_position_usd=25, max_event_usd=25, max_order_usd=25)
    return Engine(pm, StateStore(tmp_path), HarvestStrategy(config, MODEL), limits), pm


def test_quiet_filter_buys_only_what_has_not_moved(tmp_path, monkeypatch):
    markets = {1: live(1, 0.92, 0.93), 2: live(2, 0.92, 0.93), 3: live(3, 0.92, 0.93)}
    tape = {"0x1": [print_(1, "T1a", 0.93), print_(4, "T1a", 0.92), print_(10, "T1a", 0.93)],     # quiet
            "0x2": [print_(1, "T2a", 0.93), print_(3, "T2a", 0.80), print_(10, "T2a", 0.93)],     # dipped this week
            "0x3": [print_(1, "T3a", 0.93), print_(2, "T3a", 0.93)]}                               # too new to say
    e, pm = quiet_engine(tmp_path, monkeypatch, markets, tape, quiet_days=7.0, quiet_range=0.03)
    rep = e.run_cycle(NOW)
    assert rep.placed == 1 and [p.market_id for p in e.portfolio.positions.values()] == [1]
    import csv
    checks = {int(r["market_id"]): r for r in csv.DictReader((tmp_path / "quiet.csv").open())}
    assert checks[1]["quiet"] == "1" and checks[2]["quiet"] == "0" and checks[3]["quiet"] == "0"
    assert checks[3]["seasoned"] == "0" and float(checks[2]["range"]) == pytest.approx(0.13)
    decisions = [json.loads(line) for line in (tmp_path / "decisions.jsonl").open()]
    assert any(d.get("action") == "screened" and d["by_limit"].get("not quiet") == 2 for d in decisions)


def test_without_the_filter_nothing_is_looked_up_for_trading(tmp_path, monkeypatch):
    markets = {1: live(1, 0.92, 0.93)}
    e, pm = quiet_engine(tmp_path, monkeypatch, markets, {"0x1": [print_(1, "T1a", 0.50), print_(10, "T1a", 0.93)]})
    assert e.run_cycle(NOW).placed == 1                          # busy, and bought all the same
    assert not (tmp_path / "quiet.csv").exists()


def test_quiet_answers_are_remembered_between_cycles(tmp_path, monkeypatch):
    markets = {1: live(1, 0.92, 0.93), 2: live(2, 0.92, 0.93)}
    tape = {"0x1": [print_(1, "T1a", 0.93), print_(3, "T1a", 0.70), print_(10, "T1a", 0.93)],
            "0x2": [print_(1, "T2a", 0.93), print_(3, "T2a", 0.70), print_(10, "T2a", 0.93)]}
    e, pm = quiet_engine(tmp_path, monkeypatch, markets, tape, quiet_days=7.0, confirm_hours=0.0, watch_lo=0.0, watch_hi=0.0)
    e.run_cycle(NOW)
    first = pm.tape_reads
    assert first == 2
    again = Engine(pm, StateStore(tmp_path), e.strategy, e.limits)       # a new process, as on the schedule
    again.run_cycle(NOW + 3 * 3600)
    assert pm.tape_reads == first                                 # both were busy: not asked again so soon
    again.run_cycle(NOW + 13 * 3600)
    assert pm.tape_reads == first + 2


def test_every_forward_test_signal_gets_its_traded_range_recorded_once(tmp_path, monkeypatch):
    import csv
    from kht.trading.report import score_shadow, shadow_quiet
    markets = {1: live(1, 0.92, 0.93), 2: live(2, 0.92, 0.93)}
    tape = {"0x1": [print_(1, "T1a", 0.93), print_(4, "T1a", 0.92), print_(10, "T1a", 0.93)],
            "0x2": [print_(1, "T2a", 0.93), print_(3, "T2a", 0.80), print_(10, "T2a", 0.93)]}
    e, pm = quiet_engine(tmp_path, monkeypatch, markets, tape)    # no filter: this account trades everything
    e.run_cycle(NOW)
    e.run_cycle(NOW + 600)
    rows = list(csv.DictReader((tmp_path / "shadow_quiet.csv").open()))
    assert sorted(int(r["market_id"]) for r in rows) == [1, 2]    # once each
    assert shadow_quiet(tmp_path) == {"1:core": True, "2:core": False}
    resolved = {1: live(1, None, None, closed=True, final0=1.0, accepting=False),
                2: live(2, None, None, closed=True, final0=0.0, accepting=False)}
    assert score_shadow(tmp_path, resolved, "core", quiet=True)["win_rate"] == 1.0
    assert score_shadow(tmp_path, resolved, "core", quiet=False)["win_rate"] == 0.0
    assert score_shadow(tmp_path, resolved, "core")["signals"] == 2


def test_signals_logged_before_ranges_were_recorded_are_caught_up_as_of_their_own_time(tmp_path, monkeypatch):
    import csv
    markets = {1: live(1, 0.92, 0.93)}
    # quiet up to the signal, then a collapse afterwards that must not count
    tape = {"0x1": [print_(-0.5, "T1a", 0.40), print_(1, "T1a", 0.93), print_(4, "T1a", 0.92), print_(10, "T1a", 0.93)]}
    e, pm = quiet_engine(tmp_path, monkeypatch, markets, tape)
    e.run_cycle(NOW)
    (tmp_path / "shadow_quiet.csv").unlink()                      # as if the signal had been logged by older code
    old = Engine(pm, StateStore(tmp_path), e.strategy, e.limits)
    old.shadow_quiet_done.clear()
    old.run_cycle(NOW + DAY)                                      # a day later, after the collapse
    rows = list(csv.DictReader((tmp_path / "shadow_quiet.csv").open()))
    assert len(rows) == 1 and float(rows[0]["range"]) == pytest.approx(0.01) and rows[0]["ts"] == str(int(NOW))


def test_lookups_are_rationed_within_a_cycle(tmp_path, monkeypatch):
    import kht.trading.engine as eng
    monkeypatch.setattr(eng, "QUIET_LOOKUPS_PER_CYCLE", 3)
    markets = {i: live(i, 0.92, 0.93) for i in range(1, 9)}
    tape = {f"0x{i}": [print_(1, f"T{i}a", 0.93), print_(10, f"T{i}a", 0.93)] for i in range(1, 9)}
    e, pm = quiet_engine(tmp_path, monkeypatch, markets, tape, quiet_days=7.0, confirm_hours=0.0)
    e.run_cycle(NOW)
    assert pm.tape_reads == 3
