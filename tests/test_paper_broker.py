"""Paper broker behaviour against a scripted exchange."""

import pytest

from kht.trading import broker
from kht.trading.broker import PaperBroker
from kht.trading.models import Intent, MarketInfo, OrderKind, OrderStatus, Side
from kht.trading.portfolio import Portfolio

M = MarketInfo(market_id=1, condition_id="0xc", question="A vs B", token0="T0", token1="T1",
               outcome0="A", outcome1="B", fee_rate=0.05, tick=0.01)


class FakeExchange:
    """Stands in for kht.api.Polymarket: a fixed book and a growing tape."""

    def __init__(self):
        self.books = {"T0": {"bids": [{"price": "0.40", "size": "300"}, {"price": "0.39", "size": "500"}],
                             "asks": [{"price": "0.42", "size": "200"}, {"price": "0.43", "size": "900"}]}}
        self.tape = []      # newest first, like the API

    def book(self, token):
        return self.books[token]

    def iter_trades(self, condition, page_size=1000, max_pages=None):
        assert condition == "0xc"
        cut = None if max_pages is None else page_size * max_pages      # the feed stops at the page limit
        return iter(self.tape[:cut])

    def trade(self, ts, token_index, side, price, size):
        self.tape.insert(0, {"timestamp": ts, "outcome_index": token_index, "side": side, "price": price,
                             "size": size, "token_id": "T0" if token_index == 0 else "T1"})


def make():
    ex = FakeExchange()
    return ex, PaperBroker(ex, Portfolio(cash=1000.0))


def test_post_only_order_that_would_cross_is_rejected():
    ex, br = make()
    o, fills = br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.42, 50), M, now=100)
    assert o.status == OrderStatus.REJECTED and not fills and not br.open_orders()


def test_resting_order_joins_back_of_queue_and_fills_from_tape():
    ex, br = make()
    o, _ = br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.40, 100), M, now=100)
    assert o.queue_ahead == 300                       # the 300 already bid at 0.40 are ahead of us
    ex.trade(150, 0, "SELL", 0.40, 250)               # eaten by the queue
    assert br.sync({1: M}, now=200) == []
    ex.trade(250, 0, "SELL", 0.40, 120)               # 50 left in queue, 70 reach us
    fills = br.sync({1: M}, now=300)
    assert len(fills) == 1 and fills[0].size == pytest.approx(70) and fills[0].fee == 0
    assert br.portfolio.shares("T0") == pytest.approx(70)
    assert br.portfolio.cash == pytest.approx(1000 - 28)


def test_sync_does_not_replay_old_prints():
    ex, br = make()
    br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.41, 100), M, now=100)
    ex.trade(150, 0, "SELL", 0.40, 10)                # through our 0.41 -> full fill
    assert sum(f.size for f in br.sync({1: M}, now=200)) == 100
    assert br.sync({1: M}, now=300) == []             # same tape, nothing new


def test_print_older_than_order_never_fills_it():
    ex, br = make()
    ex.trade(50, 0, "SELL", 0.30, 1000)
    br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.40, 100), M, now=100)
    assert br.sync({1: M}, now=200) == []


def test_a_long_gap_between_syncs_is_read_back_in_full():
    """The price dips through the bid and recovers, and the next sync comes
    6,000 prints later. The dip is the oldest thing in the gap, so a short
    read of the tape would miss the fill, and a missed dip flatters the account."""
    ex, br = make()
    br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.40, 100), M, now=100)
    ex.trade(150, 0, "SELL", 0.39, 10)                # through our 0.40: the level was swept
    for i in range(6000):
        ex.trade(200 + i, 0, "BUY", 0.42, 1)          # then a long recovery
    fills = br.sync({1: M}, now=10_000)
    assert sum(f.size for f in fills) == 100 and br.tape_gaps == []


def test_a_tape_too_long_to_read_back_is_reported(monkeypatch):
    monkeypatch.setattr(broker, "TAPE_PAGE", 10)
    monkeypatch.setattr(broker, "TAPE_MAX_PAGES", 3)
    ex, br = make()
    br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.40, 100), M, now=100)
    ex.trade(150, 0, "SELL", 0.39, 10)                # would have filled us, but lies beyond the limit
    for i in range(30):
        ex.trade(200 + i, 0, "BUY", 0.42, 1)
    assert br.sync({1: M}, now=1000) == []
    assert [g["market_id"] for g in br.tape_gaps] == [1] and br.tape_gaps[0]["prints_read"] == 30
    assert br.sync({1: M}, now=1100) == [] and br.tape_gaps == []     # nothing new since: reported once


def test_tape_is_not_read_back_past_the_oldest_resting_order(monkeypatch):
    monkeypatch.setattr(broker, "TAPE_PAGE", 10)
    monkeypatch.setattr(broker, "TAPE_MAX_PAGES", 3)
    ex, br = make()
    br.last_print_ts[1] = 50.0                        # left behind by an order long gone
    for i in range(100):
        ex.trade(60 + i, 0, "BUY", 0.42, 1)           # a busy stretch in which nothing was resting
    br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.40, 100), M, now=1000)
    ex.trade(1050, 0, "SELL", 0.39, 10)
    fills = br.sync({1: M}, now=2000)
    assert sum(f.size for f in fills) == 100 and br.tape_gaps == []


def test_only_markets_with_a_resting_order_keep_a_tape_position():
    ex, br = make()
    br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.41, 100), M, now=100)
    assert br.to_dict()["last_print_ts"] == {"1": 100}
    ex.trade(150, 0, "SELL", 0.40, 10)
    br.sync({1: M}, now=200)                          # filled in full: nothing rests there any more
    assert br.to_dict()["last_print_ts"] == {}


def test_taker_buy_pays_ask_and_fee_and_kills_remainder():
    ex, br = make()
    o, fills = br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.TAKER, 0.42, 300), M, now=100)
    assert sum(f.size for f in fills) == 200 and fills[0].price == 0.42
    assert o.status == OrderStatus.CANCELLED          # 100 unfilled, not left resting
    assert br.portfolio.fees_paid == pytest.approx(200 * 0.05 * 0.42 * 0.58)


def test_expired_orders_are_cancelled():
    ex, br = make()
    o, _ = br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.40, 100, expires_ts=500), M, now=100)
    br.sync({1: M}, now=600)
    assert o.status == OrderStatus.CANCELLED


def test_state_survives_serialisation():
    ex, br = make()
    br.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.40, 100), M, now=100)
    again = PaperBroker.from_dict(ex, br.portfolio, br.to_dict())
    assert len(again.open_orders()) == 1 and again.open_orders()[0].queue_ahead == 300
    o2, _ = again.place(Intent("place", 1, "T0", Side.BUY, OrderKind.MAKER, 0.39, 10), M, now=101)
    assert o2.order_id not in br.orders               # ids keep increasing after a restart
