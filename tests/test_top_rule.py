"""The rule of test G1 (src/kht/trading/top_rule.py, docs/13 section 4)."""

from __future__ import annotations

import pytest

from kht.trading import top_rule as rule

BIDS = [(0.52, 300.0), (0.51, 5000.0), (0.40, 9000.0)]
ASKS = [(0.54, 6000.0), (0.55, 100.0)]


def test_a_book_qualifies_when_both_sides_hold_the_target_within_twice_the_spread():
    assert rule.reaches(BIDS, 5000) == 0.51 and rule.reaches(ASKS, 5000) == 0.54 and rule.reaches(ASKS, 7000) is None
    assert rule.qualifies(BIDS, ASKS, 5000, 0.03)                      # 0.51 to 0.54: three cents, six are allowed
    assert not rule.qualifies(BIDS, ASKS, 5400, 0.03)                  # the bid side now needs the level at 0.40
    assert rule.qualifies(BIDS, ASKS, 5400, None)                      # no maximum spread: each side by itself
    assert not rule.qualifies(BIDS, ASKS, 20000, None) and not rule.qualifies([], ASKS, 10, None)


def test_share_follows_the_filed_formula():
    # joining the best bid: 100 of 400 at the best price, 5,000 one tick behind at 30%
    assert rule.share(BIDS, 0.52, 100, 5000, 0.3, True) == pytest.approx(100 / (400 + 0.3 * 5000))
    # the whole level where the target is reached counts, and nothing behind it
    assert rule.share(ASKS, 0.54, 100, 5000, 0.3, False) == pytest.approx(100 / 6100)
    # a tenth of a contract alone at the top, with the size eleven ticks behind, holds nearly all of the score
    dusty = [(0.62, 0.1), (0.51, 5000.0)]
    assert rule.share(dusty, 0.62, 100, 5000, 0.3, True) > 0.99
    assert rule.share(dusty, 0.62, 0.0, 5000, 0.3, True) == 0.0
    # a side that never reaches the target has no score
    assert rule.share([(0.5, 10.0)], 0.5, 100, 5000, 0.3, True) == 0.0


def test_with_order_puts_a_new_price_in_its_place():
    assert rule.with_order(BIDS, 0.515, 50, True) == [(0.52, 300.0), (0.515, 50), (0.51, 5000.0), (0.40, 9000.0)]
    assert rule.with_order(ASKS, 0.53, 50, False)[0] == (0.53, 50)
    assert rule.with_order(ASKS, 0.60, 50, False)[-1] == (0.60, 50)
    assert rule.with_order(BIDS, None, 50, True) == BIDS


def test_quotes_join_the_best_prices_and_respect_what_is_held():
    q = rule.quotes(BIDS, ASKS, 0.0, 100, 5000, 0.03)
    assert (q["bid_px"], q["bid_qty"], q["ask_px"], q["ask_qty"]) == (0.52, 100, 0.54, 100)
    long = rule.quotes(BIDS, ASKS, 100.0, 100, 5000, 0.03)             # holding the full size: no bid, and the offer can sell it and go short
    assert long["bid_px"] is None and long["ask_qty"] == 100
    partly = rule.quotes(BIDS, ASKS, -40.0, 100, 5000, 0.03)
    assert partly["bid_qty"] == 100 and partly["ask_qty"] == 60
    assert rule.quotes(BIDS, ASKS, 0.0, 100, 5400, 0.03)["why"] == "the book does not qualify"
    wide = [(0.59, 6000.0)]
    assert rule.quotes(BIDS, wide, 0.0, 100, 5000, None)["why"] == "best prices too far apart"
    assert rule.quotes(BIDS, ASKS, 0.0, 100, 5000, 0.03, state="EXPIRED")["why"] == "no market"


def test_shares_are_nothing_when_nothing_rests():
    none = rule.quotes(BIDS, ASKS, 0.0, 100, 5400, 0.03)
    assert rule.shares(BIDS, ASKS, none, 5400, 0.3, 0.03) == (0.0, 0.0)
    q = rule.quotes(BIDS, ASKS, 0.0, 100, 5000, 0.03)
    sb, sa = rule.shares(BIDS, ASKS, q, 5000, 0.3, 0.03)
    assert sb == pytest.approx(100 / 1900) and sa == pytest.approx(100 / 6100)


def reading(ts, traded, notional, last=None, last_t=None, low=None, low_t=None, high=None, high_t=None):
    return {"ts": ts, "traded": traded, "notional": notional, "last": last, "last_t": last_t, "low": low, "low_t": low_t, "high": high, "high_t": high_t}


def test_fills_come_from_the_running_totals():
    q = {"bid_px": 0.52, "bid_qty": 100.0, "ask_px": 0.54, "ask_qty": 100.0}
    before = reading(1000.0, 500.0, 250.0)
    # 40 contracts traded at 52c on average: the bid is hit for 40, the offer is not
    assert rule.fills(q, before, reading(1030.0, 540.0, 250.0 + 40 * 0.52), BIDS, ASKS) == (40.0, 0.0)
    # 300 traded at 54c: the offer is lifted for its whole size
    assert rule.fills(q, before, reading(1030.0, 800.0, 250.0 + 300 * 0.54), BIDS, ASKS) == (0.0, 100.0)
    # trading between our prices touches neither
    assert rule.fills(q, before, reading(1030.0, 520.0, 250.0 + 20 * 0.53), BIDS, ASKS) == (0.0, 0.0)
    # nothing traded
    assert rule.fills(q, before, reading(1030.0, 500.0, 250.0), BIDS, ASKS) == (0.0, 0.0)
    # a new low at our bid, set after the earlier reading, with an average above it: both the low and the average are evidence
    assert rule.fills(q, before, reading(1030.0, 560.0, 250.0 + 60 * 0.535, low=0.52, low_t=1010.0), BIDS, ASKS) == (60.0, 0.0)
    # the same low set before the earlier reading is not news
    assert rule.fills(q, before, reading(1030.0, 560.0, 250.0 + 60 * 0.535, low=0.52, low_t=990.0), BIDS, ASKS) == (0.0, 0.0)


def test_fills_when_the_other_side_moves_through_our_price():
    q = {"bid_px": 0.52, "bid_qty": 100.0, "ask_px": 0.54, "ask_qty": 100.0}
    before = reading(1000.0, 500.0, 250.0)
    asks_now = [(0.51, 30.0), (0.53, 500.0)]                           # somebody now offers at 51c: they would have sold to our bid
    assert rule.fills(q, before, reading(1030.0, 500.0, 250.0), BIDS, asks_now) == (30.0, 0.0)
    bids_now = [(0.55, 1000.0)]
    assert rule.fills(q, before, reading(1030.0, 500.0, 250.0), bids_now, ASKS) == (0.0, 100.0)
    one_sided = {"bid_px": None, "bid_qty": 0.0, "ask_px": 0.54, "ask_qty": 100.0}
    assert rule.fills(one_sided, before, reading(1030.0, 540.0, 250.0 + 40 * 0.52), BIDS, ASKS) == (0.0, 0.0)


def test_last_tick_stands_where_one_order_is_all_that_is_missing():
    asks = [(0.03, 6900.0), (0.11, 20.0)]
    q = rule.last_tick([], asks, 0.0, 0.0, 5000, 0.03)                   # gold on 18 November: nobody bidding, 6,900 offered at 3c
    assert (q["bid_px"], q["bid_qty"], q["ask_px"]) == (0.01, 5000, None) and q["why"] == "resting"
    sb, sa = rule.shares([], asks, q, 5000, 0.3, 0.03)
    assert sb == pytest.approx(1.0) and sa == 0.0                         # the whole of the bid side, none of the offer side
    # a tenth of a contract at 2c does not change it much: ours is one tick behind and still nearly all of the side
    sb, _ = rule.shares([(0.02, 0.1)], asks, rule.last_tick([(0.02, 0.1)], asks, 0.0, 0.0, 5000, 0.03), 5000, 0.3, 0.03)
    assert sb == pytest.approx(0.3 * 5000 / (0.1 + 0.3 * 5000))
    # the mirror image: nobody offering, the bids at 97c
    q = rule.last_tick([(0.97, 8000.0)], [], 0.0, 0.0, 5000, 0.03)
    assert (q["ask_px"], q["ask_qty"], q["bid_px"]) == (0.99, 5000, None)


def test_last_tick_rests_nothing_when_it_would_not_help_or_is_not_needed():
    asks = [(0.03, 6900.0)]
    assert rule.last_tick([(0.02, 6000.0)], asks, 0.0, 0.0, 5000, 0.03)["why"] == "the book qualifies without us"
    assert rule.last_tick([], [(0.03, 2700.0), (0.71, 400.0)], 0.0, 0.0, 3000, 0.03)["bid_px"] is None      # silver that day: the offers do not hold the target either
    assert rule.last_tick([], [(0.09, 6900.0)], 0.0, 0.0, 5000, 0.03)["bid_px"] is None                     # the offers are eight cents from the last tick: six are allowed
    assert rule.last_tick([], [(0.09, 6900.0)], 0.0, 0.0, 5000, 0.05)["bid_px"] == 0.01                     # ten are allowed here
    assert rule.last_tick([], asks, 5000.0, 0.0, 5000, 0.03)["bid_px"] is None                              # the account has bought the target size already
    assert rule.last_tick([], asks, 4999.0, 0.0, 5000, 0.03)["bid_qty"] == 5000                             # until then the order is always the whole target
    assert rule.last_tick([], asks, 0.0, 0.0, 5000, 0.03, state="EXPIRED")["why"] == "no market"
    assert rule.last_tick([], [(0.01, 9000.0)], 0.0, 0.0, 5000, 0.03)["bid_px"] is None                     # an offer at the last tick itself: a bid there would cross it
    assert rule.last_tick([], [], 0.0, 0.0, 5000, 0.03)["why"] == "an order at the last tick would not make it qualify"


def test_last_tick_order_is_filled_only_at_the_last_tick():
    q = rule.last_tick([], [(0.03, 6900.0)], 0.0, 0.0, 5000, 0.03)
    before = reading(1000.0, 4000.0, 300.0)
    assert rule.fills(q, before, reading(1030.0, 4400.0, 300.0 + 400 * 0.03), [], [(0.03, 6500.0)]) == (0.0, 0.0)    # people buying at 3c: not us
    assert rule.fills(q, before, reading(1030.0, 4400.0, 300.0 + 400 * 0.01), [], [(0.03, 6900.0)]) == (400.0, 0.0)  # somebody sold 400 at a cent
