"""Test L3: the rule, its yardstick and its scorer (docs/11 section 13)."""

from __future__ import annotations

import csv
import gzip
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from kht.trading import lasthours_rule as rule
from kht.trading.us_lasttick import BOOK_FIELDS, INDEX_FIELDS, MARKET_FIELDS

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


score = module("us_lasthours_score")
reach_script = module("lasthours_reach")

END = 1_794_693_600.0            # 14 November 2026, 22:00:00 UTC: an evening the test counts
LEVEL = 72_000.0
REACH = {"btc": {h: 0.02 + 0.0002 * h for h in range(5, 346, 5)}}       # 3% half an hour ahead, 8% five hours ahead


def bracket(lower, upper=None, slug=None, end=END, horizon="daily", coin="btc", kind="range"):
    return {"slug": slug or f"cpc-btc-range-day-2026-11-14-{int(lower)}", "kind": kind, "horizon": horizon, "coin": coin, "end": end,
            "lower": lower, "upper": lower + 249.99 if upper is None else upper, "strike": ""}


def book(bid=0.01, qty=1005.1):
    return {"bid1": bid, "bid_qty1": qty, "ask1": 0.02, "ask_qty1": 200.0}


# ---------------------------------------------------------------------------- the rule

def test_the_reach_is_read_at_the_next_figure_in_the_table():
    assert rule.reach_for(REACH, "btc", 61.2) == REACH["btc"][65] and rule.reach_for(REACH, "btc", 60.0) == REACH["btc"][60]
    assert rule.reach_for(REACH, "btc", 0.5) == REACH["btc"][5]                       # never a shorter time than the table has
    assert rule.reach_for(REACH, "btc", 345.01) is None and rule.reach_for(REACH, "doge", 60) is None


def test_a_far_bracket_with_a_bid_is_sold_and_everything_else_is_left():
    ts = END - 120 * 60
    at = ts - 60
    far = bracket(80_000.0)                                                         # 11% above: the reach two hours ahead is 4.5%
    t, why = rule.decide(far, book(), ts, LEVEL, at, REACH)
    assert why == "trade" and t["side"] == "sell" and t["price"] == 0.01 and t["qty"] == 1005.1
    assert t["gap"] == pytest.approx(8000 / 72000) and t["ahead"] == pytest.approx(122.0) and t["reach"] == REACH["btc"][125]
    assert t["premium"] == pytest.approx(1005.1 * 0.01 * (1 - 0.095 * 0.99)) and t["locked"] == pytest.approx(1005.1 * 0.99)
    assert rule.pnl(t, 0.0) == pytest.approx(t["premium"]) and rule.pnl(t, 1.0) == pytest.approx(t["premium"] - 1005.1)
    near = bracket(74_000.0)                                                        # 2.8% above
    assert rule.decide(near, book(), ts, LEVEL, at, REACH)[1] == "not far enough"
    here = bracket(72_000.0)
    assert rule.decide(here, book(0.30, 500.0), ts, LEVEL, at, REACH)[1] == "the index is in this bracket"
    assert rule.decide(far, book(None, None), ts, LEVEL, at, REACH)[1] == "far enough, nobody bidding"
    assert rule.decide(far, book(0.06), ts, LEVEL, at, REACH)[1] == "far enough, but the book disagrees"
    assert rule.decide(far, book(qty=5000.0), ts, LEVEL, at, REACH)[0]["qty"] == rule.CAP
    assert rule.decide(far, book(), ts, LEVEL, ts - 11 * 60, REACH)[1] == "no fresh index level"
    assert rule.decide(far, book(), ts, None, None, REACH)[1] == "no fresh index level"
    low = bracket(60_000.0)                                                         # as far below
    assert rule.decide(low, book(), ts, LEVEL, at, REACH)[1] == "trade"
    top = bracket(81_500.0, upper="")                                               # the open end above: one edge only
    assert rule.decide(top, book(), ts, LEVEL, at, REACH)[1] == "trade"


def test_only_brackets_of_daily_and_weekly_ladders_and_only_inside_the_window():
    ts, at = END - 120 * 60, END - 121 * 60
    above = {"slug": "cpc-btc-above-day-2026-11-14-80000", "kind": "above_below", "horizon": "daily", "coin": "btc", "end": END, "strike": 80_000.0}
    assert rule.decide(above, book(), ts, LEVEL, at, REACH)[1] == "not a bracket of a daily or weekly ladder"
    assert rule.decide(bracket(80_000.0, horizon="hourly"), book(), ts, LEVEL, at, REACH)[1] == "not a bracket of a daily or weekly ladder"
    assert rule.decide(bracket(80_000.0, horizon="weekly"), book(), ts, LEVEL, at, REACH)[1] == "trade"
    far = bracket(80_000.0)
    assert rule.decide(far, book(), END - 331 * 60, LEVEL, END - 332 * 60, REACH)[1] == "outside the time window"
    assert rule.decide(far, book(), END - 60, LEVEL, END - 120, REACH)[1] == "outside the time window"
    mid = bracket(78_000.0)                                                         # 8.3% away
    assert rule.decide(mid, book(), END - 330 * 60, LEVEL, END - 331 * 60, REACH)[1] == "not far enough"       # five and a half hours ahead the reach is 8.7%
    assert rule.decide(mid, book(), END - 120 * 60, LEVEL, END - 121 * 60, REACH)[1] == "trade"                # two hours ahead it is 4.5%
    assert rule.decide(bracket(82_000.0), book(), END - 330 * 60, LEVEL, END - 334 * 60, REACH)[1] == "trade"   # 13.9% away: the table reaches to 345 minutes
    assert rule.decide(bracket(82_000.0), book(), END - 330 * 60, LEVEL, END - 345.5 * 60, REACH)[1] == "no fresh index level"


def test_the_brake_is_the_one_of_the_last_tick_test():
    ts, at = END - 120 * 60, END - 121 * 60
    far, brake = bracket(80_000.0), {"btc": 0.01}
    calm = [(at - 300 * k, LEVEL + 10 * k) for k in range(0, 9)]
    assert rule.decide(far, book(), ts, LEVEL, at, REACH, brake, [])[1] == "far enough, too little index history"
    assert rule.decide(far, book(), ts, LEVEL, at, REACH, brake, calm)[1] == "trade"
    jumpy = calm[:3] + [(calm[3][0], LEVEL * 0.97)] + calm[4:]
    assert rule.decide(far, book(), ts, LEVEL, at, REACH, brake, jumpy)[1] == "far enough, but the index has been moving fast"


def test_the_table_in_the_repository_is_the_one_the_rule_reads():
    reach, brake = rule.load(ROOT / "config" / "lasthours_reach.json")
    raw = json.loads((ROOT / "config" / "lasthours_reach.json").read_text())
    assert set(reach) == {"btc", "eth", "sol", "xrp"} and sorted(reach["btc"]) == list(range(5, 346, 5)) and raw["one_in"] == 500 and raw["check_passed"] is True
    for coin, row in reach.items():
        values = [row[h] for h in sorted(row)]
        assert values == sorted(values) and values[0] >= 0.01                         # never less for a longer time, never under the floor
    assert brake == {c: float(v) for c, v in json.loads((ROOT / "config" / "lasttick_reach.json").read_text())["recent"]["brake"].items()}   # L1's brake, unchanged


# ---------------------------------------------------------------------------- the yardstick's arithmetic

def test_the_yardstick_measures_where_the_price_ended_and_takes_the_worst_year():
    minutes_a_year = 20_000
    idx = np.concatenate([pd.Timestamp("2021-01-01").timestamp() + 60 * np.arange(minutes_a_year), pd.Timestamp("2022-01-01").timestamp() + 60 * np.arange(minutes_a_year)])
    rng = np.random.default_rng(7)
    step = np.concatenate([rng.normal(0, 0.002, minutes_a_year), rng.normal(0, 0.0005, minutes_a_year)])       # a wild year, then a calm one
    d = pd.DataFrame({"close": 100 * np.exp(np.cumsum(step))}, index=idx)
    e = reach_script.ended(d, 10)
    assert e[0] == pytest.approx(abs(d["close"].iloc[10] / d["close"].iloc[0] - 1)) and np.isnan(e[-1])
    by_year = reach_script.yearly(d, horizons=(5, 10, 20), one_in=500)
    wild, calm = by_year[by_year.year == 2021].set_index("h")["one_in"], by_year[by_year.year == 2022].set_index("h")["one_in"]
    assert (wild > 2 * calm).all() and wild[20] > wild[5]
    reach = reach_script.reach_from(by_year, floor=0.01)
    assert float(wild[20]) <= reach[20] <= float(wild[20]) + 1e-5 and reach[5] >= 0.01 and reach[5] <= reach[10] <= reach[20]
    # a longer time never has a smaller reach, even where the raw figures dip
    dipped = pd.DataFrame({"h": [5, 10, 15], "year": [2021] * 3, "one_in": [0.03, 0.02, 0.05]})
    assert reach_script.reach_from(dipped, floor=0.01) == {5: 0.03, 10: 0.03, 15: 0.05}
    ex = reach_script.exceeded(d, reach, None, horizons=(5, 10, 20))
    assert (ex["beyond"] / ex["starts"]).max() <= 1 / 500 + 1 / 20_000               # by its making, no year goes beyond it more often than one start in 500 (give or take one start)


# ---------------------------------------------------------------------------- the scorer, on a recording

def write_run(state, run, books, markets, index):
    d = state / "runs" / run
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


def evening(state, end=END, run="r1", date="2026-11-14"):
    """A Bitcoin ladder of 40 brackets from $66,000 with the index at $72,000, read every two minutes from 330 minutes before its end.

    Every bracket carries a 1c bid for 1,005.1 until an hour before the end
    and a bid for a tenth of a contract after it. The bracket at $80,000 is
    bid 2,005.1; the one at $79,000 loses its bid two minutes after it is
    first far enough.
    """
    lowers = [66_000.0 + 400 * i for i in range(40)]
    markets, books, index = [], [], []
    for lo in lowers:
        row = dict.fromkeys(MARKET_FIELDS, "")
        row.update({"run": run, "slug": f"cpc-btc-range-day-{date}-{int(lo)}", "kind": "range", "horizon": "daily", "coin": "btc", "index": "BRTI", "end": end,
                    "lower": lo, "upper": lo + 399.99, "first_seen": end - 330 * 60})
        markets.append(row)
    for k in range(165, 0, -1):
        left = 2 * k * 60.0
        for j, m in enumerate(markets):
            qty = 1005.1 if left > 3600 else 0.1
            if m["lower"] == 80_000.0 and left > 3600:
                qty = 2005.1
            row = dict.fromkeys(BOOK_FIELDS, "")
            row.update({"run": run, "ts": end - left + 0.5 * j, "slug": m["slug"], "left": left - 0.5 * j, "state": "OPEN", "bid1": 0.01, "bid_qty1": qty, "ask1": 0.02, "ask_qty1": 200.0})
            books.append(row)
    for k in range(-13, 67):                                                       # a level every five minutes from an hour before the recording to its end
        at = end - 330 * 60 + 300 * k
        index.append({"run": run, "ts": at + 40.0, "coin": "btc", "level": LEVEL + (k % 3), "at": at, "slug": "x"})
    write_run(state, run, books, markets, index)
    return lowers


def test_the_scorer_sells_each_far_bracket_once_as_soon_as_it_is_far_enough(tmp_path):
    lowers = evening(tmp_path)
    b, m, i = score.load(tmp_path)
    history = score.known_levels(tmp_path, i, m, look_up=False)
    assert len(history["btc"]) == 80
    trades, fate = score.apply(b, m, i, REACH, {"btc": 0.01}, history)
    sold = {t["slug"]: t for t in trades}
    # with real size left only until an hour before the end, a bracket is sold if it was far enough by then: 3.2% + 1% a... the reach an hour ahead is 3.3%
    for lo in lowers:
        slug = f"cpc-btc-range-day-2026-11-14-{int(lo)}"
        edge = lo if lo > LEVEL else lo + 399.99
        gap = abs(edge - LEVEL) / LEVEL
        if lo <= LEVEL <= lo + 399.99:
            assert slug not in sold
        elif gap > REACH["btc"][10]:                                               # far enough at some reading before the end
            assert slug in sold and sold[slug]["gap"] > sold[slug]["reach"]
    far = sold["cpc-btc-range-day-2026-11-14-80000"]
    assert far["qty"] == rule.CAP and far["shown"] == 2005.1                       # capped at 2,000 a bracket
    assert far["gap"] == pytest.approx(8000 / 72000, abs=1e-4) and far["left"] > 3600   # 11.1%: far enough hours ahead, and sold then, at full size
    assert far["still_next"] is True
    early = [t for t in trades if t["left"] > 3600]
    late = [t for t in trades if t["left"] <= 3600]
    assert early and late and all(t["qty"] >= 1005.1 for t in early) and all(t["qty"] == 0.1 for t in late)     # after the hour only the tenth of a contract is left
    assert fate.set_index("slug").loc["cpc-btc-range-day-2026-11-14-72000", "fate"] == "the index is in this bracket"
    assert len(sold) == len(trades)                                                # one sale a bracket


def test_accounts_evenings_and_the_bar(tmp_path):
    evening(tmp_path)
    evening(tmp_path, end=END - 2 * 86_400, run="r0", date="2026-11-12")           # an evening seen before the rule was fixed
    b, m, i = score.load(tmp_path)
    trades, _ = score.apply(b, m, i, REACH, {"btc": 0.01}, score.known_levels(tmp_path, i, m, look_up=False))
    paid = {t["slug"]: 0.0 for t in trades}
    t_all = score.account(trades, paid)
    t_10k = score.account(rule.small_account(trades, money=score.MONEY), paid)
    ends = score.recorded(b, m)
    assert ends == {END - 2 * 86_400: 165, END: 165}
    ev = score.by_evening(t_10k, ends)
    assert list(ev["counted"]) == [False, True] and ev["recorded"].all() and ev["settled"].all() and (ev["lost"] == 0).all()
    assert ev["tied_up"].max() <= score.MONEY + 1e-6 and ev.loc[1, "pnl"] == pytest.approx(ev.loc[1, "premium"]) and ev.loc[1, "pnl"] > 50
    assert score.by_evening(t_all, ends).loc[1, "contracts"] > ev.loc[1, "contracts"]
    assert score.verdict(ev).startswith("NOT YET JUDGED: 1 evenings")              # the evening of 12 November counts for nothing
    four = pd.concat([ev[ev["counted"]].assign(end=END + 86_400 * k) for k in range(4)], ignore_index=True)
    assert score.verdict(four).startswith("PASSED: 4 evenings")
    assert score.verdict(four.assign(pnl=20.0)).startswith("NOT PASSED")
    assert score.verdict(four.assign(lost=[0, 0, 1, 0])).startswith("NOT PASSED")
    # a bracket that paid: the whole of that sale is lost, and the evening says so
    worst = max(trades, key=lambda t: (t["end"], t["qty"]))
    hit = score.by_evening(score.account(trades, paid | {worst["slug"]: 1.0}), ends)
    assert hit.loc[1, "lost"] == 1 and hit.loc[1, "pnl"] == pytest.approx(score.by_evening(t_all, ends).loc[1, "pnl"] - worst["qty"])
    lad = score.by_ladder(t_all)
    assert len(lad) == 2 and (lad["largest_sale"] == rule.CAP * 0.99).all() and set(lad["still_next"].str.split(" of ").str[1].astype(int)) == {int(lad["brackets"].iloc[0])}
    # not settled yet: the evening is not counted as made or lost
    assert pd.isna(score.by_evening(score.account(trades, {}), ends).loc[1, "pnl"])


def test_the_script_runs_on_a_recording_and_writes_its_tables(tmp_path, monkeypatch, capsys):
    state, out = tmp_path / "state", tmp_path / "out"
    evening(state)
    b, m, i = score.load(state)
    pd.DataFrame({"slug": sorted(m["slug"]), "settle": 0.0}).to_csv(state / "settlements.csv", index=False)
    monkeypatch.setattr(sys, "argv", ["us_lasthours_score.py", "--state", str(state), "--out", str(out)])
    assert score.main() == 0
    text = capsys.readouterr().out
    assert "NOT YET JUDGED: 1 evenings" in text and "L3-10k" in text and "14 Nov 22:00" in text
    assert len(pd.read_csv(out / "lh_trades.csv")) > 10 and len(pd.read_csv(out / "lh_by_evening_10k.csv")) == 1 and (out / "lh_summary.txt").exists()
    monkeypatch.setattr(sys, "argv", ["us_lasthours_score.py", "--state", str(tmp_path / "nothing"), "--out", str(out)])
    assert score.main() == 0 and "Nothing has been recorded yet" in capsys.readouterr().out
