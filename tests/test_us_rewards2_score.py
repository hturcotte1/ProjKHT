"""The scorer of test R2 (scripts/us_rewards2_score.py, docs/13 section 3)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

spec = importlib.util.spec_from_file_location("us_rewards2_score", Path(__file__).resolve().parents[1] / "scripts" / "us_rewards2_score.py")
r2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r2)

DAY = 86_400.0


def test_only_games_from_the_nineteenth_count():
    assert pd.Timestamp(r2.COUNTED_FROM, unit="s", tz="UTC").tz_convert("America/New_York").strftime("%Y-%m-%d %H:%M") == "2026-11-19 00:00"
    g = pd.DataFrame({"slug": ["old", "new", "moved", "moved"], "start": [r2.COUNTED_FROM - 1, r2.COUNTED_FROM, r2.COUNTED_FROM - 600, r2.COUNTED_FROM + 600]})
    h = pd.DataFrame({"slug": ["old", "new", "moved"], "dv": [1.0, 2.0, 3.0]})
    kept, hits = r2.counted(g, h)
    assert set(kept["slug"]) == {"new", "moved"}                           # a game whose start was moved past midnight counts by where it ended up
    assert sorted(hits["dv"]) == [2.0, 3.0]
    assert r2.counted(pd.DataFrame(), pd.DataFrame())[0].empty


def games(n, dates, net, programme="utr_moneyline_day_of_20261008", in_event=1, over=True, settle=1.0):
    return pd.DataFrame({"markets_in_event": in_event, "program": programme, "over": over, "settle": settle, "net": [net(i) for i in range(n)],
                         "day": [f"2026-11-{19 + i % dates:02d}" for i in range(n)]})


def test_the_judge_takes_utr_games_that_are_old_enough_and_settled():
    per = pd.concat([games(5, 5, lambda i: 1.0), games(3, 3, lambda i: 9.0, programme="itf_moneyline_dayof_20261018"), games(2, 2, lambda i: 9.0, in_event=3),
                     games(2, 2, lambda i: 9.0, over=False), games(2, 2, lambda i: 9.0, settle=None)], ignore_index=True)
    assert len(r2.judged(per)) == 5


def test_the_verdict_waits_for_800_games_on_12_dates():
    text, mean, z, k = r2.verdict(r2.judged(games(600, 12, lambda i: 2.0 + (i % 5))))
    assert text.startswith("NOT YET JUDGED: 600 games on 12 US dates")
    assert r2.verdict(r2.judged(games(900, 9, lambda i: 2.0 + (i % 5))))[0].startswith("NOT YET JUDGED: 900 games on 9 US dates")
    assert r2.verdict(r2.judged(games(0, 1, lambda i: 0.0)))[0].startswith("NOT YET JUDGED: no game")
    good = r2.verdict(r2.judged(games(900, 12, lambda i: 2.0 + (i % 12) * 0.1 + (i % 5))))
    assert good[0].startswith("PASSES: 900 games on 12 US dates") and good[3] == 12
    # ahead on average, but one date in two is far behind: twelve dates cannot tell that from luck
    swing = r2.verdict(r2.judged(games(900, 12, lambda i: 30.0 if i % 2 else -26.0)))
    assert swing[0].startswith("DOES NOT PASS") and swing[1] > 0
    assert r2.verdict(r2.judged(games(900, 12, lambda i: -1.0 - (i % 3))))[0].startswith("DOES NOT PASS")
