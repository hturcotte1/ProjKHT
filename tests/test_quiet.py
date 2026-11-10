"""The traded-range measure used to tell a quiet outcome from a busy one."""

from kht.trading import quiet
from kht.trading.models import MarketInfo
from kht.trading.quiet import Quietness, traded_range

M = MarketInfo(market_id=1, condition_id="0xc", question="Will it happen by June 30?", token0="YES", token1="NO",
               outcome0="Yes", outcome1="No")
DAY = 86_400
NOW = 100 * DAY


class Feed:
    """Stands in for kht.api.Polymarket: a tape, newest first, cut off at the page limit."""

    def __init__(self, trades):
        self.tape = sorted(trades, key=lambda t: -t["timestamp"])

    def iter_trades(self, condition, page_size=1000, max_pages=None):
        assert condition == "0xc"
        cut = None if max_pages is None else page_size * max_pages
        return iter(self.tape[:cut])


def trade(days_ago, token, price):
    return {"timestamp": NOW - days_ago * DAY, "token_id": token, "price": price, "side": "BUY", "size": 10}


def test_range_counts_both_outcomes_in_the_asked_outcomes_terms():
    # "No" bought at 94c and 95c; "Yes" bought at 7c is the same trade as "No" sold at 93c
    feed = Feed([trade(1, "NO", 0.94), trade(2, "NO", 0.95), trade(3, "YES", 0.07), trade(9, "NO", 0.90)])
    q = traded_range(feed, M, outcome=1, as_of=NOW, days=7)
    assert q.prints == 3 and abs(q.range - 0.02) < 1e-9 and q.seasoned and q.complete
    assert q.is_quiet(0.03) and not q.is_quiet(0.015)
    # the same tape seen from the "Yes" side has the same width
    assert abs(traded_range(feed, M, outcome=0, as_of=NOW, days=7).range - 0.02) < 1e-9


def test_a_move_inside_the_window_is_not_quiet_but_one_before_it_is_forgotten():
    moved = Feed([trade(1, "NO", 0.94), trade(5, "NO", 0.80), trade(9, "NO", 0.94)])
    assert not traded_range(moved, M, 1, NOW, 7).is_quiet(0.03)
    earlier = Feed([trade(1, "NO", 0.94), trade(6, "NO", 0.95), trade(9, "NO", 0.60)])
    assert traded_range(earlier, M, 1, NOW, 7).is_quiet(0.03)


def test_a_market_younger_than_the_window_is_not_quiet():
    q = traded_range(Feed([trade(1, "NO", 0.94), trade(3, "NO", 0.94)]), M, 1, NOW, 7)
    assert q.prints == 2 and q.range == 0 and not q.seasoned and q.complete
    assert not q.is_quiet(0.03)


def test_nothing_traded_in_the_window_is_not_called_quiet():
    q = traded_range(Feed([trade(20, "NO", 0.94)]), M, 1, NOW, 7)
    assert q.prints == 0 and q.range is None and q.seasoned
    assert not q.is_quiet(0.03)          # the backtest only ever saw days with trades


def test_trades_after_the_moment_asked_about_are_ignored():
    feed = Feed([trade(0.5, "NO", 0.50), trade(3, "NO", 0.94), trade(4, "NO", 0.95), trade(12, "NO", 0.93)])
    as_of = NOW - 2 * DAY                                   # a signal logged two days ago
    q = traded_range(feed, M, 1, as_of, 7)
    assert q.prints == 2 and abs(q.range - 0.01) < 1e-9 and q.is_quiet(0.03)


def test_a_feed_cut_off_before_the_window_starts_is_reported_not_guessed(monkeypatch):
    monkeypatch.setattr(quiet, "PAGE", 5)
    feed = Feed([trade(d / 10, "NO", 0.94) for d in range(1, 40)] + [trade(9, "NO", 0.94)])
    q = traded_range(feed, M, 1, NOW, 7, max_pages=2)       # ten prints read, the window not exhausted
    assert q.prints == 10 and not q.complete and not q.is_quiet(0.03)
    q = traded_range(feed, M, 1, NOW, 7, max_pages=20)
    assert q.complete and q.seasoned and q.is_quiet(0.03)


def test_to_dict_is_plain_numbers():
    assert Quietness(0.0123456, 4, True, True).to_dict() == {"range": 0.0123, "prints": 4, "seasoned": 1, "complete": 1}
    assert Quietness(None, 0, False, True).to_dict()["range"] is None
