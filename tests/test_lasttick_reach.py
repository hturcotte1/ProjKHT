"""The reach table of test L1 (scripts/lasttick_reach.py, docs/11 section 5)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location("lasttick_reach", Path(__file__).resolve().parents[1] / "scripts" / "lasttick_reach.py")
lr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lr)

T0 = int(pd.Timestamp("2021-06-01").timestamp())


def frame(close, high=None, low=None, start=T0):
    close = np.asarray(close, dtype=float)
    d = pd.DataFrame({"close": close, "high": close if high is None else np.asarray(high, float), "low": close if low is None else np.asarray(low, float)},
                     index=start + 60 * np.arange(len(close)))
    return d


def test_a_move_is_the_furthest_the_price_went_either_way_in_the_minutes_after():
    #        minute:  0     1     2     3     4     5
    d = frame([100, 100, 100, 100, 100, 100], high=[100, 101, 100, 104, 100, 100], low=[100, 100, 97, 100, 100, 100])
    m1, m2, m3 = lr.moves(d, 1), lr.moves(d, 2), lr.moves(d, 3)
    assert m1[0] == pytest.approx(0.01) and m1[1] == pytest.approx(0.03) and m1[2] == pytest.approx(0.04) and m1[3] == pytest.approx(0.0)
    assert m2[0] == pytest.approx(0.03)                     # minutes 1 and 2: up 1%, down 3%
    assert m3[0] == pytest.approx(0.04)                     # minute 3 adds a high of 104
    assert np.isnan(m1[5]) and np.isnan(m2[4]) and np.isnan(m3[3])     # no future left to look at
    assert m1[0] == pytest.approx(0.01)                     # a minute's own high does not count: only what comes after it


def test_the_reach_is_the_worst_year_and_never_under_the_floor():
    by_year = pd.DataFrame({"year": [2020, 2021, 2022, 2020, 2021, 2022], "h": [5, 5, 5, 10, 10, 10], "one_in": [0.004, 0.025, 0.012, 0.006, 0.03, 0.05]})
    assert lr.reach_from(by_year) == {5: 0.025, 10: 0.05}
    assert lr.reach_from(by_year, [2020]) == {5: lr.FLOOR, 10: lr.FLOOR}
    assert lr.reach_from(by_year, [2020, 2021]) == {5: 0.025, 10: 0.03}


def test_yearly_figures_and_how_often_a_year_went_further(monkeypatch):
    monkeypatch.setattr(lr, "HORIZONS", (1, 2))
    monkeypatch.setattr(lr, "SHOWN", (1, 2))
    monkeypatch.setattr(lr, "ONE_IN", 1_000)
    n = 150_000
    rng = np.random.default_rng(7)
    close = np.full(n, 100.0)
    high = close * (1 + np.abs(rng.normal(0, 0.0005, n)))
    high[[50_000, 50_001, 120_000]] = [108.0, 107.0, 106.0]            # two jumps: one lasting two minutes, one a day or so later
    d = frame(close, high=high)
    by = lr.yearly(d)
    assert set(by["h"]) == {1, 2} and set(by["year"]) == {2021} and int(by.loc[by["h"] == 1, "starts"].iloc[0]) == n - 1
    assert by.loc[by["h"] == 1, "largest"].iloc[0] == pytest.approx(0.08)
    q = by.set_index("h")["one_in"]
    assert 0.001 < q[1] < 0.003 and q[2] >= q[1]                       # the one-in-a-thousand move of quiet noise, not the jumps
    ex = lr.exceed(d, {1: 0.05, 2: 0.05}, [2021]).set_index("h")
    assert ex.loc[1, "over"] == 3 and ex.loc[1, "occasions"] == 2      # starts 49,999, 50,000 and 119,999
    assert ex.loc[2, "over"] == 5 and ex.loc[2, "occasions"] == 2
    assert ex.loc[1, "one_in"] == pytest.approx((n - 1) / 3)


def test_missing_minutes_are_filled_with_the_last_close(tmp_path, monkeypatch):
    t = T0 + 60 * np.array([0, 1, 2, 5, 6])
    pd.DataFrame({"t": t, "open": 100.0, "high": [101, 102, 103, 110, 111], "low": [99, 98, 97, 90, 89], "close": [100, 101, 102, 105, 106]}).to_parquet(
        tmp_path / "minute_btc.parquet", index=False)
    monkeypatch.setattr(lr, "PRICES", tmp_path)
    d = lr.minutes("btc")
    assert len(d) == 7 and d.attrs["missing"] == 2
    assert d["close"].tolist() == [100, 101, 102, 102, 102, 105, 106]
    assert d["high"].tolist() == [101, 102, 103, 102, 102, 110, 111] and d["low"].tolist() == [99, 98, 97, 102, 102, 90, 89]


def test_the_brake_flags_the_hour_after_a_fast_five_minutes():
    n = 600                                                    # ten hours of minutes, flat at 100
    close = np.full(n, 100.0)
    close[300:] = 102.0                                        # a 2% step at minute 300, a five-minute mark
    d = frame(close, start=T0)
    ch = lr.five_minute_changes(d)
    assert len(ch) == n // 5 - 1 and ch.max() == pytest.approx(0.02) and ch.idxmax() == T0 + 300 * 60
    stop = lr.braked(d, 0.01)
    assert stop[:30].all()                                     # under half an hour of history: not enough changes known, so no trade
    assert not stop[30:300].any()                              # then quiet
    assert stop[300:355].all() and stop[355:360].all()         # the step, and the twelve changes that still contain it
    assert not stop[360:].any()                                # an hour on it has left the window
    assert not lr.braked(d, 0.03)[30:].any()                   # a higher limit is not tripped


def test_the_second_yardstick_is_checked_only_on_what_the_brake_lets_through(monkeypatch):
    monkeypatch.setattr(lr, "SHOWN", (3,))
    n = 400_000
    close = np.full(n, 100.0)
    high = close.copy()
    high[200_003] = 106.0                                      # a jump out of nothing: the brake cannot see it coming
    close[300_000:] = 103.0                                    # a fast five minutes...
    high[300_000:] = 103.0
    high[300_010] = 110.0                                      # ...and a jump ten minutes after it: the brake is on
    d = frame(close, high=high, start=int(pd.Timestamp("2021-01-01").timestamp()))
    chk = lr.check_recent(d, {3: 0.05}, 0.01).set_index("year")
    assert chk.loc[2021, "over_without_brake"] == 6            # three starts before each jump
    assert chk.loc[2021, "over"] == 3 and chk.loc[2021, "occasions"] == 1          # only the jump out of nothing gets through
    assert chk.loc[2021, "one_in"] == pytest.approx(chk.loc[2021, "traded_starts"] / 3)
    assert 0 < chk.loc[2021, "braked_share"] < 0.001


def test_the_yardstick_at_the_settlement_itself(monkeypatch):
    monkeypatch.setattr(lr, "SHOWN", (6,))
    start = int(pd.Timestamp("2026-11-06 00:00").timestamp())                    # three evenings; 5 pm New York is 22:00 UTC in November
    n = 3 * 1440
    t = start + 60 * np.arange(n)
    close = np.full(n, 100.0)
    high, low = close.copy(), close.copy()
    def minute(day, hh, mm):
        return (day * 1440) + hh * 60 + mm
    low[minute(0, 21, 57)] = 94.0                                                # evening one: a dip of 6% three minutes before, and back
    close[minute(1, 21, 56):minute(1, 22, 30)] = 95.5                            # evening two: down 4.5% and still there at 22:00
    low[minute(1, 21, 56):minute(1, 22, 30)] = 95.5
    high[minute(1, 21, 56):minute(1, 22, 30)] = 95.5
    d = pd.DataFrame({"close": close, "high": high, "low": low}, index=t)
    counts, events = lr.evenings(d, {6: 0.05}, None)
    c = counts.iloc[0]
    assert c["evenings"] == 3 and c["furthest_over"] == 1 and c["ended_over"] == 0          # the dip went beyond 5% and did not last
    assert c["furthest_over_half"] == 2 and c["ended_over_half"] == 1                       # the second evening ended 4.5% away
    assert sorted(events["date"]) == ["2026-11-06", "2026-11-07"]
    e = events.set_index("date")
    assert e.loc["2026-11-06", "furthest"] == pytest.approx(0.06) and e.loc["2026-11-06", "ended"] == pytest.approx(0.0)
    assert e.loc["2026-11-07", "ended"] == pytest.approx(0.045)
    counts, _ = lr.evenings(d, {6: 0.05}, 0.01)                                             # with a brake: the fall of evening two is not seen coming either
    assert counts.iloc[0]["braked"] == 0 and counts.iloc[0]["furthest_over_half"] == 2
