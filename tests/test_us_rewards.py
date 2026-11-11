"""The paper account that rests small orders before games on Polymarket US (docs/09)."""

from __future__ import annotations

import csv
import gzip

import pytest

from kht.trading import us_rewards as rw


def px(v: float) -> dict:
    return {"value": f"{v:.4f}", "currency": "USD"}


def book(bids, asks, vol=0.0, notional=0.0, last=None, last_t=None, low=None, low_t=None, high=None, high_t=None) -> dict:
    stats = {"sharesTraded": f"{vol:.4f}", "notionalTraded": px(notional)}
    for key, value, when in (("lastTradePx", last, last_t), ("lowPx", low, low_t), ("highPx", high, high_t)):
        if value is not None:
            stats[key] = px(value)
            stats[key.replace("Px", "SetTime").replace("lastTrade", "lastTrade")] = when
    return {"bids": [{"px": px(p), "qty": str(q)} for p, q in bids], "offers": [{"px": px(p), "qty": str(q)} for p, q in asks],
            "state": "MARKET_STATE_OPEN", "stats": stats}


def entry(slug, program="itf_moneyline_dayof_1", start="2026-11-12 18:00:00+00", pool=12, target=1000, discount=0.5, max_spread=None,
          period="day_of", product="aec", state="INSTRUMENT_STATE_OPEN") -> dict:
    tp = {"programId": program, "programType": "liquidityProgram", "rewardPool": pool, "status": "active", "discountFactor": discount, "targetSize": target,
          "period": period}
    if max_spread is not None:
        tp["maxSpread"] = max_spread
    return {"marketSlug": slug, "timePeriods": [tp], "instrumentState": state, "category": "SPR", "eventStartTime": start, "instrumentProduct": product}


GAME = {"slug": "aec-itfme-a-b-2026-11-12", "program": "itf", "pool": 12.0, "target": 1000.0, "discount": 0.5, "max_spread": None,
        "start": 1_000_000.0, "markets_in_event": 1}


def test_when_reads_both_spellings():
    assert rw._when("2026-11-12 17:00:00+00") == rw._when("2026-11-12T17:00:00Z")
    assert rw._when("2026-11-11T08:42:30.788839011Z") == pytest.approx(rw._when("2026-11-11T08:42:30Z") + 0.788839, abs=1e-5)
    assert rw._when(None) is None and rw._when("soon") is None


def test_event_key_drops_the_product_and_what_follows_the_date():
    assert rw.event_key("tsc-setkamecz-barmil-marhjan-2026-11-11-st-3pt5") == "setkamecz-barmil-marhjan-2026-11-11"
    assert rw.event_key("aec-utr-abddan-liand-2026-11-10") == "utr-abddan-liand-2026-11-10"


def test_games_keeps_two_way_winner_markets_in_day_of_programmes():
    sched = [
        entry("aec-itfme-a-b-2026-11-12"),
        entry("aec-setka-c-d-2026-11-12", program="table_tennis_moneyline_day_of_1", pool=5),
        entry("tsc-setka-c-d-2026-11-12-st-3pt5", program="table_tennis_moneyline_day_of_1", pool=5, product="tsc"),
        entry("tsc-setka-c-d-2026-11-12-st-4pt5", program="table_tennis_moneyline_day_of_1", pool=5, product="tsc"),
        entry("aec-itfme-e-f-2026-11-12", period="live", program="itf_ml_live_1"),            # not a day-of period
        entry("asc-nfl-g-h-2026-11-12-3pt5", program="nfl_spreads_day_of_1", product="asc"),   # not on who wins
        entry("aec-itfme-i-j-2026-11-12", state="INSTRUMENT_STATE_CLOSED"),
        {**entry("aec-pol-k-l-2026-11-12"), "category": "POL"},
    ]
    g = rw.games(sched)
    assert set(g) == {"aec-itfme-a-b-2026-11-12", "aec-setka-c-d-2026-11-12"}
    assert g["aec-itfme-a-b-2026-11-12"]["markets_in_event"] == 1
    assert g["aec-setka-c-d-2026-11-12"]["markets_in_event"] == 3          # the pool is shared with the two totals
    assert g["aec-itfme-a-b-2026-11-12"]["start"] == rw._when("2026-11-12T18:00:00Z")


def test_infer_tick():
    assert rw.infer_tick([0.45, 0.46, 0.99]) == 0.01
    assert rw.infer_tick([0.455, 0.46]) == 0.005
    assert rw.infer_tick([0.451, 0.46]) == 0.001


def test_quote_level_skips_dust_and_refuses_a_far_price():
    assert rw.quote_level([(0.69, 0.09), (0.70, 985.0)], 0.01) == 0.70          # a tenth of a contract is not a price
    assert rw.quote_level([(0.45, 30.0), (0.44, 100.0)], 0.01) == 0.45
    assert rw.quote_level([(0.45, 5.0), (0.44, 5.0), (0.43, 10.0)], 0.01) == 0.43  # adds up by the third level
    assert rw.quote_level([(0.45, 1.0), (0.30, 500.0)], 0.01) is None           # real size is 15 ticks away
    assert rw.quote_level([], 0.01) is None


def test_side_with_order_scores_as_documented():
    # 1,000 at the best and 1,000 one tick away, discount 0.30: the documented example, then ours added at the best
    levels = [(0.50, 1000.0), (0.49, 1000.0)]
    at, share = rw.side_with_order(levels, 0.50, 1000.0, 2000.0, 0.30, 0.01)
    assert at == 0.50 and share == pytest.approx(0.5)                 # the target is now met at the best price, and half of it is ours
    at, share = rw.side_with_order(levels, 0.49, 1000.0, 3000.0, 0.30, 0.01)
    assert at == 0.49 and share == pytest.approx(300.0 / (1000.0 + 600.0))
    at, share = rw.side_with_order(levels, 0.50, 100.0, 5000.0, 0.30, 0.01)
    assert at is None                                                 # the side never reaches the target: not paid


def test_quote_state_shares_and_the_maximum_spread():
    b = rw.read_book(book([(0.45, 100.0), (0.01, 2000.0)], [(0.47, 300.0), (0.99, 2000.0)]))
    q = rw.quote_state(b, GAME)
    assert q["quoting"] and q["bid_px"] == 0.45 and q["ask_px"] == 0.47
    assert q["share"][100] == pytest.approx((100.0 / 200.0, 100.0 / 400.0))
    assert q["alone"] == (True, True)
    # with a maximum spread the far orders no longer make the book qualify, and nobody is paid
    q = rw.quote_state(b, {**GAME, "max_spread": 0.05})
    assert q["quoting"] and q["share"][100] == (0.0, 0.0) and q["alone"] == (False, False)
    # unless our own orders carry both sides to the target within the spread
    q = rw.quote_state(b, {**GAME, "max_spread": 0.05, "target": 250.0})
    assert q["share"][100] == (0.0, 0.0)
    assert q["share"][250][0] == pytest.approx(250.0 / 350.0) and q["share"][250][1] == pytest.approx(250.0 / 550.0)


def test_quote_state_does_not_quote_a_wide_or_empty_book():
    wide = rw.read_book(book([(0.30, 100.0)], [(0.60, 100.0)]))
    assert not rw.quote_state(wide, GAME)["quoting"]
    one_sided = rw.read_book(book([(0.30, 100.0)], []))
    q = rw.quote_state(one_sided, GAME)
    assert not q["quoting"] and q["mid"] is None


def test_hits_by_trade_and_by_crossing():
    q = {"bid_px": 0.45, "ask_px": 0.47}
    prev = rw.read_book(book([(0.45, 100.0)], [(0.47, 100.0)], vol=10.0, notional=4.6))
    # 30 contracts traded at 45c: the bid was hit
    cur = rw.read_book(book([(0.45, 70.0)], [(0.47, 100.0)], vol=40.0, notional=4.6 + 30 * 0.45, last=0.45, last_t="2026-11-12T12:00:05Z"))
    h = rw.hits(prev, q, cur, rw._when("2026-11-12T12:00:00Z"))
    assert [(x["side"], x["dv"], x["crossed"]) for x in h] == [("bid", 30.0, 0)]
    # 30 contracts traded at 47c: the offer was hit
    cur = rw.read_book(book([(0.45, 100.0)], [(0.47, 70.0)], vol=40.0, notional=4.6 + 30 * 0.47, last=0.47, last_t="2026-11-12T12:00:05Z"))
    assert [x["side"] for x in rw.hits(prev, q, cur, rw._when("2026-11-12T12:00:00Z"))] == ["ask"]
    # nothing traded: no hit
    assert rw.hits(prev, q, prev, 0.0) == []
    # an old last trade at our price does not count when the volume came from somewhere in between
    cur = rw.read_book(book([(0.45, 100.0)], [(0.47, 100.0)], vol=11.0, notional=4.6 + 0.46, last=0.45, last_t="2026-11-12T11:00:00Z"))
    assert rw.hits(prev, q, cur, rw._when("2026-11-12T12:00:00Z")) == []
    # the offers have moved down through our bid without a trade: they would have traded against us
    cur = rw.read_book(book([(0.40, 100.0)], [(0.44, 60.0), (0.46, 100.0)], vol=10.0, notional=4.6))
    h = rw.hits(prev, q, cur, 0.0)
    assert [(x["side"], x["crossed"], x["cross_qty"]) for x in h] == [("bid", 1, 60.0)]
    # the running total started again: what it shows is what traded
    cur = rw.read_book(book([(0.45, 100.0)], [(0.47, 100.0)], vol=5.0, notional=5 * 0.45, low=0.45, low_t="2026-11-12T12:00:05Z"))
    h = rw.hits(prev, q, cur, rw._when("2026-11-12T12:00:00Z"))
    assert [(x["side"], x["dv"]) for x in h] == [("bid", 5.0)]


def test_follower_accrues_only_inside_the_window_and_before_the_pull():
    start = rw._when("2026-11-12T18:00:00Z")
    f = rw.Follower({**GAME, "start": start})
    b = book([(0.45, 100.0), (0.01, 2000.0)], [(0.47, 300.0), (0.99, 2000.0)])
    f.see(start - 3600, b)
    f.see(start - 3480, b)                       # two minutes, both sides paid
    day = f.days["2026-11-12"]
    assert day["obs_s"] == pytest.approx(120.0) and day["quote_s"] == pytest.approx(120.0)
    assert day["acc_bid_100"] == pytest.approx(120.0 * 0.5) and day["acc_ask_100"] == pytest.approx(120.0 * 0.25)
    assert day["cap_s"] == pytest.approx(120.0 * (0.45 + 0.53))
    f.see(start - 3480 + 2000, b)                # a gap too long to join up: not counted
    assert day["obs_s"] == pytest.approx(120.0)
    f.see(start - 660, b)
    f.see(start - 540, b)                        # straddles the pull, ten minutes before the start: only a minute counts
    assert day["obs_s"] == pytest.approx(120.0 + (3480 - 2000 - 660) + 60.0)
    assert f.done and f.quoted
    rows = f.rows("r1")
    assert len(rows) == 1 and rows[0]["date"] == "2026-11-12" and rows[0]["polls"] == 5 and rows[0]["mid_last"] == pytest.approx(0.46)


def test_follower_splits_a_window_across_two_us_dates():
    start = rw._when("2026-11-12T06:00:00Z")     # 1am Eastern: the window starts on the 11th there
    f = rw.Follower({**GAME, "start": start})
    b = book([(0.45, 100.0), (0.01, 2000.0)], [(0.47, 300.0), (0.99, 2000.0)])
    f.see(start - 3 * 3600, b)                   # 10pm Eastern on the 11th
    f.see(start - 3 * 3600 + 120, b)
    f.see(start - 3000, b)                       # 12:10am Eastern on the 12th
    f.see(start - 2880, b)
    assert set(f.days) == {"2026-11-11", "2026-11-12"}
    assert f.days["2026-11-12"]["obs_s"] == pytest.approx(120.0)


def test_follower_records_a_hit_with_its_prices():
    start = rw._when("2026-11-12T18:00:00Z")
    f = rw.Follower({**GAME, "start": start})
    f.see(start - 3600, book([(0.45, 100.0)], [(0.47, 100.0)], vol=0.0, notional=0.0))
    f.see(start - 3480, book([(0.44, 100.0)], [(0.46, 100.0)], vol=40.0, notional=18.0, last=0.45, last_t="2026-11-12T17:01:00Z"))
    assert len(f.hits) == 1
    h = f.hits[0]
    assert (h["side"], h["px"], h["dv"], h["mid0"], h["mid1"]) == ("bid", 0.45, 40.0, pytest.approx(0.46), pytest.approx(0.45))


class FakeUS:
    def __init__(self, schedule, books):
        self.schedule, self.books, self.asked = schedule, books, []

    def iter_incentives(self, statuses="active"):
        return iter(self.schedule)

    def book(self, slug):
        self.asked.append(slug)
        if slug == "aec-itfme-broken-x-2026-11-12":
            raise RuntimeError("gateway down")
        return self.books[slug]


def test_run_follows_games_in_their_window_and_writes_files(tmp_path):
    clock = {"t": rw._when("2026-11-12T15:00:00Z")}
    sched = [entry("aec-itfme-a-b-2026-11-12", start="2026-11-12 18:00:00+00"),           # three hours ahead: followed
             entry("aec-itfme-c-d-2026-11-13", start="2026-11-13 09:00:00+00"),           # eighteen hours ahead: not yet
             entry("aec-itfme-e-f-2026-11-12", start="2026-11-12 15:05:00+00"),           # inside the last ten minutes: too late
             entry("aec-itfme-broken-x-2026-11-12", start="2026-11-12 18:00:00+00")]
    b = book([(0.45, 100.0), (0.01, 2000.0)], [(0.47, 300.0), (0.99, 2000.0)])
    us = FakeUS(sched, {"aec-itfme-a-b-2026-11-12": b})
    line = rw.run(tmp_path, minutes=7, us=us, interval=120.0, now=lambda: clock["t"], sleep=lambda s: clock.__setitem__("t", clock["t"] + s))
    assert set(us.asked) == {"aec-itfme-a-b-2026-11-12", "aec-itfme-broken-x-2026-11-12"}
    assert line["cycles"] == 4 and line["books"] == 4 and line["errors"] == 4 and line["games"] == 2 and line["games_quoted"] == 1 and line["hits"] == 0
    out = tmp_path / "runs" / line["run"]
    with gzip.open(out / "games.csv.gz", "rt", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert [r["slug"] for r in rows] == ["aec-itfme-a-b-2026-11-12"]
    assert float(rows[0]["obs_s"]) == pytest.approx(360.0) and float(rows[0]["acc_bid_100"]) == pytest.approx(180.0)
    assert (out / "hits.csv").read_text().strip() == ",".join(rw.HIT_FIELDS)
    assert (tmp_path / "log.csv").read_text().count("\n") == 2
    status = (tmp_path / "STATUS.md").read_text()
    assert "itf_moneyline_dayof_1" in status and "No orders are placed" in status
    # the reward the status reports: 360 seconds of a 6-hour window, $12 a game, shares of a half and a quarter
    assert f"${12 * (180 + 90) / (2 * 21600):,.2f}" in status
