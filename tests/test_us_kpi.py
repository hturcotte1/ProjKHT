"""Test K1: the recorder run on the earnings markets, and its scorer (scripts/us_kpi_score.py)."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from kht.trading import top_rule as rule
from kht.trading import us_top as top

spec = importlib.util.spec_from_file_location("us_kpi_score", Path(__file__).resolve().parents[1] / "scripts" / "us_kpi_score.py")
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)

EPS_MARKET = "kpic-intu-q1eps-2026-11-19-above-2pt46"
REV_A, REV_B = "kpic-intu-q1oerev-2026-11-19-above-2pt35b", "kpic-intu-q1oerev-2026-11-19-above-2pt40b"
CUT_AFTER = datetime(2026, 11, 19, 20, 0, tzinfo=timezone.utc).timestamp()      # 15:00 US Eastern on the day of the report
CUT_BEFORE = datetime(2026, 11, 19, 5, 0, tzinfo=timezone.utc).timestamp()      # midnight US Eastern at the start of that day
LISTED = CUT_AFTER - 24 * 3600.0                                                 # 18 November 2026, 20:00 UTC: after the rule was fixed
TERMS = {"pool": 250.0, "target": 500.0, "discount": 0.5, "max_spread": 0.06, "reports": "after", "listed": LISTED}


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def reading(ts, bids="0.77:900", asks="0.78:900", traded=0.0, notional=0.0, state="OPEN", last=None, last_t=None):
    return {"ts": ts, "slug": EPS_MARKET, "state": state, "bids": bids, "asks": asks, "traded": traded, "notional": notional, "last": last, "last_t": last_t,
            "low": None, "low_t": None, "high": None, "high_t": None}


def quiet(start, end, step=30.0, **kw):
    out, t = [], start
    while t <= end:
        out.append(reading(t, **kw))
        t += step
    return out


def test_the_event_and_the_day_of_the_report_are_read_from_the_name():
    assert score.event_of(EPS_MARKET) == ("intu-q1eps-2026-11-19", "2026-11-19")
    assert score.event_of(REV_A)[0] == score.event_of(REV_B)[0] == "intu-q1oerev-2026-11-19"
    assert score.event_of("cpausp-gold-updown-1d-2026-11-18-2315z") is None


def test_events_count_from_six_in_the_evening_of_the_day_the_rule_was_fixed():
    assert score.COUNTED_FROM == datetime(2026, 11, 18, 18, 0, tzinfo=timezone.utc).timestamp()


def test_the_cut_off_is_three_in_the_afternoon_for_a_report_after_the_close_and_midnight_otherwise():
    assert score.cutoff("2026-11-19", "after") == CUT_AFTER
    assert score.cutoff("2026-11-19", "before") == CUT_BEFORE
    assert score.cutoff("2026-11-19", float("nan")) == CUT_BEFORE          # not said: the careful one
    # summer time: 15:00 Eastern is 19:00 UTC
    assert score.cutoff("2026-07-21", "after") == datetime(2026, 7, 21, 19, 0, tzinfo=timezone.utc).timestamp()


def test_a_quiet_hour_is_paid_its_share_of_the_day():
    rows = quiet(CUT_AFTER - 7200.0, CUT_AFTER - 3600.0)
    s = score.simulate(rows, TERMS, 100, CUT_AFTER)
    assert s["fills"] == 0 and s["pos"] == 0
    assert s["rest_s"] == pytest.approx(3600.0)
    share = 100.0 / 1000.0                                                 # 100 of ours beside 900 on each side
    assert sum(s["credit"].values()) == pytest.approx(3600.0 * share)
    assert list(s["credit"]) == ["2026-11-19"]


def test_nothing_rests_from_the_cut_off_on():
    rows = quiet(CUT_AFTER - 600.0, CUT_AFTER + 600.0)
    s = score.simulate(rows, TERMS, 100, CUT_AFTER)
    assert s["rest_s"] == pytest.approx(600.0)
    assert s["closed_at"] == CUT_AFTER


def test_what_is_held_at_the_cut_off_is_sold_to_the_bids_and_pays_the_fee():
    t = CUT_AFTER - 300.0
    rows = [reading(t), reading(t + 30, traded=100.0, notional=77.0, last=0.77, last_t=t + 10)]        # 100 contracts traded at our bid
    rows += quiet(t + 60, CUT_AFTER + 60, traded=100.0, notional=77.0)
    s = score.simulate(rows, TERMS, 100, CUT_AFTER)
    assert s["bought"] == 100 and s["sold"] == 0
    assert s["left_open"] == 0                                             # sold at the cut-off to the 900 bid at 77c
    assert s["cash"] == pytest.approx(0.0)                                 # bought at 77c, sold at 77c
    assert s["fees"] == pytest.approx(100 * 0.095 * 0.77 * 0.23)
    assert s["notional"] == pytest.approx(154.0)


def test_closing_walks_down_the_book_and_stops_where_it_ends():
    cash, fee, done, traded = score.close_out(150.0, [(0.70, 100.0), (0.60, 20.0)], [(0.75, 500.0)])
    assert done == 120 and cash == pytest.approx(82.0) and traded == pytest.approx(82.0)
    cash, fee, done, traded = score.close_out(-50.0, [(0.70, 100.0)], [(0.75, 500.0)])
    assert done == 50 and cash == pytest.approx(-37.5)


def one_event(rows, settle=None, in_event=1, now=CUT_AFTER + 3600.0, terms=TERMS, size=100):
    out = score.event_rows(EPS_MARKET, rows, terms, settle, in_event, now)
    return next(r for r in out if r["size"] == size)


def test_an_event_counts_only_if_recorded_from_its_listing_to_past_the_cut_off():
    listed = LISTED
    whole = one_event(quiet(listed + 600.0, CUT_AFTER + 60.0, step=30.0))
    assert whole["whole"] and whole["net"] == pytest.approx(whole["reward_paid"])
    late = one_event(quiet(listed + 7 * 3600.0, CUT_AFTER + 60.0))
    assert not late["whole"]
    seen_before = {**TERMS, "listed": score.COUNTED_FROM - 60.0}           # listed a minute before the rule was fixed: described, never judged
    assert not one_event(quiet(listed + 600.0, CUT_AFTER + 60.0), terms=seen_before)["whole"]
    unseen = one_event(quiet(listed + 600.0, CUT_AFTER - 3600.0))
    assert not unseen["whole"] and pd.isna(unseen["net"])                  # the cut-off was never read and there is no result: not finished
    thin = one_event(quiet(listed + 600.0, CUT_AFTER + 60.0, step=60.0))
    assert not thin["whole"]


def test_the_reward_is_counted_by_the_day_and_a_day_under_a_dollar_is_not_paid():
    listed = LISTED
    r = one_event(quiet(listed + 600.0, CUT_AFTER + 60.0))
    seconds = CUT_AFTER - (listed + 600.0)
    assert r["reward_formula"] == pytest.approx(250.0 * 0.1 * seconds / 86_400.0, rel=1e-3)
    assert r["reward_paid"] == pytest.approx(r["reward_formula"])          # every day is well over a dollar
    small = {**TERMS, "pool": 2.0}
    assert one_event(quiet(listed + 600.0, CUT_AFTER + 60.0), terms=small)["reward_paid"] == 0.0


def test_an_event_of_several_markets_is_given_an_even_part_of_the_pool_and_is_not_judged():
    listed = LISTED
    rows = quiet(listed + 600.0, CUT_AFTER + 60.0)
    alone, shared = one_event(rows), one_event(rows, in_event=4)
    assert shared["reward_formula"] == pytest.approx(alone["reward_formula"] / 4.0)
    events = pd.DataFrame([{**shared, "report_date": f"2026-11-{10 + i:02d}", "net": 20.0 + i % 3} for i in range(20)])
    assert score.verdict(events).startswith("NOT YET JUDGED")


def test_the_verdict_waits_for_twelve_events_on_five_dates_and_asks_for_five_dollars_beyond_doubt():
    def events(n, dates, nets):
        return pd.DataFrame([{"in_event": 1, "size": rule.JUDGED, "whole": True, "report_date": f"2026-12-{1 + i % dates:02d}", "net": nets[i % len(nets)]} for i in range(n)])

    assert score.verdict(events(11, 5, [10.0, 12.0])).startswith("NOT YET JUDGED")
    assert score.verdict(events(12, 4, [10.0, 12.0])).startswith("NOT YET JUDGED")
    assert score.verdict(events(12, 6, [10.0, 12.0, 14.0])).startswith("PASSES")
    assert score.verdict(events(12, 6, [3.0, 4.0, 5.0])).startswith("DOES NOT PASS")          # beyond doubt, and too little
    assert score.verdict(events(12, 6, [60.0, -40.0, 10.0])).startswith("DOES NOT PASS")      # enough on average, and not beyond doubt


def entry(slug, program="kpic_20261116", state="INSTRUMENT_STATE_OPEN"):
    return {"marketSlug": slug, "instrumentState": state,
            "timePeriods": [{"programId": program, "status": "active", "rewardPool": 250, "targetSize": 500, "discountFactor": 0.5, "maxSpread": 0.06, "period": "daily_event"}]}


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
    def __init__(self):
        self.described: list[str] = []

    def iter_incentives(self, statuses=None):
        return iter([entry(EPS_MARKET), entry(REV_A), entry("cpausp-gold-updown-1d-2026-11-18-2315z", "metals_gold_updown_1d_20261110"),
                     entry("kpic-tgt-q3eps-2026-11-18-above-2pt08", state="INSTRUMENT_STATE_CLOSED")])

    def market(self, slug):
        self.described.append(slug)
        when = "after the market close" if "intu-q1eps" in slug else "before the market open"
        return {"question": "Will Intuit beat?", "startDate": iso(CUT_AFTER - 40 * 3600.0), "endDate": iso(CUT_AFTER + 14 * 86_400.0), "assetPriceTerms": None,
                "description": f"Intuit is scheduled to report its first-quarter results on November 19, 2026, {when}. The figure is taken from ..."}

    def book(self, slug):
        return {"bids": [level(0.77, 900)], "offers": [level(0.78, 900)], "state": "MARKET_STATE_OPEN", "transactTime": "2026-11-18T17:00:00Z",
                "stats": {"sharesTraded": "0", "notionalTraded": {"value": "0", "currency": "USD"}, "openInterest": "0"}}


def test_the_recorder_reads_the_earnings_markets_and_describes_each_once(tmp_path):
    import csv

    clock, us = Clock(CUT_AFTER - 30 * 3600.0), FakeUS()
    line = top.run(tmp_path, minutes=5.0, us=us, programmes=("kpic",), price_terms=False, test="K1", scorer="scripts/us_kpi_score.py",
                   now=clock.now, sleep=clock.sleep, background=False)
    assert line["markets"] == 2 and line["errors"] == 0 and line["books"] == 20
    assert sorted(us.described) == sorted([EPS_MARKET, REV_A])             # once each, though neither will ever have a price to beat
    rows = {r["slug"]: r for r in csv.DictReader(next(tmp_path.glob("runs/*/markets.csv")).open())}
    assert rows[EPS_MARKET]["reports"] == "after" and rows[REV_A]["reports"] == "before"
    assert float(rows[EPS_MARKET]["listed"]) == CUT_AFTER - 40 * 3600.0
    assert float(rows[EPS_MARKET]["pool"]) == 250.0 and float(rows[EPS_MARKET]["max_spread"]) == 0.06
    assert "test K1" in (tmp_path / "STATUS.md").read_text() and "us_kpi_score.py" in (tmp_path / "STATUS.md").read_text()


def test_the_recorder_of_gold_and_silver_still_asks_again_for_a_price_to_beat(tmp_path):
    """The option that stops the asking is off unless given: test G1's recorder is as it was."""
    import inspect

    assert inspect.signature(top.run).parameters["price_terms"].default is True
    assert top.PROGRAMMES == ("metals_gold_updown_1d", "metals_silver_updown_1d", "crypto_btc_updown_1d", "crypto_alt_updown_1d")
