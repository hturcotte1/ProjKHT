"""The program that would place the last-tick sales (src/kht/trading/us_taker.py, docs/12_us_taker.md)."""

from __future__ import annotations

import csv
import gzip
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from kht.trading import lasttick_rule as rule
from kht.trading import us_taker as tk
from kht.trading.us_lasttick import BOOK_FIELDS, INDEX_FIELDS, MARKET_FIELDS

END = 1_794_520_800.0            # 12 November 2026, 22:00:00 UTC
REACH = {"btc": {h: 0.03 for h in range(1, 31)}, "eth": {h: 0.03 for h in range(1, 31)}}
LEVEL = 74_000.0


def far(slug="cpc-btc-above-day-2026-11-12-80000", strike=80_000.0, coin="btc", end=END, **kw):
    """A level 8% above the index: out of reach, and "Yes" will pay nothing."""
    return {"slug": slug, "kind": "above_below", "horizon": "daily", "coin": coin, "end": end, "strike": strike, **kw}


def book(bid=0.01, bid_qty=1500.0, ask=0.02, ask_qty=200.0):
    return {"bid1": bid, "bid_qty1": bid_qty, "ask1": ask, "ask_qty1": ask_qty}


def engine(tmp_path, broker=None, clock=None, brake=None, **cfg):
    e = tk.Engine(tmp_path, tk.TakerConfig(yardstick="strict" if brake is None else "recent", **cfg), broker or tk.PaperTaker(), REACH, brake,
                  now=clock or (lambda: END - 600.0))
    e.on_index("btc", LEVEL, END - 15 * 60 - 60)       # a level published a minute before the window opens
    e.on_index("eth", 2_000.0, END - 15 * 60 - 60)
    return e


def actions(tmp_path):
    with (tmp_path / "actions.csv").open(newline="") as fh:
        return list(csv.DictReader(fh))


def test_an_order_is_an_immediate_or_cancel_limit_order_and_nothing_outside_the_limits_is_built():
    body = tk.order_body(tk.Ticket("cpc-btc-above-day-2026-11-12-80000", "sell", 0.01, 500.0, END))
    assert body == {"marketSlug": "cpc-btc-above-day-2026-11-12-80000", "type": "ORDER_TYPE_LIMIT", "price": {"value": "0.01", "currency": "USD"}, "quantity": 500,
                    "tif": "TIME_IN_FORCE_IMMEDIATE_OR_CANCEL", "intent": "ORDER_INTENT_BUY_SHORT", "manualOrderIndicator": "MANUAL_ORDER_INDICATOR_AUTOMATIC",
                    "synchronousExecution": True, "maxBlockTime": "5"}
    assert "participateDontInitiate" not in body and "goodTillTime" not in body       # it takes what is there and leaves nothing resting
    buy = tk.order_body(tk.Ticket("m", "buy", 0.99, 10.0, END))
    assert buy["intent"] == "ORDER_INTENT_BUY_LONG" and buy["price"]["value"] == "0.99"
    for bad in (tk.Ticket("m", "sell", 0.06, 10.0, END), tk.Ticket("m", "sell", 0.0, 10.0, END), tk.Ticket("m", "buy", 0.94, 10.0, END),
                tk.Ticket("m", "sell", 0.01, 0.5, END), tk.Ticket("m", "sell", 0.01, 10.5, END), tk.Ticket("m", "sell", 0.01, tk.MAX_CAP + 1, END),
                tk.Ticket("m", "short", 0.01, 10.0, END)):
        with pytest.raises(ValueError):
            tk.order_body(bad)


def test_the_configuration_cannot_ask_for_more_than_the_code_allows(tmp_path):
    with pytest.raises(ValueError):
        tk.TakerConfig(money=tk.MAX_MONEY + 1)
    with pytest.raises(ValueError):
        tk.TakerConfig(cap=tk.MAX_CAP + 1)
    with pytest.raises(ValueError):
        tk.TakerConfig(sides=("sell", "hold"))
    with pytest.raises(ValueError):
        tk.TakerConfig(yardstick="loose")
    shipped = tk.TakerConfig.load(Path(__file__).resolve().parents[1] / "config" / "us_taker.json")
    assert shipped.money <= 500 and shipped.coins == ("btc",) and shipped.sides == ("sell",) and shipped.stop_on_loss      # what is in the repository is small
    reach, brake = shipped.yardsticks(Path(__file__).resolve().parents[1])
    assert set(reach) == {"btc", "eth", "sol", "xrp"} and brake is not None and 0 < brake["btc"] < 0.05


def test_the_answer_to_an_order_is_read_for_what_was_filled():
    t = tk.Ticket("m", "sell", 0.01, 500.0, END)
    order = lambda cum, px: {"order": {"cumQuantity": cum, "avgPx": px, "state": "ORDER_STATE_FILLED"}, "type": "EXECUTION_TYPE_FILL"}
    whole = tk.read_fill({"id": "1", "executions": [{"order": {"cumQuantity": "0"}, "type": "EXECUTION_TYPE_NEW"}, order("500", {"value": "0.0100", "currency": "USD"})]}, t)
    assert whole.qty == 500.0 and whole.price == 0.01 and whole.fee == pytest.approx(0.095 * 0.01 * 0.99 * 500) and whole.note == "filled"
    part = tk.read_fill({"executions": [order(120.0, "0.01"), {"order": {"cumQuantity": 120.0, "avgPx": "0.01"}, "type": "EXECUTION_TYPE_CANCELED"}]}, t)
    assert part.qty == 120.0 and part.note == "filled in part"
    # the answer may give the price of "No" for a sale of "Yes": 99c is 1c
    assert tk.read_fill({"executions": [order(500, "0.99")]}, t).price == pytest.approx(0.01)
    # the fee is the exchange's own figure where it gives one
    paid = tk.read_fill({"executions": [{**order(500, "0.01"), "commissionNotionalCollected": {"value": "0.47", "currency": "USD"}}]}, t)
    assert paid.fee == 0.47
    refused = tk.read_fill({"executions": [{"order": {"cumQuantity": 0}, "type": "EXECUTION_TYPE_REJECTED", "orderRejectReason": "ORD_REJECT_REASON_NO_LIQUIDITY"}]}, t)
    assert refused.qty == 0.0 and "NO_LIQUIDITY" in refused.note
    nothing = tk.read_fill({"executions": [{"order": {"cumQuantity": 0}, "type": "EXECUTION_TYPE_CANCELED"}]}, t)
    assert nothing.qty == 0.0 and nothing.note == "nothing filled"
    assert tk.read_fill({"id": "1"}, t).qty is None and tk.read_fill(None, t).qty is None          # no report at all: not known, which is not the same as nothing


def test_on_paper_an_order_is_filled_against_the_book_it_was_decided_on():
    paper = tk.PaperTaker()
    assert paper.take(tk.Ticket("m", "sell", 0.01, 500.0, END), book(bid_qty=1500.0)).qty == 500.0
    short = paper.take(tk.Ticket("m", "sell", 0.01, 500.0, END), book(bid_qty=120.7))
    assert short.qty == 120.0 and short.note == "filled in part"                                  # whole contracts only
    assert paper.take(tk.Ticket("m", "sell", 0.02, 500.0, END), book(bid=0.01)).qty == 0.0        # the bid is below the order's price
    assert paper.take(tk.Ticket("m", "sell", 0.01, 500.0, END), {"bid1": "", "bid_qty1": ""}).qty == 0.0
    assert paper.take(tk.Ticket("m", "buy", 0.99, 50.0, END), book(ask=0.99, ask_qty=30.0)).qty == 30.0
    assert paper.take(tk.Ticket("m", "buy", 0.98, 50.0, END), book(ask=0.99, ask_qty=30.0)).qty == 0.0


def test_the_engine_sends_one_order_a_market_inside_the_window_and_keeps_to_its_money(tmp_path):
    e = engine(tmp_path, money=500.0, cap=500.0)
    a, b, c = far("a", 80_000.0), far("b", 80_250.0), far("c", 80_500.0)
    assert e.on_book(a, book(), END - 20 * 60) is None and not e.done               # twenty minutes before the end: outside the rule's window
    first = e.on_book(a, book(), END - 14 * 60)
    assert first.qty == 500.0 and e.held["a"].qty == 500.0 and e.tied_up(END) == pytest.approx(495.0)      # the bid was for 1,500: the cap decides
    assert e.on_book(a, book(), END - 13 * 60) is None and e.n.orders == 1          # never a second order to the same market
    second = e.on_book(b, book(), END - 13 * 60)
    assert second.qty == 5.0 and e.tied_up(END) == pytest.approx(495.0 + 4.95)      # $5 was left of the $500: five whole contracts
    assert e.on_book(c, book(), END - 12 * 60) is None and "c" not in e.done        # nothing left; the market is not used up by that
    other_evening = far("d", 80_000.0, end=END + 86_400.0)
    e.on_index("btc", LEVEL, END + 86_400.0 - 16 * 60)
    assert e.on_book(other_evening, book(), END + 86_400.0 - 10 * 60).qty == 500.0   # the sum is for each settlement time
    rows = actions(tmp_path)
    assert [(r["slug"], r["side"], r["price"], r["wanted"], r["filled"]) for r in rows] == [("a", "sell", "0.01", "500.0", "500.0"), ("b", "sell", "0.01", "5.0", "5.0"),
                                                                                            ("d", "sell", "0.01", "500.0", "500.0")]
    assert rows[0]["mode"] == "paper" and float(rows[0]["gap"]) == pytest.approx(6000 / 74000, abs=1e-4) and rows[0]["reach"] == "0.03"
    # what it holds and what it has used up survive a restart
    again = tk.Engine(tmp_path, tk.TakerConfig(yardstick="strict", money=500.0, cap=500.0), tk.PaperTaker(), REACH)
    assert again.done == {"a", "b", "d"} and again.held["b"].qty == 5.0 and again.tied_up(END) == pytest.approx(499.95)


def test_a_reading_the_rule_does_not_trade_sends_nothing(tmp_path):
    e = engine(tmp_path)
    near = far("near", 75_000.0)                                                     # 1.35% away: within reach
    assert e.on_book(near, book(), END - 10 * 60) is None
    assert e.on_book(far("nobody"), book(bid="", bid_qty=""), END - 10 * 60) is None  # out of reach, nobody bidding
    assert e.on_book(far("dear"), book(bid=0.08), END - 10 * 60) is None              # out of reach, but the book disagrees
    stale = tk.Engine(tmp_path / "stale", tk.TakerConfig(yardstick="strict"), tk.PaperTaker(), REACH)
    stale.on_index("btc", LEVEL, END - 40 * 60)                                       # the only level known is half an hour old
    assert stale.on_book(far("x"), book(), END - 10 * 60) is None
    assert e.n.orders == 0 and stale.n.orders == 0 and not (tmp_path / "actions.csv").exists()
    assert e.n.why == {"within reach": 1, "out of reach, nobody bidding": 1, "out of reach, but the book disagrees": 1} and stale.n.why == {"no fresh index level": 1}


def test_coins_and_sides_outside_the_configuration_are_left_alone(tmp_path):
    e = engine(tmp_path / "one", coins=("btc",), sides=("sell",))
    eth = far("eth-far", 2_200.0, coin="eth")
    sure = far("sure", 68_000.0)                                                     # 8% below the index: "Yes" will pay, and 99c is offered
    assert e.on_book(eth, book(), END - 10 * 60) is None
    assert e.on_book(sure, book(bid=0.98, ask=0.99, ask_qty=300.0), END - 10 * 60) is None and e.n.orders == 0
    both = engine(tmp_path / "two", coins=("btc", "eth"), sides=("sell", "buy"), money=1_000.0)
    assert both.on_book(eth, book(), END - 10 * 60).qty == 500.0
    bought = both.on_book(sure, book(bid=0.98, ask=0.99, ask_qty=300.0), END - 10 * 60)
    assert bought.qty == 300.0 and both.held["sure"].side == "buy" and both.held["sure"].tied_up() == pytest.approx(297.0)
    assert both.settle("sure", 1.0) == pytest.approx(300 * 0.01 - 0.095 * 0.99 * 0.01 * 300)


def test_a_loss_stops_everything_until_a_person_removes_the_file(tmp_path):
    e = engine(tmp_path, money=2_000.0)
    e.on_book(far("a", 80_000.0), book(), END - 10 * 60)
    e.on_book(far("b", 80_250.0), book(), END - 10 * 60)
    kept = e.settle("a", 0.0)
    assert kept == pytest.approx(500 * 0.01 - 0.095 * 0.01 * 0.99 * 500) and e.stopped() is None
    assert e.settle("a", 0.0) is None                                                # nothing is settled twice
    lost = e.settle("b", 1.0)                                                        # the level came in after all
    assert lost == pytest.approx(-(500 * 0.99) - 0.095 * 0.01 * 0.99 * 500) and e.n.lost == 1
    assert "stopped after a loss of $495" in e.stopped() and "b" in e.stopped()
    assert e.on_book(far("c", 80_500.0), book(), END - 9 * 60) is None and e.n.orders == 2 and "c" not in e.done
    assert "**STOPPED:**" in e.status_text()
    with (tmp_path / "settled.csv").open(newline="") as fh:
        assert [(r["slug"], r["settle"]) for r in csv.DictReader(fh)] == [("a", "0.0"), ("b", "1.0")]
    (tmp_path / "STOP").unlink()
    assert e.on_book(far("c", 80_500.0), book(), END - 9 * 60).qty == 500.0
    quiet = engine(tmp_path / "quiet", stop_on_loss=False, money=2_000.0)
    quiet.on_book(far("b", 80_250.0), book(), END - 10 * 60)
    quiet.settle("b", 1.0)
    assert quiet.stopped() is None


def test_the_second_yardstick_does_not_trade_when_the_index_has_been_moving_fast_or_is_not_known(tmp_path):
    brake = {"btc": 0.01}
    calm = lambda e: [e.on_history("btc", LEVEL + 10 * k, END - 15 * 60 - 60 - 300 * k) for k in range(1, 9)]
    unknown = engine(tmp_path / "u", brake=brake)
    assert unknown.on_book(far(), book(), END - 10 * 60) is None and unknown.n.why == {"out of reach, too little index history": 1}
    quiet = engine(tmp_path / "q", brake=brake)
    calm(quiet)
    assert quiet.on_book(far(), book(), END - 10 * 60).qty == 500.0
    fast = engine(tmp_path / "f", brake=brake)
    calm(fast)
    fast.on_history("btc", LEVEL * 0.98, END - 15 * 60 - 60 - 300 * 4)               # one five-minute change of 2% in the hour before
    assert fast.on_book(far(), book(), END - 10 * 60) is None and fast.n.why == {"out of reach, but the index has been moving fast": 1}


class Wire:
    """A stand-in for the connection to the exchange: it writes down what it is asked and answers from a list."""

    def __init__(self, answers):
        self.answers, self.calls = list(answers), []

    def _call(self, method, path, body=None, params=None):
        self.calls.append((method, path, body))
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_a_real_order_is_sent_once_and_a_lost_answer_is_never_retried(tmp_path):
    filled = {"id": "9", "executions": [{"order": {"cumQuantity": "500", "avgPx": {"value": "0.01", "currency": "USD"}}, "type": "EXECUTION_TYPE_FILL"}]}
    wire = Wire([filled, RuntimeError("HTTP 504 for POST /v1/orders"), filled])
    e = engine(tmp_path, broker=tk.LiveTaker(wire), money=2_000.0)
    e.mode = "live"
    assert e.on_book(far("a", 80_000.0), book(), END - 10 * 60).qty == 500.0
    lost = e.on_book(far("b", 80_250.0), book(), END - 10 * 60)
    assert lost.qty is None and "not known" in lost.note and "b" in e.done and "b" not in e.held and e.n.unknown == 1
    assert e.on_book(far("b", 80_250.0), book(), END - 9 * 60) is None                # it may have gone through: it is not sent again
    assert [(m, p, b["marketSlug"]) for m, p, b in wire.calls] == [("POST", "/v1/orders", "a"), ("POST", "/v1/orders", "b")]
    assert all(b["tif"] == "TIME_IN_FORCE_IMMEDIATE_OR_CANCEL" and b["intent"] == "ORDER_INTENT_BUY_SHORT" for _, _, b in wire.calls)
    rows = actions(tmp_path)
    assert rows[1]["filled"] == "" and "look at the account" in rows[1]["note"] and rows[1]["mode"] == "live"
    # the market was written down as used before the order went out, so a crash in between cannot lead to a second order
    assert "b" in json.loads((tmp_path / "positions.json").read_text())["done"]


def test_a_preview_goes_to_the_preview_call_only(tmp_path):
    wire = Wire([{"preview": "ok"}])
    live = tk.LiveTaker(wire, preview=True)
    e = engine(tmp_path, broker=live)
    got = e.on_book(far(), book(), END - 10 * 60)
    assert got.qty == 0.0 and got.note == "previewed, not sent" and not e.held
    assert [(m, p) for m, p, _ in wire.calls] == [("POST", "/v1/order/preview")] and live.previews == [{"preview": "ok"}]


# ---------------------------------------------------------------------------- a recording, replayed

spec = importlib.util.spec_from_file_location("us_lasttick_score", Path(__file__).resolve().parents[1] / "scripts" / "us_lasttick_score.py")
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)


def recording(state):
    """An evening as the recorder writes it: twelve far levels with 1c bids, one near the price, read every minute for 17 minutes."""
    markets, books, index = [], [], []
    for i in range(12):
        row = dict.fromkeys(MARKET_FIELDS, "")
        row.update({"run": "r1", "slug": f"cpc-btc-above-day-2026-11-12-{80000 + 250 * i}", "kind": "above_below", "horizon": "daily", "coin": "btc", "index": "BRTI",
                    "end": END, "strike": 80000.0 + 250 * i, "first_seen": END - 17 * 60})
        markets.append(row)
    near = dict.fromkeys(MARKET_FIELDS, "")
    near.update({"run": "r1", "slug": "cpc-btc-above-day-2026-11-12-74500", "kind": "above_below", "horizon": "daily", "coin": "btc", "index": "BRTI", "end": END,
                 "strike": 74500.0, "first_seen": END - 17 * 60})
    markets.append(near)
    for k in range(17, -1, -1):
        for j, m in enumerate(markets):
            row = dict.fromkeys(BOOK_FIELDS, "")
            ts = END - k * 60 + j                                        # a sweep reads one book a second
            row.update({"run": "r1", "ts": ts, "slug": m["slug"], "left": END - ts, "state": "OPEN", "bid1": 0.01, "bid_qty1": 1000.0 + 100 * j, "ask1": 0.02, "ask_qty1": 50.0})
            books.append(row)
    for k in range(5):
        at = END - 20 * 60 + 300 * k
        index.append({"run": "r1", "ts": at + 45.0, "coin": "btc", "level": 74_000.0 + 5 * k, "at": at, "slug": "x"})
    d = state / "runs" / "r1"
    d.mkdir(parents=True)
    with gzip.open(d / "books.csv.gz", "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=BOOK_FIELDS)
        w.writeheader()
        w.writerows(books)
    for name, fields, rows in (("markets.csv", MARKET_FIELDS, markets), ("index.csv", INDEX_FIELDS, index)):
        with (d / name).open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    with (state / "settlements.csv").open("w", newline="") as fh:
        fh.write("slug,settle,checked\n" + "".join(f"{m['slug']},0.0,1\n" for m in markets))


def test_a_replay_of_a_recording_makes_the_trades_the_scorer_counts(tmp_path):
    rec = tmp_path / "rec"
    recording(rec)
    got = tk.load_recording(rec)
    assert len(got["books"]) == 18 * 13 and len(got["markets"]) == 13 and len(got["index"]) == 5 and len(got["settlements"]) == 13
    e = tk.Engine(tmp_path / "state", tk.TakerConfig(yardstick="strict", money=10_000.0, cap=2_000.0), tk.PaperTaker(), REACH, mode="replay")
    line = tk.replay(e, got["books"], got["markets"], got["index"], got["levels"], got["settlements"])
    # the scorer, on the same files
    b, m, i = score.load(rec)
    trades, _ = score.apply(b, m, i, REACH)
    small = rule.small_account(trades, money=10_000.0)
    mine = {r["slug"]: float(r["filled"]) for r in actions(tmp_path / "state")}
    assert set(mine) == {t["slug"] for t in small}
    assert len(mine) == 8                                                             # bids of 1,000, 1,100, ... contracts: the $10,000 runs out in the eighth
    assert "cpc-btc-above-day-2026-11-12-74500" not in mine
    for t in small:
        assert mine[t["slug"]] == pytest.approx(t["qty"], abs=1.0)                    # whole contracts here, fractions there
    assert sum(mine.values()) == pytest.approx(sum(t["qty"] for t in small), abs=1.0)
    assert line["orders"] == 8 and line["settled"] == 8 and line["lost"] == 0 and line["pnl"] == pytest.approx(sum(rule.pnl(t, 0.0) for t in small), abs=0.02)
    assert not e.held and "mode: replay" in (tmp_path / "state" / "STATUS.md").read_text()


# ---------------------------------------------------------------------------- the live loop, against a stand-in for the exchange

def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def listed(slug, kind, horizon, end, start=None, strike=None, ptb=None):
    money = lambda x: None if x is None else {"value": str(x), "currency": "USD"}
    return {"slug": slug, "assetPriceTerms": {"marketType": "ASSET_PRICE_MARKET_TYPE_" + kind, "asset": {"symbol": "btc"}, "indexSymbol": "BRTI", "horizon": horizon,
                                              "windowStart": None if start is None else iso(start), "windowEnd": iso(end), "priceToBeat": money(ptb),
                                              "strike": money(strike), "rangeLower": None, "rangeUpper": None, "direction": "ASSET_PRICE_DIRECTION_UNSPECIFIED"}}


class Clock:
    def __init__(self, t):
        self.t = t

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


class FakeUS:
    def __init__(self, clock):
        self.clock, self.books_read, self.asked = clock, [], []

    def iter_markets(self, **filters):
        t = self.clock.t
        five = END - 300 * (int((END - t) // 300) + 1)
        out = [listed("cpc-btc-updown-5m-now", "UP_DOWN", "5m", five + 300, start=five, ptb=LEVEL)]
        if t <= END:
            out += [listed("cpc-btc-above-day-2026-11-12-80000", "ABOVE_BELOW", "daily", END, strike=80000),
                    listed("cpc-btc-above-day-2026-11-12-74500", "ABOVE_BELOW", "daily", END, strike=74500)]
        return iter(out)

    def book(self, slug):
        self.books_read.append((round(END - self.clock.t), slug))
        level = lambda px, qty: {"px": {"value": str(px), "currency": "USD"}, "qty": str(qty)}
        return {"bids": [level(0.01, 1500)], "offers": [level(0.02, 100)], "state": "MARKET_STATE_OPEN", "stats": {}}

    def market(self, slug):
        self.asked.append(slug)
        return {"assetPriceTerms": {"priceToBeat": {"value": str(LEVEL), "currency": "USD"}}}

    def settlement(self, slug):
        return 0.0 if self.clock.t > END + 30 else None


def test_the_live_loop_reads_orders_once_and_settles(tmp_path):
    clock = Clock(END - 25 * 60)
    us = FakeUS(clock)
    reach, brake = tk.TakerConfig().yardsticks(Path(__file__).resolve().parents[1])   # the yardsticks shipped in the repository, brake included
    e = tk.Engine(tmp_path, tk.TakerConfig(money=500.0, cap=500.0), tk.PaperTaker(), reach, brake, now=clock.now)
    line = e.run(30, us, sleep=clock.sleep)
    rows = actions(tmp_path)
    assert [(r["slug"], r["filled"]) for r in rows] == [("cpc-btc-above-day-2026-11-12-80000", "500.0")]       # the far level once; the near one never
    assert rule.LAST <= float(rows[0]["left"]) <= rule.FIRST
    assert line["orders"] == 1 and line["filled"] == 1 and line["settled"] == 1 and line["lost"] == 0 and line["errors"] == 0
    assert line["pnl"] == pytest.approx(500 * 0.01 - 0.095 * 0.01 * 0.99 * 500)
    first_read = max(left for left, slug in us.books_read if slug.endswith("80000"))
    assert first_read <= rule.FIRST + 90 and not any(slug.endswith("80000") and left < float(rows[0]["left"]) - 1 for left, slug in us.books_read)   # not read again once sold
    assert any("updown-5m" in s for s in us.asked)                                    # the brake's five-minute marks were looked up
    status = (tmp_path / "STATUS.md").read_text()
    assert "orders: 1; filled: 1" in status and "settled: 1; lost: 0" in status and "Nothing was sent anywhere" in status
