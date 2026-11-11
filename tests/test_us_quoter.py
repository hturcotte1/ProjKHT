"""The system that rests orders before games on Polymarket US: its decisions, its paper broker, its engine."""

from __future__ import annotations

import csv
import json

import pytest

from kht.trading import us_quoter as uq
from kht.trading import us_rewards as rw

T0 = rw._when("2026-11-12T15:00:00Z")
START = rw._when("2026-11-12T18:00:00Z")


def px(v: float) -> dict:
    return {"value": f"{v:.4f}", "currency": "USD"}


def book(bids, asks, vol=0.0, notional=0.0, last=None, last_t=None, state="MARKET_STATE_OPEN") -> dict:
    stats = {"sharesTraded": f"{vol:.4f}", "notionalTraded": px(notional)}
    if last is not None:
        stats.update({"lastTradePx": px(last), "lastTradeSetTime": last_t})
    return {"bids": [{"px": px(p), "qty": str(q)} for p, q in bids], "offers": [{"px": px(p), "qty": str(q)} for p, q in asks], "state": state, "stats": stats}


def entry(slug, program="itf_moneyline_dayof_1", start="2026-11-12 18:00:00+00", pool=12, target=1000, discount=0.5) -> dict:
    tp = {"programId": program, "programType": "liquidityProgram", "rewardPool": pool, "status": "active", "discountFactor": discount, "targetSize": target, "period": "day_of"}
    return {"marketSlug": slug, "timePeriods": [tp], "instrumentState": "INSTRUMENT_STATE_OPEN", "category": "SPR", "eventStartTime": start, "instrumentProduct": "aec"}


GAME = {"slug": "aec-itfme-a-b-2026-11-12", "program": "itf_moneyline_dayof_1", "pool": 12.0, "target": 1000.0, "discount": 0.5, "max_spread": None,
        "start": START, "markets_in_event": 1}
QUIET = book([(0.45, 100.0), (0.01, 2000.0)], [(0.47, 300.0), (0.99, 2000.0)])       # 100 contracts would hold a half and a quarter of the score


def quote(raw=QUIET, game=GAME) -> dict:
    return rw.quote_state(rw.read_book(raw), game)


# ------------------------------------------------------------------ settings
def test_settings_are_checked():
    with pytest.raises(ValueError):
        uq.QuoterConfig(size=5000)
    with pytest.raises(ValueError):
        uq.QuoterConfig(renew=200, expire=180)
    with pytest.raises(ValueError):
        uq.QuoterConfig(refresh=120, expire=180)
    with pytest.raises(ValueError):
        uq.QuoterConfig(max_games=0)


def test_settings_load_from_a_file_and_refuse_what_they_do_not_know(tmp_path):
    p = tmp_path / "q.json"
    p.write_text(json.dumps({"_comment": "x", "size": 50, "programmes": ["utr_moneyline"]}))
    cfg = uq.QuoterConfig.load(p)
    assert cfg.size == 50 and cfg.programmes == ("utr_moneyline",) and cfg.max_games == 20
    p.write_text(json.dumps({"sise": 50}))
    with pytest.raises(ValueError):
        uq.QuoterConfig.load(p)


def test_the_example_settings_file_loads():
    from pathlib import Path

    cfg = uq.QuoterConfig.load(Path(__file__).resolve().parents[1] / "config" / "us_quoter.json")
    assert cfg.size <= uq.MAX_SIZE and cfg.max_at_risk > 0


# ------------------------------------------------------------------ positions
def test_what_a_position_can_still_lose():
    assert uq.Position(bought=100, cost=45).at_risk() == pytest.approx(45)                       # long: what was paid
    assert uq.Position(sold=100, proceeds=47).at_risk() == pytest.approx(53)                     # short: a dollar less what was received
    assert uq.Position(bought=100, cost=45, sold=100, proceeds=47).at_risk() == 0                # flat, two dollars ahead
    assert uq.Position(bought=100, cost=45, sold=40, proceeds=18.8).at_risk() == pytest.approx(26.2)
    assert uq.Position(bought=40, cost=18, sold=100, proceeds=47).at_risk() == pytest.approx(31)
    p = uq.Position(bought=100, cost=45, sold=40, proceeds=18.8)
    assert p.value(1.0) == pytest.approx(33.8) and p.value(0.0) == pytest.approx(-26.2)


# ------------------------------------------------------------------ the orders for one game
def test_a_fresh_game_gets_one_opening_order_on_each_side():
    cfg = uq.QuoterConfig()
    closing, opening = uq.wants_for_game(GAME, quote(), uq.Position(), cfg, T0)
    assert closing == []
    assert [(w.side, w.intent, w.price, w.qty) for w in opening] == [("bid", uq.BUY_YES, 0.45, 100.0), ("ask", uq.BUY_NO, 0.47, 100.0)]
    assert all(w.expires == T0 + cfg.expire for w in opening)
    assert opening[0].worst() == pytest.approx(45.0) and opening[1].worst() == pytest.approx(53.0)


def test_orders_never_outlive_the_pull_before_the_game():
    cfg = uq.QuoterConfig()
    late = START - rw.PULL - 60
    _, opening = uq.wants_for_game(GAME, quote(), uq.Position(), cfg, late)
    assert all(w.expires == START - rw.PULL for w in opening)
    assert uq.wants_for_game(GAME, quote(), uq.Position(), cfg, START - rw.PULL - 2) == ([], [])


def test_a_filled_side_is_not_offered_again_and_the_other_side_closes_first():
    cfg = uq.QuoterConfig()
    closing, opening = uq.wants_for_game(GAME, quote(), uq.Position(bought=60, cost=27), cfg, T0)
    assert [(w.side, w.intent, w.qty) for w in closing] == [("ask", uq.SELL_YES, 60.0)]          # sell what is held
    assert [(w.side, w.intent, w.qty) for w in opening] == [("bid", uq.BUY_YES, 40.0), ("ask", uq.BUY_NO, 40.0)]
    closing, opening = uq.wants_for_game(GAME, quote(), uq.Position(sold=100, proceeds=47), cfg, T0)
    assert [(w.side, w.intent, w.qty) for w in closing] == [("bid", uq.SELL_NO, 100.0)]          # buy back what is owed
    assert opening == []
    done = uq.Position(bought=100, cost=45, sold=100, proceeds=47)
    assert uq.wants_for_game(GAME, quote(), done, cfg, T0) == ([], [])                           # both sides done: nothing more in this game


def test_nothing_is_wanted_in_a_book_that_cannot_be_rested_in():
    wide = quote(book([(0.30, 100.0)], [(0.60, 100.0)]))
    assert uq.wants_for_game(GAME, wide, uq.Position(), uq.QuoterConfig(), T0) == ([], [])


def test_expected_reward_is_the_formula_over_the_time_left():
    q = quote()
    left = START - rw.PULL - T0                                                                  # two hours fifty minutes
    assert uq.expected_reward(GAME, q, 100, T0) == pytest.approx(12.0 * (0.5 + 0.25) / (2 * rw.WINDOW) * left)
    assert uq.expected_reward(GAME, q, 100, START) == 0.0
    assert uq.expected_reward(GAME, {"quoting": False}, 100, T0) == 0.0


# ------------------------------------------------------------------ which games
def cand(slug, expected=2.0, accrued=0.0, lead=7200.0, quoting=True):
    return {"slug": slug, "quoting": quoting, "lead": lead, "expected": expected, "accrued": accrued}


def test_choose_keeps_what_it_has_and_adds_the_best_paying():
    cfg = uq.QuoterConfig(max_games=3)
    cands = [cand("a", 0.2), cand("b", 3.0), cand("c", 2.0), cand("d", 5.0), cand("e", 1.0), cand("f", 9.0, quoting=False), cand("g", 9.0, lead=600)]
    assert uq.choose(cands, {"a"}, set(), cfg) == ["a", "d", "b"]          # a stays although it pays little; f cannot be rested in; g is too close
    assert uq.choose(cands, set(), set(), cfg) == ["d", "b", "c"]
    assert uq.choose([cand("e", 0.5, accrued=0.8)], set(), set(), cfg) == ["e"]      # what it has earned counts towards the minimum
    assert uq.choose([cand("e", 0.5, accrued=0.2)], set(), set(), cfg) == []


def test_choose_starts_nothing_new_while_too_many_games_hold_a_position():
    cfg = uq.QuoterConfig(max_filled_games=2)
    cands = [cand("a"), cand("b"), cand("c")]
    assert uq.choose(cands, {"a"}, {"a", "b"}, cfg) == ["a", "b"]
    assert uq.choose(cands, {"a"}, {"a"}, cfg) == ["a", "b", "c"]


# ------------------------------------------------------------------ what to send and what to cancel
def test_reconcile_keeps_an_order_that_is_still_right_and_replaces_the_rest():
    cfg = uq.QuoterConfig()
    want = [uq.Want("m", "bid", uq.BUY_YES, 0.45, 100.0, T0 + 180), uq.Want("m", "ask", uq.BUY_NO, 0.47, 100.0, T0 + 180)]
    good = uq.Order("1", "m", "bid", uq.BUY_YES, 0.45, 100.0, T0 + 150)
    old = uq.Order("2", "m", "ask", uq.BUY_NO, 0.47, 100.0, T0 + 60)             # too little life left
    cancel, send = uq.reconcile(want, [good, old], T0, cfg)
    assert cancel == [old] and send == [want[1]]
    moved = uq.Order("3", "m", "bid", uq.BUY_YES, 0.44, 100.0, T0 + 150)         # the price has moved away from it
    partly = uq.Order("4", "m", "ask", uq.BUY_NO, 0.47, 70.0, T0 + 150)          # part filled: the size no longer matches
    stray = uq.Order("5", "other", "bid", uq.BUY_YES, 0.30, 100.0, T0 + 150)     # in a game we no longer want
    cancel, send = uq.reconcile(want, [moved, partly, stray], T0, cfg)
    assert cancel == [moved, partly, stray] and send == want
    assert uq.reconcile([], [good], T0, cfg) == ([good], [])


# ------------------------------------------------------------------ the paper broker
def test_paper_orders_are_filled_from_what_the_book_did():
    b = uq.PaperBroker()
    b.place([uq.Want("m", "ask", uq.SELL_YES, 0.47, 60.0, T0 + 180), uq.Want("m", "ask", uq.BUY_NO, 0.47, 40.0, T0 + 180), uq.Want("m", "bid", uq.BUY_YES, 0.45, 40.0, T0 + 180)])
    b.pos["m"] = uq.Position(bought=60, cost=27.0)
    prev = rw.read_book(book([(0.45, 100.0)], [(0.47, 100.0)], vol=10.0, notional=4.6))
    cur = rw.read_book(book([(0.45, 100.0)], [(0.47, 30.0)], vol=80.0, notional=4.6 + 70 * 0.47, last=0.47, last_t="2026-11-12T15:00:20Z"))
    fills = b.trade("m", prev, cur, T0)
    assert [(f["intent"], f["qty"]) for f in fills] == [(uq.SELL_YES, 60.0), (uq.BUY_NO, 10.0)]          # the closing order is filled first
    assert b.pos["m"].sold == 70 and b.pos["m"].proceeds == pytest.approx(70 * 0.47) and b.pos["m"].net == -10
    left = {o.intent: o.qty for o in b.open_orders(["m"])}
    assert left == {uq.BUY_NO: 30.0, uq.BUY_YES: 40.0}
    assert b.trade("m", cur, cur, T0 + 30) == []                                                         # nothing traded: nothing filled


def test_paper_orders_lapse_and_positions_settle():
    b = uq.PaperBroker()
    b.place([uq.Want("m", "bid", uq.BUY_YES, 0.45, 100.0, T0 + 180)])
    b.expire(T0 + 179)
    assert len(b.orders) == 1
    b.expire(T0 + 180)
    assert b.orders == {}
    b.pos["m"] = uq.Position(bought=100, cost=45.0)
    assert b.equity({"m": 0.50}) == pytest.approx(5.0) and b.equity({}) == pytest.approx(5.0)
    row = b.settle("m", 1.0)
    assert row["pnl"] == pytest.approx(55.0) and b.cash == pytest.approx(55.0) and b.pos == {}


# ------------------------------------------------------------------ the engine
class FakeUS:
    def __init__(self, schedule, books):
        self.schedule, self.books, self.fail, self.settled, self.asked = schedule, books, set(), {}, []

    def iter_incentives(self, statuses="active"):
        return iter(self.schedule)

    def book(self, slug):
        self.asked.append(slug)
        if slug in self.fail:
            raise RuntimeError("gateway down")
        return self.books[slug]

    def settlement(self, slug):
        return self.settled.get(slug)


def engine(tmp_path, us, **settings):
    clock = {"t": T0}
    e = uq.Engine(tmp_path, uq.QuoterConfig(**settings), uq.PaperBroker(), us, now=lambda: clock["t"])
    return e, clock


A, B = "aec-itfme-a-b-2026-11-12", "aec-utr-c-d-2026-11-12"


def test_engine_rests_in_a_game_credits_the_formula_and_renews_its_orders(tmp_path):
    us = FakeUS([entry(A)], {A: QUIET})
    e, clock = engine(tmp_path, us)
    line = e.step()
    assert line["games"] == 1 and line["placed"] == 2 and line["cancelled"] == 0 and e.reward() == 0.0
    orders = e.broker.open_orders([A])
    assert sorted((o.side, o.price, o.qty) for o in orders) == [("ask", 0.47, 100.0), ("bid", 0.45, 100.0)]
    clock["t"] += 30
    line = e.step()
    assert line["placed"] == 0 and line["cancelled"] == 0                                    # the same orders still stand
    assert e.reward() == pytest.approx(12.0 * (0.5 + 0.25) * 30 / (2 * rw.WINDOW))           # thirty seconds at a half and a quarter of the score
    clock["t"] += 90
    line = e.step()
    assert line["placed"] == 2 and line["cancelled"] == 2                                    # under ninety seconds of life left: sent again
    assert {o.expires for o in e.broker.open_orders([A])} == {clock["t"] + 180}
    assert line["renewed"] == 2
    actions = list(csv.DictReader((tmp_path / "actions.csv").open()))
    assert [a["action"] for a in actions] == ["place", "place"]                              # sending an order again unchanged is counted, not listed
    assert len(list(csv.DictReader((tmp_path / "cycles.csv").open()))) == 1                  # and a line is kept for one cycle in ten
    assert json.loads((tmp_path / "accrued.json").read_text())[A]["2026-11-12"] == pytest.approx(e.reward())


def test_engine_only_rests_in_its_programmes_and_in_books_it_can_read(tmp_path):
    us = FakeUS([entry(A), entry(B, program="utr_moneyline_day_of_1"), entry("aec-atp-e-f-2026-11-12", program="atp_wta_moneyline_day_of_1")],
                {A: QUIET, B: QUIET, "aec-atp-e-f-2026-11-12": QUIET})
    e, clock = engine(tmp_path, us)
    assert e.step()["games"] == 2 and "aec-atp-e-f-2026-11-12" not in us.asked               # the main tours are not in the list
    us.fail.add(B)
    clock["t"] += 30
    line = e.step()
    assert line["games"] == 1 and line["cancelled"] == 2                                     # B cannot be read: its orders come out
    assert {o.slug for o in e.broker.open_orders([A, B])} == {A}


def test_engine_fills_on_paper_then_stops_offering_that_side_and_settles(tmp_path):
    us = FakeUS([entry(A)], {A: book([(0.45, 100.0), (0.01, 2000.0)], [(0.47, 300.0), (0.99, 2000.0)], vol=0.0, notional=0.0)})
    e, clock = engine(tmp_path, us)
    e.step()
    clock["t"] += 30
    # sixty contracts are sold into the bid, and the book steps down
    us.books[A] = book([(0.44, 100.0), (0.01, 2000.0)], [(0.46, 300.0), (0.99, 2000.0)], vol=60.0, notional=27.0, last=0.45, last_t="2026-11-12T15:00:10Z")
    line = e.step()
    pos = e.broker.positions()[A]
    assert pos.bought == 60 and pos.cost == pytest.approx(27.0) and line["filled_games"] == 1 and line["at_risk"] == pytest.approx(27.0)
    have = sorted((o.side, o.intent, o.price, o.qty) for o in e.broker.open_orders([A]))
    assert have == [("ask", uq.BUY_NO, 0.46, 40.0), ("ask", uq.SELL_YES, 0.46, 60.0), ("bid", uq.BUY_YES, 0.44, 40.0)]
    assert [a["action"] for a in csv.DictReader((tmp_path / "actions.csv").open())].count("fill") == 1
    # the game is played and "Yes" wins: three hours after the start the paper position is closed at a dollar
    us.settled[A] = 1.0
    clock["t"] = START + uq.SETTLE_AFTER + 1
    e.step()
    assert e.broker.positions() == {} and e.broker.cash == pytest.approx(60 * (1.0 - 0.45))
    assert float(list(csv.DictReader((tmp_path / "settled.csv").open()))[0]["pnl"]) == pytest.approx(33.0)


def test_engine_keeps_what_could_be_lost_under_the_limit(tmp_path):
    slugs = [f"aec-itfme-p{i}-q{i}-2026-11-12" for i in range(6)]
    us = FakeUS([entry(s) for s in slugs], {s: QUIET for s in slugs})
    e, _ = engine(tmp_path, us, max_at_risk=120.0)                                           # each game can cost $53 on its worse side
    line = e.step()
    assert line["games"] == 2 and line["placed"] == 4


def test_engine_stops_on_the_stop_file_and_at_the_day_loss_limit(tmp_path):
    us = FakeUS([entry(A)], {A: QUIET})
    e, clock = engine(tmp_path, us, max_day_loss=20.0)
    e.step()
    (tmp_path / "STOP").write_text("")
    assert "STOP" in e.step()["stopped"] and e.broker.open_orders([A]) == []
    (tmp_path / "STOP").unlink()
    clock["t"] += 30
    e.step()                                                                                 # the day starts level
    e.broker.pos[A] = uq.Position(bought=100, cost=70.0)                                     # bought at 70c, and the book says 46c
    clock["t"] += 30
    out = e.step()
    assert "since midnight" in out["stopped"] and e.broker.open_orders([A]) == []


def test_run_always_pulls_the_orders_when_it_ends(tmp_path):
    us = FakeUS([entry(A)], {A: QUIET})
    e, clock = engine(tmp_path, us)
    e.run(minutes=2, sleep=lambda s: clock.__setitem__("t", clock["t"] + s))
    assert e.broker.open_orders([A]) == []
    actions = [a["action"] for a in csv.DictReader((tmp_path / "actions.csv").open())]
    assert actions[:2] == ["place", "place"] and actions[-1] == "stop"
    assert "On paper" in (tmp_path / "STATUS.md").read_text()


def test_engine_reads_every_book_once_then_a_share_of_the_others_each_cycle(tmp_path):
    slugs = [f"aec-itfme-p{i}-q{i}-2026-11-12" for i in range(30)]
    us = FakeUS([entry(s) for s in slugs], {s: QUIET for s in slugs})
    e, clock = engine(tmp_path, us, max_games=5)
    e.step()
    assert len(us.asked) == 30 and len(e.resting) == 5                    # the first cycle looks at everything
    us.asked.clear()
    clock["t"] += 30
    e.step()
    assert len(us.asked) == 5 + 3 and set(e.resting) <= set(us.asked)     # then the five it rests in, and a tenth of the other 25, rounded up
    seen = set(us.asked)
    for _ in range(9):
        us.asked.clear()
        clock["t"] += 30
        e.step()
        seen |= set(us.asked)
    assert seen == set(slugs)                                             # within five minutes every candidate has been read again


class AccountBroker(uq.PaperBroker):
    """A stand-in for a real account: its open orders show in the books that are read, as they would on the exchange."""

    def equity(self, marks):
        return None


def test_with_a_real_account_the_engine_does_not_anchor_on_its_own_order(tmp_path):
    us = FakeUS([entry(A)], {A: QUIET})
    clock = {"t": T0}
    e = uq.Engine(tmp_path, uq.QuoterConfig(), AccountBroker(), us, mode="live", now=lambda: clock["t"])
    e.step()
    assert sorted((o.side, o.price) for o in e.broker.open_orders([A])) == [("ask", 0.47), ("bid", 0.45)]
    # everyone else leaves 45c and now bids 43c. In the book as the exchange shows it, our own 100 contracts are still at 45c, alone.
    us.books[A] = book([(0.45, 100.0), (0.43, 300.0), (0.01, 2000.0)], [(0.47, 400.0), (0.99, 2000.0)])
    clock["t"] += 30
    e.step()
    assert sorted((o.side, o.price, o.qty) for o in e.broker.open_orders([A])) == [("ask", 0.47, 100.0), ("bid", 0.43, 100.0)]
    # and the reward it credits itself is its share of other people's score plus its own, not counting its order twice
    us.books[A] = book([(0.43, 400.0), (0.01, 2000.0)], [(0.47, 400.0), (0.99, 2000.0)])       # 300 of theirs and 100 of ours on each side
    before = e.reward()
    clock["t"] += 30
    e.step()
    assert e.reward() - before == pytest.approx(12.0 * (0.25 + 0.25) * 30 / (2 * rw.WINDOW))
