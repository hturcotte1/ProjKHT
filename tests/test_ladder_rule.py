"""The rule of test L2: selling every bracket of a ladder at once (src/kht/trading/ladder_rule.py, docs/11 section 12)."""

from __future__ import annotations

import pytest

from kht.trading import ladder_rule as rule


def test_the_fee_is_rounded_to_the_cent_with_halves_to_the_even_cent():
    assert rule.fee(169.49, 0.01) == 0.16                     # 0.1594
    assert rule.fee(5, 0.01) == 0.0                           # 0.0047: a fill this small pays nothing
    assert rule.fee(100, 0.5) == 2.38                         # 2.375 goes up to the even cent
    assert rule.fee(300, 0.5) == 7.12                         # 7.125 goes down to it
    assert rule.fee(0, 0.3) == 0.0 and rule.fee(10, 0.0) == 0.0 and rule.fee(10, 1.0) == 0.0


def test_bids_are_read_off_a_recorded_row_best_first():
    row = {"bid1": "0.02", "bid_qty1": "0.5", "bid2": "0.01", "bid_qty2": "999.999", "bid3": "", "bid_qty3": "", "ask1": "0.03", "ask_qty1": "5380"}
    assert rule.bids(row) == [(0.02, 0.5), (0.01, 999.99)]                      # sizes in whole hundredths, never rounded up
    assert rule.bids({"bid1": 0.01, "bid_qty1": 1000.0, "bid2": 0.11, "bid_qty2": 3.0}) == [(0.11, 3.0), (0.01, 1000.0)]
    assert rule.bids({"bid1": None, "bid_qty1": None}) == [] and rule.bids({}) == []
    assert rule.bids({"bid1": 0.01, "bid_qty1": 0.0, "bid2": float("nan"), "bid_qty2": 5}) == []


def test_a_sale_walks_down_the_bids_and_each_level_is_one_fill():
    leg = rule.sell([(0.02, 0.5), (0.01, 1000.0)], 169.49)                      # what was sold on one bracket on 11 November
    assert leg["sold"] == 169.49 and leg["money"] == pytest.approx(0.5 * 0.02 + 168.99 * 0.01)
    assert leg["fees"] == pytest.approx(0.0 + 0.16) and leg["margin"] == pytest.approx(0.5 * 0.98 + 168.99 * 0.99)
    short = rule.sell([(0.05, 3.0)], 10.0)
    assert short["sold"] == 3.0 and short["money"] == pytest.approx(0.15)       # no further than the recorded bids go
    assert rule.sell([], 10.0)["sold"] == 0.0


def test_what_a_sale_locks_is_the_money_in_less_fees_less_what_one_bracket_can_cost():
    books = {"a": [(0.60, 100.0)], "b": [(0.30, 100.0)], "c": [(0.20, 100.0)], "d": []}
    s = rule.sale(books, 100.0)
    assert set(s["legs"]) == {"a", "b", "c"} and s["money"] == pytest.approx(110.0)
    assert s["fees"] == pytest.approx(2.28 + 2.00 + 1.52)                        # 1.995 is a half: it goes to the even cent
    assert s["pays_at_most"] == 100.0 and s["locks"] == pytest.approx(110.0 - 5.80 - 100.0)
    assert s["margin"] == pytest.approx(40.0 + 70.0 + 80.0)
    # whichever bracket pays, at least that much is left; if none of the sold ones pays, all the money is
    for paid in ("a", "b", "c"):
        assert rule.result(s, {paid: 1.0}) == pytest.approx(s["locks"])
    assert rule.result(s, {"d": 1.0}) == pytest.approx(110.0 - 5.80)


def test_the_best_size_is_where_the_bids_stop_adding_up_to_a_dollar_and_the_fees():
    # thirty far brackets with a 1c bid for 1,000 and two near the price whose good bids are small
    far = {f"far{i:02d}": [(0.01, 1000.0)] for i in range(30)}
    near = {"n1": [(0.55, 50.0), (0.50, 400.0), (0.30, 5000.0)], "n2": [(0.35, 80.0), (0.30, 300.0), (0.10, 5000.0)]}
    books = {**far, **near}
    assert rule.sizes(books) == [50.0, 80.0, 380.0, 450.0, 1000.0, 5380.0, 5450.0]
    b = rule.best(books, room=1e9)
    # a unit brings 0.30 + 0.55 + 0.35 = 1.20 up to 50, then 1.15 up to 80, then 1.10 up to 380: each more than a dollar and the fees.
    # Beyond 380 it brings 0.90, so every further unit loses
    assert b["q"] == 380.0
    locks = {q: rule.sale(books, q)["locks"] for q in (50.0, 80.0, 380.0, 450.0, 1000.0)}
    assert b["locks"] == pytest.approx(locks[380.0]) and locks[380.0] > locks[80.0] > locks[50.0] > 0
    assert locks[450.0] < locks[380.0] and locks[1000.0] < 0
    # with twenty far brackets the second step already falls short once the fees are counted: 1.05 less 6.4 cents
    fewer = {k: v for k, v in books.items() if k not in {f"far{i:02d}" for i in range(20, 30)}}
    assert rule.best(fewer, room=1e9)["q"] == 50.0
    assert rule.best({}, 1e9) is None and rule.best(books, 0.0) is None


def test_the_money_limits_the_size_to_a_hundredth_of_a_contract():
    books = {f"far{i:02d}": [(0.01, 1000.0)] for i in range(59)} | {"near": [(0.60, 1000.0)]}
    full = rule.sale(books, 1000.0)
    assert full["margin"] == pytest.approx(59 * 990.0 + 400.0)
    q = rule.largest(books, 10_000.0, 1000.0)
    assert rule.sale(books, q)["margin"] <= 10_000.0 < rule.sale(books, q + 0.01)["margin"]
    assert q == pytest.approx(10_000.0 / (59 * 0.99 + 0.40), abs=0.01)
    b = rule.best(books, 10_000.0)
    assert b["q"] == q and b["locks"] == pytest.approx(b["money"] - b["fees"] - q)
    assert rule.largest(books, 1e9, 1000.0) == 1000.0


def test_a_sale_needs_25_dollars_and_10_in_the_last_half_hour():
    books = {f"far{i:02d}": [(0.01, 1000.0)] for i in range(40)} | {"near": [(0.80, 100.0)]}
    b = rule.best(books, 1e9)
    assert b["locks"] == pytest.approx(120.0 - 40 * 0.09 - 1.52 - 100.0)        # 100 a bracket: $1.20 a unit, less fees, less the dollar: $14.88
    assert rule.least(1801) == 25.0 and rule.least(1800) == 10.0 and rule.least(120) == 10.0
    assert rule.decide(books, left=3 * 3600, room=1e9) is None                   # hours before the end: not enough, so wait
    late = rule.decide(books, left=1800, room=1e9)
    assert late is not None and late["q"] == 100.0
    assert rule.decide(books, left=119, room=1e9) is None and rule.decide(books, left=rule.FIRST + 1, room=1e9) is None   # outside the readings
    big = {f"far{i:02d}": [(0.01, 1000.0)] for i in range(40)} | {"near": [(0.80, 200.0)]}
    assert rule.decide(big, left=3 * 3600, room=1e9)["locks"] >= 25.0


def test_a_bracket_first_quoted_after_the_sale_is_added_once_and_cannot_raise_what_is_paid():
    books = {f"far{i:02d}": [(0.01, 1000.0)] for i in range(40)} | {"near": [(0.80, 200.0)]}
    pos = rule.decide(books, left=3 * 3600, room=1e9)
    before = pos["locks"]
    later = {**books, "end-above": [(0.01, 1000.0)], "end-below": [(0.01, 50.0)]}
    legs = rule.top_up(later, pos, room=1e9)
    assert set(legs) == {"end-above", "end-below"} and legs["end-above"]["sold"] == pos["q"] == 200.0 and legs["end-below"]["sold"] == 50.0
    rule.add(pos, legs)
    assert pos["pays_at_most"] == 200.0 and pos["locks"] == pytest.approx(before + 2.0 + 0.5 - rule.fee(200, 0.01) - rule.fee(50, 0.01))
    assert rule.top_up(later, pos, room=1e9) == {}                               # nothing is sold twice
    tight = rule.top_up({**later, "new": [(0.01, 1000.0)]}, pos, room=99.0)      # the money that is left decides how much
    assert tight["new"]["sold"] == 100.0 and tight["new"]["margin"] == pytest.approx(99.0)
    assert rule.top_up({**later, "new": [(0.01, 1000.0)]}, pos, room=0.0) == {}


def test_a_ladder_is_read_165_times_from_five_and_a_half_hours_to_two_minutes_before_its_end():
    end = 1_794_520_800.0
    r = rule.readings(end)
    assert len(r) == 165 and r[0] == end - 330 * 60 and r[-1] == end - 120 and all(b - a == 120 for a, b in zip(r, r[1:]))
