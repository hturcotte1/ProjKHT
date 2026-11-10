"""Fill rules, accounting and risk limits: the parts where a bug costs money."""

import pytest

from kht.trading.fees import taker_fee, taker_fee_per_share
from kht.trading.fills import in_token_frame, maker_fill, round_to_tick, taker_fill
from kht.trading.models import (Fill, Intent, MarketInfo, Order, OrderKind, OrderStatus, Side,
                                TradePrint)
from kht.trading.portfolio import Portfolio
from kht.trading.risk import RiskLimits, RiskManager

M = MarketInfo(market_id=1, condition_id="0xc", question="A vs B", token0="T0", token1="T1",
               outcome0="A", outcome1="B", event_id=7, category="sports", fee_rate=0.05, tick=0.01)


def buy(price=0.40, size=100, queue=0.0, kind=OrderKind.MAKER, token="T0", ts=0.0):
    return Order("o1", 1, token, Side.BUY, kind, price, size, created_ts=ts, queue_ahead=queue)


# ------------------------------------------------------------------ fees
def test_fee_matches_published_tables():
    # docs.polymarket.com/trading/fees: 100 shares
    assert taker_fee(100, 0.50, 0.05) == pytest.approx(1.25)    # sports at 50c
    assert taker_fee(100, 0.30, 0.07) == pytest.approx(1.47)    # crypto at 30c
    assert taker_fee(100, 0.90, 0.04) == pytest.approx(0.36)    # politics at 90c
    assert taker_fee(100, 0.50, 0.0) == 0.0                      # geopolitics is free
    assert taker_fee_per_share(0.3, 0.05) == pytest.approx(taker_fee_per_share(0.7, 0.05))  # symmetric


# ----------------------------------------------------------------- fills
def test_maker_buy_not_filled_by_trade_above_its_price():
    o = buy(0.40)
    assert maker_fill(o, TradePrint(1, "T0", Side.SELL, 0.41, 500), M) is None
    assert o.filled == 0


def test_maker_buy_not_filled_by_taker_buys():
    o = buy(0.40)
    assert maker_fill(o, TradePrint(1, "T0", Side.BUY, 0.40, 500), M) is None


def test_trade_through_fills_in_full():
    o = buy(0.40, size=100, queue=10_000)          # queue is irrelevant once swept
    f = maker_fill(o, TradePrint(1, "T0", Side.SELL, 0.39, 5), M)
    assert f.size == 100 and f.price == 0.40 and f.fee == 0.0 and f.maker
    assert o.status == OrderStatus.FILLED


def test_trade_at_price_respects_queue_ahead():
    o = buy(0.40, size=100, queue=250)
    assert maker_fill(o, TradePrint(1, "T0", Side.SELL, 0.40, 200), M) is None   # all to the queue
    assert o.queue_ahead == 50
    f = maker_fill(o, TradePrint(2, "T0", Side.SELL, 0.40, 80), M)                # 50 queue, 30 to us
    assert f.size == pytest.approx(30)
    assert o.status == OrderStatus.OPEN and o.remaining == pytest.approx(70)


def test_mirrored_print_fills_resting_order():
    # buying the other token at 0.61 is selling ours at 0.39: through our 0.40 bid
    o = buy(0.40)
    assert in_token_frame(TradePrint(1, "T1", Side.BUY, 0.61, 10), "T0", M) == (Side.SELL, pytest.approx(0.39))
    f = maker_fill(o, TradePrint(1, "T1", Side.BUY, 0.61, 10), M)
    assert f is not None and f.size == 100


def test_prints_before_placement_or_after_expiry_do_not_fill():
    o = buy(0.40, ts=100.0)
    assert maker_fill(o, TradePrint(99.0, "T0", Side.SELL, 0.30, 500), M) is None
    o.expires_ts = 200.0
    assert maker_fill(o, TradePrint(200.0, "T0", Side.SELL, 0.30, 500), M) is None
    assert maker_fill(o, TradePrint(150.0, "T0", Side.SELL, 0.30, 500), M) is not None


def test_resting_sell_is_symmetric():
    o = Order("s", 1, "T0", Side.SELL, OrderKind.MAKER, 0.60, 50, created_ts=0)
    assert maker_fill(o, TradePrint(1, "T0", Side.BUY, 0.59, 500), M) is None
    f = maker_fill(o, TradePrint(1, "T0", Side.BUY, 0.62, 5), M)
    assert f.size == 50 and f.price == 0.60


def test_taker_walks_book_pays_fee_and_stops_at_limit():
    o = buy(0.42, size=100, kind=OrderKind.TAKER)
    fills = taker_fill(o, [(0.41, 30), (0.42, 40), (0.43, 1000)], M, ts=5)
    assert [f.price for f in fills] == [0.41, 0.42]
    assert sum(f.size for f in fills) == 70
    assert fills[0].fee == pytest.approx(taker_fee(30, 0.41, 0.05))
    assert o.status == OrderStatus.CANCELLED          # unfilled remainder is killed, not rested


def test_round_to_tick_never_more_aggressive():
    assert round_to_tick(0.4567, 0.01, Side.BUY) == 0.45
    assert round_to_tick(0.4567, 0.01, Side.SELL) == 0.46
    assert round_to_tick(0.45, 0.01, Side.BUY) == 0.45
    assert round_to_tick(0.45, 0.01, Side.SELL) == 0.45
    assert round_to_tick(0.0004, 0.001, Side.BUY) == 0.001     # clamped inside (0, 1)


# ------------------------------------------------------------- portfolio
def test_buy_sell_round_trip_accounting():
    pf = Portfolio(cash=100.0)
    pf.apply(Fill("a", 1, "T0", Side.BUY, 0.40, 50, 0.6, 0, maker=False))
    assert pf.cash == pytest.approx(100 - 20 - 0.6)
    assert pf.positions["T0"].avg_price == pytest.approx(20.6 / 50)
    pf.apply(Fill("b", 1, "T0", Side.SELL, 0.50, 50, 0.0, 1, maker=True))
    assert "T0" not in pf.positions
    assert pf.cash == pytest.approx(100 - 20.6 + 25)
    assert pf.realized == pytest.approx(25 - 20.6)


def test_settlement_pays_one_or_zero():
    pf = Portfolio(cash=0.0)
    pf.apply(Fill("a", 1, "T0", Side.BUY, 0.40, 10, 0.0, 0, maker=True))
    assert pf.settle("T0", 1.0) == pytest.approx(6.0)
    assert pf.cash == pytest.approx(6.0)
    pf.apply(Fill("b", 2, "X", Side.BUY, 0.40, 10, 0.0, 0, maker=True))
    assert pf.settle("X", 0.0) == pytest.approx(-4.0)


def test_cannot_sell_more_than_held():
    pf = Portfolio(cash=10.0)
    with pytest.raises(ValueError):
        pf.apply(Fill("a", 1, "T0", Side.SELL, 0.5, 1, 0.0, 0, maker=False))


def test_equity_marks_positions():
    pf = Portfolio(cash=50.0)
    pf.apply(Fill("a", 1, "T0", Side.BUY, 0.40, 100, 0.0, 0, maker=True))
    assert pf.equity({"T0": 0.45}) == pytest.approx(10 + 45)
    assert pf.equity({}) == pytest.approx(10 + 40)          # no mark -> carried at cost


def test_portfolio_round_trips_through_dict():
    pf = Portfolio(cash=50.0)
    pf.apply(Fill("a", 1, "T0", Side.BUY, 0.40, 100, 0.5, 0, maker=False))
    again = Portfolio.from_dict(pf.to_dict())
    assert again.cash == pf.cash and again.positions["T0"].shares == 100


# ------------------------------------------------------------------ risk
def intent(price=0.40, size=50, side=Side.BUY, kind=OrderKind.MAKER, **meta):
    return Intent("place", 1, "T0", side, kind, price, size, meta=meta)


def rm(**kw):
    return RiskManager(RiskLimits(bankroll=1000, max_position_usd=25, max_event_usd=40,
                                  max_order_usd=25, **kw))


def test_per_market_cap_counts_positions_and_resting_orders():
    r, pf = rm(), Portfolio(cash=1000)
    assert r.check(intent(0.40, 50), M, pf, [])[0]                       # $20 ok
    resting = [buy(0.40, 50)]                                            # $20 already resting
    ok, why = r.check(intent(0.40, 50), M, pf, resting)
    assert not ok and "market exposure" in why


def test_event_cap_spans_markets():
    r, pf = rm(), Portfolio(cash=1000)
    pf.apply(Fill("a", 2, "Z", Side.BUY, 0.50, 50, 0.0, 0, maker=True))  # $25 in sibling market 2
    ok, why = r.check(intent(0.40, 50), M, pf, [], market_event={1: 7, 2: 7})
    assert not ok and "event exposure" in why


def test_price_bounds_and_minimum_size():
    r, pf = rm(), Portfolio(cash=1000)
    assert not r.check(intent(0.01, 50), M, pf, [])[0]
    assert not r.check(intent(0.40, 1), M, pf, [])[0]


def test_cannot_spend_cash_reserved_by_resting_orders():
    r = RiskManager(RiskLimits(bankroll=1000, max_position_usd=1e9, max_event_usd=1e9,
                               max_order_usd=1e9, max_total_exposure_frac=1.0))
    pf = Portfolio(cash=30.0)
    other = Order("x", 99, "Q", Side.BUY, OrderKind.MAKER, 0.50, 40, created_ts=0)   # reserves $20
    ok, why = r.check(intent(0.40, 50), M, pf, [other])                              # needs $20, $10 free
    assert not ok and "cash" in why


def test_kill_switch_trips_and_blocks_buys_but_not_sells():
    r, pf = rm(daily_loss_limit_usd=50), Portfolio(cash=1000)
    r.update(1000.0, now_ts=86_400 * 10)
    r.update(949.0, now_ts=86_400 * 10 + 60)
    assert r.state.halted and "daily loss" in r.state.halt_reason
    assert not r.check(intent(), M, pf, [])[0]
    pf.apply(Fill("a", 1, "T0", Side.BUY, 0.40, 50, 0.0, 0, maker=True))
    assert r.check(intent(0.40, 50, side=Side.SELL), M, pf, [])[0]       # reducing risk stays allowed
    r.update(1000.0, now_ts=86_400 * 11)                                 # a new day does not un-halt
    assert r.state.halted


def test_drawdown_limit_uses_high_water_mark():
    r = rm(daily_loss_limit_usd=1e9, max_drawdown_usd=100)
    r.update(1000, 0); r.update(1200, 86_400); r.update(1101, 2 * 86_400)
    assert not r.state.halted
    r.update(1099, 3 * 86_400)
    assert r.state.halted


def test_taker_must_clear_its_fee():
    r, pf = rm(), Portfolio(cash=1000)
    ok, why = r.check(intent(0.50, 40, kind=OrderKind.TAKER, edge=0.01), M, pf, [])   # fee is 1.25c
    assert not ok and "fee" in why
    assert r.check(intent(0.50, 40, kind=OrderKind.TAKER, edge=0.03), M, pf, [])[0]


def test_sell_limited_to_free_holding():
    r, pf = rm(), Portfolio(cash=1000)
    pf.apply(Fill("a", 1, "T0", Side.BUY, 0.40, 50, 0.0, 0, maker=True))
    resting_sell = Order("s", 1, "T0", Side.SELL, OrderKind.MAKER, 0.6, 30, created_ts=0)
    assert r.check(intent(0.6, 20, side=Side.SELL), M, pf, [resting_sell])[0]
    assert not r.check(intent(0.6, 21, side=Side.SELL), M, pf, [resting_sell])[0]


def test_theme_cap_spans_events():
    """Three different events about one story must not all be filled."""
    r = RiskManager(RiskLimits(bankroll=1000, max_position_usd=25, max_event_usd=25, max_theme_usd=40, max_order_usd=25))
    pf = Portfolio(cash=1000)
    pf.apply(Fill("a", 2, "Z", Side.BUY, 0.50, 50, 0.0, 0, maker=True))      # $25 in market 2, a different event
    themes = {1: frozenset({"hormuz"}), 2: frozenset({"hormuz", "iran"}), 3: frozenset({"fed"})}
    ok, why = r.check(intent(0.40, 50), M, pf, [], market_event={1: 7, 2: 8}, market_themes=themes)
    assert not ok and "theme 'hormuz'" in why
    other = MarketInfo(market_id=3, condition_id="0xd", question="Fed?", token0="F0", token1="F1",
                       outcome0="Yes", outcome1="No", event_id=9)
    assert r.check(Intent("place", 3, "F0", Side.BUY, OrderKind.MAKER, 0.40, 50), other, pf, [],
                   market_event={2: 8, 3: 9}, market_themes=themes)[0]
