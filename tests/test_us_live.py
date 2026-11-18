"""Test D1: the recorder of UTR matches around their start (src/kht/trading/us_live.py) and its scorer (scripts/us_delay_score.py)."""

from __future__ import annotations

import csv
import gzip
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from kht.trading import us_live as live

spec = importlib.util.spec_from_file_location("us_delay_score", Path(__file__).resolve().parents[1] / "scripts" / "us_delay_score.py")
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)

T0 = datetime(2026, 11, 20, 15, 0, tzinfo=timezone.utc).timestamp()      # a listed start on 20 November 2026
MATCH, MARKET = "utr-aaa-bbb-2026-11-20", "aec-utr-aaa-bbb-2026-11-20"
TERMS = {"dayof_pool": 10.0, "dayof_target": 250.0, "dayof_discount": 0.35, "dayof_max_spread": 0.07,
         "live_pool": 50.0, "live_target": 500.0, "live_discount": 0.3, "live_max_spread": 0.06, "start_first": T0}


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def reading(ts, bids="0.39:1;0.01:650", asks="0.4:1;0.99:650", period="NS", live_now=0, score_now="0-0", state="OPEN", traded=0.0, notional=0.0, last=None, last_t=None,
            start=T0):
    return {"ts": ts, "slug": MARKET, "state": state, "bids": bids, "asks": asks, "traded": traded, "notional": notional, "last": last, "last_t": last_t,
            "low": None, "low_t": None, "high": None, "high_t": None, "start": start, "live": live_now, "period": period, "score": score_now}


def span(first, last, step=30.0, **kw):
    out, t = [], first
    while t <= last:
        out.append(reading(t, **kw))
        t += step
    return out


def a_match(wait=3600.0, play=5400.0, **kw):
    """Followed from a quarter of an hour before the listed start; starts ``wait`` seconds late; closes ``play`` seconds after that."""
    rows = span(T0 - 900.0, T0 + wait - 30.0, **kw)
    rows += span(T0 + wait, T0 + wait + play - 30.0, period="S1", live_now=1, score_now="1-0:0-15", bids="0.39:400;0.38:500", asks="0.4:400;0.41:500")
    rows += span(T0 + wait + play, T0 + wait + play + 120.0, state="CLOSED", period="FT", live_now=0, score_now="6-4, 6-4", bids="", asks="")
    return rows


def test_the_listing_is_taken_at_its_word_and_no_word_means_no_orders():
    assert score.waiting({"period": "NS", "live": 0, "score": "0-0"}) and not score.playing({"period": "NS", "live": 0, "score": "0-0"})
    assert score.playing({"period": "S1", "live": 1, "score": "0-0:15-0"}) and not score.waiting({"period": "S1", "live": 1, "score": "0-0:15-0"})
    assert score.playing({"period": "SUS", "live": 0, "score": "3-6, 3-2"})                # suspended is not "not started"
    assert not score.waiting({"period": "NS", "live": 0, "score": "0-0:15-0"})             # a point has been played, whatever the period says
    for nothing in ({"period": "", "live": "", "score": ""}, {"period": float("nan"), "live": float("nan"), "score": float("nan")}):
        assert not score.waiting(nothing) and not score.playing(nothing)


def test_the_orders_stand_five_cents_either_side_of_the_middle():
    q = score.quotes([(0.39, 1.0)], [(0.40, 1.0)], 0.0)
    assert (q["bid_px"], q["ask_px"], q["bid_qty"], q["ask_qty"]) == (0.34, 0.45, 500.0, 500.0)
    q = score.quotes([(0.39, 1.0)], [(0.41, 1.0)], 0.0)
    assert (q["bid_px"], q["ask_px"]) == (0.35, 0.45)
    assert score.quotes([(0.39, 1.0)], [(0.45, 1.0)], 0.0)["bid_px"] is None               # no middle to stand around
    assert score.quotes([], [(0.45, 1.0)], 0.0)["why"] == "one side is empty"
    assert score.quotes([(0.03, 1.0)], [(0.04, 1.0)], 0.0)["bid_px"] is None               # five cents below would be under a cent
    q = score.quotes([(0.39, 1.0)], [(0.40, 1.0)], 200.0)                                   # 200 held: the bid is cut, the offer is not
    assert (q["bid_qty"], q["ask_qty"]) == (300.0, 500.0)


def test_an_hour_of_waiting_is_paid_both_ways_and_nothing_rests_once_play_shows():
    rows = a_match(wait=3600.0, play=5400.0)
    s = score.simulate(rows, TERMS, 500.0)
    assert s["fills"] == 0 and s["pos"] == 0
    assert s["wait_s"] == pytest.approx(3600.0) and s["rest_s"] == pytest.approx(3600.0)
    assert s["listed"] == T0 and s["started"] == T0 + 3600.0 and s["closed"] == T0 + 3600.0 + 5400.0
    r = next(x for x in score.match_rows(MARKET, rows, TERMS, 1.0) if x["size"] == 500.0)
    assert r["whole"] and r["wait_min"] == pytest.approx(60.0)
    # as the six hours before the start: ten dollars over six hours, times our share of the score in that hour
    assert r["reward_before"] == pytest.approx(10.0 * 3600.0 * r["share_before"] / 21_600.0)
    # as play from the listed start: fifty dollars over the two and a half hours from the listed start to the close
    assert r["reward_live"] == pytest.approx(50.0 * 3600.0 * r["share_live"] / (3600.0 + 5400.0), rel=1e-3)
    assert 0.3 < r["share_live"] < 0.9 and 0.3 < r["share_before"] < 0.95                  # the single contracts at the best prices keep part of the score
    assert r["net_before"] == pytest.approx(r["reward_before"]) and r["net_live"] == pytest.approx(r["reward_live"])


def test_the_orders_stay_while_the_listed_start_is_moved_forward_a_little_at_a_time():
    """While a match waits the exchange moves its listed start on, ten or twenty minutes at a time. The orders stay through that."""
    rows = span(T0 - 900.0, T0 - 30.0)                                        # before the first listed start: nothing rests
    rows += span(T0, T0 + 570.0)                                              # past it
    rows += span(T0 + 600.0, T0 + 1170.0, start=T0 + 1200.0)                  # the start has been moved twenty minutes on
    rows += span(T0 + 1200.0, T0 + 1470.0, start=T0 + 1200.0)                 # past that one too
    rows += span(T0 + 1500.0, T0 + 1770.0, start=T0 + 2100.0)                 # and moved again
    rows += span(T0 + 1800.0, T0 + 5370.0, start=T0 + 1790.0, period="S1", live_now=1, score_now="0-0:15-0", bids="0.39:400", asks="0.4:400")
    rows += span(T0 + 5400.0, T0 + 5520.0, state="CLOSED", period="FT", live_now=0, score_now="6-4, 6-4", bids="", asks="")
    s = score.simulate(rows, TERMS, 500.0)
    assert s["listed"] == T0 and s["started"] == T0 + 1800.0
    assert s["wait_s"] == pytest.approx(1800.0) and s["rest_s"] == pytest.approx(1800.0)       # half an hour, without a break
    r = next(x for x in score.match_rows(MARKET, rows, TERMS, 1.0) if x["size"] == 500.0)
    assert r["whole"]
    assert r["reward_before"] == pytest.approx(10.0 * 1800.0 * r["share_before"] / 21_600.0)
    # counted as play only for the fifteen minutes past a listed start as it then stood; the other fifteen as the six hours before
    past, ahead = 900.0, 900.0
    assert r["past_min"] == pytest.approx(15.0)
    assert r["reward_live"] == pytest.approx(50.0 * past * r["share_live"] / 5400.0 + 10.0 * ahead * r["share_before"] / 21_600.0, rel=1e-3)


def test_nothing_rests_while_a_match_is_put_off_by_more_than_half_an_hour():
    rows = span(T0 - 900.0, T0 + 570.0)                                       # ten minutes past the listed start,
    rows += span(T0 + 600.0, T0 + 7170.0, start=T0 + 7200.0)                  # then put off by two hours
    rows += span(T0 + 7200.0, T0 + 7290.0, start=T0 + 7200.0)
    rows += span(T0 + 7320.0, T0 + 9000.0, start=T0 + 7300.0, period="S1", live_now=1, score_now="0-0:15-0", bids="0.39:400", asks="0.4:400")
    s = score.simulate(rows, TERMS, 500.0)
    # ten minutes at first; then nothing until half an hour before the new start; then thirty minutes and the two past it
    assert s["rest_s"] == pytest.approx(600.0 + 1800.0 + 120.0)


def test_before_the_first_listed_start_has_passed_nothing_rests_however_near_it_is():
    rows = span(T0 - 900.0, T0 - 30.0)
    rows += span(T0, T0 + 600.0, period="S1", live_now=1, score_now="0-0:15-0", bids="0.39:400", asks="0.4:400")
    assert score.simulate(rows, TERMS, 500.0)["rest_s"] == 0.0


def test_250_a_side_cannot_be_paid_as_play():
    r = next(x for x in score.match_rows(MARKET, a_match(), TERMS, 1.0) if x["size"] == 250.0)
    assert r["reward_live"] == 0.0 and r["reward_before"] > 0.0


def test_a_fill_while_waiting_is_closed_when_play_shows_and_pays_the_fee():
    t = T0 + 600.0
    rows = span(T0 - 900.0, t)
    rows.append(reading(t + 30.0, traded=500.0, notional=170.0, last=0.34, last_t=t + 10.0))     # 500 contracts traded at our bid of 34c
    rows += span(t + 60.0, t + 300.0, traded=500.0, notional=170.0)
    rows += span(t + 330.0, t + 900.0, period="S1", live_now=1, score_now="0-1:0-0", bids="0.30:600", asks="0.32:600", traded=500.0, notional=170.0)
    rows += span(t + 930.0, t + 1050.0, state="CLOSED", period="FT", live_now=0, score_now="4-6, 2-6", bids="", asks="", traded=500.0, notional=170.0)
    s = score.simulate(rows, TERMS, 500.0)
    assert s["bought"] == 500.0 and s["pos"] == 0.0                                        # bought at 34c, sold at 30c when play showed
    assert s["cash"] == pytest.approx(500 * (0.30 - 0.34))
    assert s["fees"] == pytest.approx(500 * 0.095 * 0.30 * 0.70)
    r = next(x for x in score.match_rows(MARKET, rows, TERMS, 0.0) if x["size"] == 500.0)
    assert r["pnl_fills"] == pytest.approx(-20.0 - 9.975)


def test_a_price_that_jumps_as_play_begins_takes_the_order_that_was_still_resting():
    rows = span(T0 - 900.0, T0 + 570.0)
    rows += span(T0 + 600.0, T0 + 1200.0, period="S1", live_now=1, score_now="0-0:0-40", bids="0.47:400;0.46:500", asks="0.48:400")      # play shows with the price 8c higher
    rows += span(T0 + 1230.0, T0 + 1350.0, state="CLOSED", period="FT", live_now=0, score_now="6-0, 6-0", bids="", asks="")
    s = score.simulate(rows, TERMS, 500.0)
    assert s["sold"] == 500.0 and s["bought"] == 0.0                                       # our offer at 45c was taken by the bids that now stand above it
    assert s["pos"] == 0.0                                                                 # 400 bought back at 48c at once, the last 100 from the offers of the next reading
    r = next(x for x in score.match_rows(MARKET, rows, TERMS, 1.0) if x["size"] == 500.0)
    assert r["pnl_fills"] == pytest.approx(500 * (0.45 - 0.48) - 500 * 0.095 * 0.48 * 0.52)


def test_a_match_that_starts_on_time_counts_as_nothing_gained_and_nothing_lost():
    rows = span(T0 - 900.0, T0 - 30.0)
    rows += span(T0, T0 + 3600.0, period="S1", live_now=1, score_now="0-0:15-0", bids="0.45:400", asks="0.46:400")
    rows += span(T0 + 3630.0, T0 + 3750.0, state="CLOSED", period="FT", live_now=0, score_now="6-0, 6-0", bids="", asks="")
    r = next(x for x in score.match_rows(MARKET, rows, TERMS, 1.0) if x["size"] == 500.0)
    assert r["whole"] and r["wait_min"] == 0 and r["net_before"] == 0.0 and r["net_live"] == 0.0


def test_a_match_counts_only_if_followed_from_its_listed_start_and_listed_from_19_november():
    late = [r for r in a_match() if r["ts"] >= T0 + 600.0]
    assert not next(x for x in score.match_rows(MARKET, late, TERMS, 1.0) if x["size"] == 500.0)["whole"]
    early_day = score.COUNTED_FROM - 3600.0
    rows = [{**r, "ts": r["ts"] - T0 + early_day, "start": early_day} for r in a_match()]
    assert not next(x for x in score.match_rows(MARKET, rows, {**TERMS, "start_first": early_day}, 1.0) if x["size"] == 500.0)["whole"]
    thin = [r for i, r in enumerate(a_match()) if i % 2 == 0]
    assert not next(x for x in score.match_rows(MARKET, thin, TERMS, 1.0) if x["size"] == 500.0)["whole"]


def test_the_verdict_names_which_reading_of_the_rules_it_needs():
    def matches(n, dates, before, live_):
        return pd.DataFrame([{"size": 500.0, "whole": True, "day": f"2026-11-{20 + i % dates:02d}", "net_before": before[i % len(before)], "net_live": live_[i % len(live_)]}
                             for i in range(n)])

    assert score.verdict(matches(399, 10, [1.0, 2.0], [5.0, 6.0])).startswith("NOT YET JUDGED")
    assert score.verdict(matches(400, 9, [1.0, 2.0], [5.0, 6.0])).startswith("NOT YET JUDGED")
    assert score.verdict(matches(440, 10, [1.0, 2.0, 1.5], [5.0, 6.0, 7.0])).startswith("PASSES:")
    assert score.verdict(matches(440, 10, [-1.0, -2.0, -1.5], [5.0, 6.0, 7.0])).startswith("PASSES ONLY IF PLAY IS COUNTED FROM THE LISTED START")
    assert score.verdict(matches(440, 10, [-1.0, -2.0, -1.5], [-5.0, -6.0, 7.0])).startswith("DOES NOT PASS")


def level(px, qty):
    return {"px": {"value": str(px), "currency": "USD"}, "qty": str(qty)}


class Clock:
    def __init__(self, t):
        self.t = t

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


class FakeUS:
    """One UTR match that starts four minutes late and is over six minutes after its listed start; another tour's match beside it."""

    def __init__(self, clock):
        self.clock, self.books = clock, []

    def iter_incentives(self, statuses=None):
        periods = [{"programId": "utr_moneyline_day_of_20261008", "programType": "liquidityProgram", "status": "active", "rewardPool": 10, "targetSize": 250,
                    "discountFactor": 0.35, "maxSpread": 0.07, "period": "day_of"},
                   {"programId": "utr_moneyline_live_20261008", "programType": "liquidityProgram", "status": "active", "rewardPool": 50, "targetSize": 500,
                    "discountFactor": 0.3, "maxSpread": 0.06, "period": "live"}]
        return iter([{"marketSlug": MARKET, "timePeriods": periods}, {"marketSlug": "aec-itfme-ccc-ddd-2026-11-20", "timePeriods": periods}])

    def iter_events(self, max_pages=None, **filters):
        assert filters.get("tagSlug") == "tennis" and filters.get("closed") is False
        t = self.clock.t
        if t >= T0 + 360.0:
            return iter([])                                                 # over: no longer listed
        playing = t >= T0 + 240.0
        ev = {"slug": MATCH, "title": "A vs. B", "startTime": iso(T0), "live": playing, "period": "S1" if playing else "NS", "score": "0-0:15-0" if playing else "0-0",
              "ended": False, "eventState": {"updatedAt": iso(t)}, "markets": [{"slug": MARKET, "closed": False}]}
        other = {**ev, "slug": "itfme-ccc-ddd-2026-11-20", "markets": [{"slug": "aec-itfme-ccc-ddd-2026-11-20", "closed": False}]}
        return iter([ev, other])

    def book(self, slug):
        self.books.append(slug)
        state = "MARKET_STATE_OPEN" if self.clock.t < T0 + 360.0 else "MARKET_STATE_CLOSED"
        return {"bids": [level(0.39, 1)], "offers": [level(0.40, 1)], "state": state, "transactTime": "2026-11-20T15:00:00Z",
                "stats": {"sharesTraded": "0", "notionalTraded": {"value": "0", "currency": "USD"}, "openInterest": "0"}}


def test_the_recorder_follows_a_match_from_before_its_listed_start_until_its_market_has_closed(tmp_path):
    clock = Clock(T0 - 1200.0)                                              # twenty minutes before the listed start: not yet followed
    us = FakeUS(clock)
    line = live.run(tmp_path, minutes=40.0, us=us, now=clock.now, sleep=clock.sleep, background=False)
    assert line["errors"] == 0 and line["markets"] == 1 and set(us.books) == {MARKET}      # the other tour's match is left alone
    with gzip.open(next(tmp_path.glob("runs/*/books.csv.gz")), "rt") as fh:
        rows = list(csv.DictReader(fh))
    ts = [float(r["ts"]) for r in rows]
    assert min(ts) == pytest.approx(T0 - 900.0, abs=31.0)                                   # from a quarter of an hour before
    assert max(ts) == pytest.approx(T0 + 360.0 + 120.0, abs=31.0)                           # until two minutes after the market closed, and no longer
    waiting = [r for r in rows if r["period"] == "NS" and float(r["ts"]) >= T0]
    assert len(waiting) == 8 and all(r["live"] == "0" and r["score"] == "0-0" for r in waiting)
    assert [r["period"] for r in rows if T0 + 240.0 <= float(r["ts"]) < T0 + 360.0] == ["S1"] * 4
    assert all(r["period"] == "" and r["live"] == "" for r in rows if float(r["ts"]) >= T0 + 360.0)      # no longer listed: nothing is known
    m = list(csv.DictReader(next(tmp_path.glob("runs/*/markets.csv")).open()))
    assert len(m) == 1 and m[0]["event"] == MATCH and float(m[0]["live_pool"]) == 50.0 and float(m[0]["dayof_target"]) == 250.0 and float(m[0]["start_first"]) == T0
    assert "test D1" in (tmp_path / "STATUS.md").read_text()
    # and the scorer reads what the recorder wrote
    b, mk = score.top.load(tmp_path)
    out = score.match_rows(MARKET, b[b.slug == MARKET].to_dict("records"), mk.set_index("slug").to_dict("index")[MARKET], 1.0)
    r = next(x for x in out if x["size"] == 500.0)
    assert r["whole"] and r["wait_min"] == pytest.approx(4.0) and r["reward_before"] > 0 and r["reward_live"] > 0


def test_a_listing_that_cannot_be_read_stops_nothing_and_says_nothing(tmp_path):
    clock = Clock(T0 - 600.0)
    us = FakeUS(clock)
    real = us.iter_events
    calls = {"n": 0}

    def flaky(max_pages=None, **filters):
        calls["n"] += 1
        if calls["n"] in (3, 4):
            raise RuntimeError("gateway timeout")
        return real(max_pages=max_pages, **filters)

    us.iter_events = flaky
    line = live.run(tmp_path, minutes=5.0, us=us, now=clock.now, sleep=clock.sleep, background=False)
    assert line["errors"] == 2 and line["books"] == 10
    with gzip.open(next(tmp_path.glob("runs/*/books.csv.gz")), "rt") as fh:
        rows = list(csv.DictReader(fh))
    assert [r["period"] for r in rows][2:4] == ["", ""] and rows[4]["period"] == "NS"       # two readings with nothing known, then the listing is back


def test_a_match_whose_book_can_no_longer_be_read_is_let_go(tmp_path):
    clock = Clock(T0 - 600.0)
    us = FakeUS(clock)
    real = us.book

    def gone(slug):
        if clock.t >= T0 - 300.0:
            raise RuntimeError("404")
        return real(slug)

    us.book = gone
    line = live.run(tmp_path, minutes=30.0, us=us, now=clock.now, sleep=clock.sleep, background=False)
    assert line["books"] == 10 and line["errors"] == live.GIVE_UP          # ten readings, then twenty tries, then no more
