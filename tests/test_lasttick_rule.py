"""The rule of test L1 (src/kht/trading/lasttick_rule.py, docs/11 section 5)."""

from __future__ import annotations

import json

import pytest

from kht.trading import lasttick_rule as rule

END = 1_794_434_400.0                      # a settlement time
REACH = {"btc": {h: 0.01 + 0.001 * h for h in range(1, 31)}, "xrp": {h: 0.05 for h in range(1, 31)}}


def above(strike, **kw):
    return {"slug": f"above-{strike}", "kind": "above_below", "coin": "btc", "horizon": "daily", "end": END, "strike": strike, **kw}


def book(bid=None, bid_qty=None, ask=None, ask_qty=None):
    return {"bid1": bid, "bid_qty1": bid_qty, "ask1": ask, "ask_qty1": ask_qty}


def test_gap_for_each_kind_of_market():
    assert rule.gap(above(78_000), 74_000) == (pytest.approx(4_000 / 74_000), "no")
    assert rule.gap(above(70_000), 74_000) == (pytest.approx(4_000 / 74_000), "yes")
    bracket = {"kind": "range", "lower": 74_000.0, "upper": 74_249.99}
    assert rule.gap(bracket, 74_100) == (pytest.approx(100 / 74_100), "yes")              # inside: the nearer edge
    assert rule.gap(bracket, 73_000) == (pytest.approx(1_000 / 73_000), "no")
    assert rule.gap({"kind": "range", "lower": None, "upper": 65_999.99}, 74_000)[1] == "no"     # "below 66,000"
    assert rule.gap({"kind": "range", "lower": 82_000.0, "upper": None}, 83_000)[1] == "yes"     # "above 82,000"
    assert rule.gap({"kind": "one_touch", "strike": 85_000, "direction": "up"}, 74_000) == (pytest.approx(11_000 / 74_000), "no")
    assert rule.gap({"kind": "one_touch", "strike": 57_500, "direction": "down"}, 74_000) == (pytest.approx(16_500 / 74_000), "no")
    assert rule.gap({"kind": "one_touch", "strike": 70_000, "direction": "up"}, 74_000) is None  # reached already
    assert rule.gap({"kind": "up_down", "price_to_beat": 73_000.0}, 74_000) == (pytest.approx(1_000 / 74_000), "yes")
    assert rule.gap({"kind": "up_down", "price_to_beat": 75_000.0}, 74_000)[1] == "no"
    assert rule.gap({"kind": "up_down", "price_to_beat": None}, 74_000) is None
    assert rule.gap({"kind": "range", "lower": None, "upper": None}, 74_000) is None
    assert rule.gap(above(78_000), 0) is None and rule.gap({"kind": "something else"}, 74_000) is None
    assert rule.gap({"kind": "above_below", "strike": "78000.0"}, 74_000.0)[1] == "no"          # values read back from a file are text


def test_the_reach_is_looked_up_for_the_minutes_left_plus_the_age_of_the_level_plus_one():
    assert rule.reach_for(REACH, "btc", 10.0) == pytest.approx(0.020) and rule.reach_for(REACH, "btc", 10.2) == pytest.approx(0.021)
    assert rule.reach_for(REACH, "btc", 0.3) == pytest.approx(0.011) and rule.reach_for(REACH, "btc", 31) is None and rule.reach_for(REACH, "doge", 5) is None
    m = above(76_000)                                                # 2.70% above an index of 74,000
    ts = END - 600                                                   # ten minutes left
    trade, why = rule.decide(m, book(bid=0.01, bid_qty=1500), ts, 74_000.0, ts - 240, REACH)        # level four minutes old: horizon 15, reach 2.5%
    assert why == "trade" and trade["reach"] == pytest.approx(0.025) and trade["age"] == 240
    trade, why = rule.decide(m, book(bid=0.01, bid_qty=1500), ts, 74_000.0, ts - 480, REACH)        # eight minutes old: horizon 19, reach 2.9%
    assert trade is None and why == "within reach"


def test_a_sale_to_the_best_bid_when_yes_will_pay_nothing():
    ts = END - 300
    trade, why = rule.decide(above(78_000), book(bid=0.01, bid_qty=1500, ask=0.02, ask_qty=100), ts, 74_000.0, ts - 60, REACH)
    assert why == "trade" and trade["side"] == "sell" and trade["price"] == 0.01 and trade["qty"] == 1500
    assert trade["fee"] == pytest.approx(0.095 * 0.01 * 0.99 * 1500) and trade["locked"] == pytest.approx(1485.0)
    assert trade["premium"] == pytest.approx(15.0 - 1.41075)
    assert rule.pnl(trade, 0.0) == pytest.approx(13.58925)
    assert rule.pnl(trade, 1.0) == pytest.approx(-1485.0 - 1.41075)
    big, _ = rule.decide(above(78_000), book(bid=0.01, bid_qty=1_520_680), ts, 74_000.0, ts - 60, REACH)
    assert big["qty"] == rule.CAP and big["shown"] == 1_520_680


def test_a_purchase_at_the_best_offer_when_yes_will_pay_a_dollar():
    ts = END - 300
    trade, why = rule.decide(above(70_000), book(bid=0.97, bid_qty=65, ask=0.99, ask_qty=255), ts, 74_000.0, ts - 60, REACH)
    assert why == "trade" and trade["side"] == "buy" and trade["price"] == 0.99 and trade["qty"] == 255 and trade["locked"] == pytest.approx(252.45)
    assert rule.pnl(trade, 1.0) == pytest.approx(255 * 0.01 - 0.095 * 0.99 * 0.01 * 255)
    assert rule.pnl(trade, 0.0) == pytest.approx(-252.45 - trade["fee"])
    assert rule.pnl(trade, 0.5) == pytest.approx(255 * (0.5 - 0.99) - trade["fee"])


def test_what_is_not_traded_and_why():
    ts = END - 300
    args = (74_000.0, ts - 60, REACH)
    assert rule.decide(above(78_000), book(bid=0.01, bid_qty=1500), END - 901, 74_000.0, END - 960, REACH)[1] == "outside the time window"
    assert rule.decide(above(78_000), book(bid=0.01, bid_qty=1500), END - 119, 74_000.0, END - 180, REACH)[1] == "outside the time window"
    assert rule.decide(above(78_000), book(bid=0.01, bid_qty=1500), END - 900, 74_000.0, END - 960, REACH)[1] == "trade"
    assert rule.decide(above(78_000), book(bid=0.01, bid_qty=1500), ts, 74_000.0, ts - 601, REACH)[1] == "no fresh index level"
    assert rule.decide(above(78_000), book(bid=0.01, bid_qty=1500), ts, None, None, REACH)[1] == "no fresh index level"
    assert rule.decide(above(74_500), book(bid=0.01, bid_qty=1500), ts, *args)[1] == "within reach"
    assert rule.decide(above(78_000), book(ask=0.02, ask_qty=100), ts, *args)[1] == "out of reach, nobody bidding"
    assert rule.decide(above(70_000), book(bid=0.98, bid_qty=105), ts, *args)[1] == "out of reach, nobody offering"
    assert rule.decide(above(78_000), book(bid=0.40, bid_qty=10), ts, *args)[1] == "out of reach, but the book disagrees"
    assert rule.decide(above(70_000), book(ask=0.60, ask_qty=10), ts, *args)[1] == "out of reach, but the book disagrees"
    assert rule.decide(above(78_000), book(bid=0.05, bid_qty=10), ts, *args)[1] == "trade"
    assert rule.decide(above(70_000), book(ask=0.95, ask_qty=10), ts, *args)[1] == "trade"
    assert rule.decide({**above(78_000), "coin": "doge"}, book(bid=0.01, bid_qty=1500), ts, *args)[1] == "no reach for this coin and horizon"
    assert rule.decide({"slug": "x", "kind": "one_touch", "coin": "btc", "end": END, "strike": 70_000, "direction": "up"}, book(), ts, *args)[1] == "cannot be read"


def test_the_small_account_takes_trades_in_order_until_its_money_is_locked():
    ts = END - 600
    trades = [rule.decide(above(78_000 + 250 * i), book(bid=0.01, bid_qty=2000), ts + i, 74_000.0, ts - 60, REACH)[0] for i in range(8)]
    later = rule.decide({**above(79_000), "end": END + 3600}, book(bid=0.01, bid_qty=2000), END + 3000, 74_000.0, END + 2940, REACH)[0]
    taken = rule.small_account(trades + [later], money=10_000.0)
    first = [t for t in taken if t["end"] == END]
    assert len(first) == 6 and sum(t["locked"] for t in first) == pytest.approx(10_000.0)
    assert [t["qty"] for t in first[:5]] == [2000.0] * 5 and first[5]["qty"] == pytest.approx(2000 * 100 / 1980)     # the sixth is taken in part
    assert first[5]["premium"] == pytest.approx(trades[5]["premium"] * 100 / 1980)
    assert [t["slug"] for t in taken if t["end"] == END + 3600] == ["above-79000"]                 # the money is back for the next settlement


def test_the_reach_table_is_read_from_its_file(tmp_path):
    path = tmp_path / "reach.json"
    path.write_text(json.dumps({"one_in": 5000, "reach": {"btc": {"1": 0.011, "16": 0.031}}}))
    assert rule.load_reach(path) == {"btc": {1: 0.011, 16: 0.031}}
