"""The scorer of the recordings of whole ladders (scripts/us_ladder_score.py, docs/11 section 12)."""

from __future__ import annotations

import csv
import gzip
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

from kht.trading import ladder_rule as rule
from kht.trading.us_lasttick import BOOK_FIELDS, MARKET_FIELDS

spec = importlib.util.spec_from_file_location("us_ladder_score", Path(__file__).resolve().parents[1] / "scripts" / "us_ladder_score.py")
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)

END = 1_794_520_800.0            # 12 November 2026, 22:00:00 UTC
MIN = 60.0


def market_row(slug, coin="btc", horizon="daily", kind="range", end=END, run="r1"):
    row = dict.fromkeys(MARKET_FIELDS, "")
    row.update({"run": run, "slug": slug, "kind": kind, "horizon": horizon, "coin": coin, "index": "BRTI", "end": end, "first_seen": end - 330 * MIN})
    return row


def book_row(slug, minutes_left, bids=(), run="r1", end=END, seconds_before_reading=20.0):
    """A recorded book, read twenty seconds before the reading that is ``minutes_left`` before the end."""
    row = dict.fromkeys(BOOK_FIELDS, "")
    ts = end - minutes_left * MIN - seconds_before_reading
    row.update({"run": run, "ts": ts, "slug": slug, "left": end - ts, "state": "OPEN"})
    for i, (px, qty) in enumerate(bids, start=1):
        row[f"bid{i}"], row[f"bid_qty{i}"] = px, qty
    return row


def write_run(state, run, books, markets):
    d = state / "runs" / run
    d.mkdir(parents=True)
    with gzip.open(d / "books.csv.gz", "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=BOOK_FIELDS)
        w.writeheader()
        w.writerows(books)
    with (d / "markets.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MARKET_FIELDS)
        w.writeheader()
        w.writerows(markets)


FAR = [f"cpc-btc-range-day-2026-11-12-{66000 + 250 * i}" for i in range(30)]
NEAR = ["cpc-btc-range-day-2026-11-12-74000", "cpc-btc-range-day-2026-11-12-74250"]
ABOVE = "cpc-btc-range-day-2026-11-12-above-81500"
ETH_FAR = [f"cpceth-eth-range-day-2026-11-12-{1400 + 20 * i}" for i in range(30)]
ETH_NEAR = ["cpceth-eth-range-day-2026-11-12-2060", "cpceth-eth-range-day-2026-11-12-2080"]


def evening(state):
    """One recorded evening: a Bitcoin and an Ether ladder ending together, read every two minutes.

    Until 200 minutes before the end the far brackets have no bids. From then
    on each has 1,000 at 1c. One far Bitcoin bracket is not read after 210
    minutes before the end. The open end of the Bitcoin ladder is first
    quoted 100 minutes before the end.
    """
    markets = [market_row(s) for s in FAR + NEAR + [ABOVE]] + [market_row(s, coin="eth") for s in ETH_FAR + ETH_NEAR]
    markets += [market_row("cpc-btc-above-day-2026-11-12-78000", kind="above_below"), market_row("cpc-btc-range-hr-2026-11-12-2200z-74000", horizon="hourly")]
    books = []
    for k in range(165, 0, -1):
        left = 2 * k
        penny = [(0.01, 1000.0)] if left <= 200 else []
        for s in FAR:
            if s == FAR[29] and left < 210:
                continue                                                         # this one drops out of the recording
            books.append(book_row(s, left, penny))
        books.append(book_row(NEAR[0], left, [(0.50, 300.0), (0.30, 5000.0)]))
        books.append(book_row(NEAR[1], left, [(0.40, 300.0), (0.20, 5000.0)]))
        books.append(book_row(ABOVE, left, [(0.01, 1000.0)] if left <= 100 else []))
        for s in ETH_FAR:
            books.append(book_row(s, left, penny))
        books.append(book_row(ETH_NEAR[0], left, [(0.50, 300.0)]))
        books.append(book_row(ETH_NEAR[1], left, [(0.40, 300.0)]))
        books.append(book_row("cpc-btc-above-day-2026-11-12-78000", left, [(0.01, 1500.0)]))
    write_run(state, "r1", books, markets)


def test_ladders_are_the_daily_and_weekly_brackets_of_a_coin_that_end_together(tmp_path):
    evening(tmp_path)
    b, m = score.load(tmp_path)
    found = score.ladders(m)
    assert [(x["coin"], x["horizon"], len(x["slugs"])) for x in found] == [("btc", "daily", 33), ("eth", "daily", 32)]   # Bitcoin is served first
    assert all("above-day" not in s and "range-hr" not in s for x in found for s in x["slugs"])
    weekly = pd.concat([m, pd.DataFrame([market_row("cpc-btc-range-wk-2026-11-12-74000", horizon="weekly")])])
    assert [(x["coin"], x["horizon"]) for x in score.ladders(weekly)] == [("btc", "daily"), ("btc", "weekly"), ("eth", "daily")]
    assert score.ladders(pd.DataFrame()) == []


def test_the_account_sells_a_ladder_once_when_it_locks_enough_and_adds_what_is_quoted_later(tmp_path):
    evening(tmp_path)
    b, m = score.load(tmp_path)
    positions, curve = score.account(score.ladders(m), score.Books(b))
    assert len(positions) == 1                                                   # the Ether ladder finds the money used
    p = positions[0]
    assert p["coin"] == "btc" and p["left"] == 200 * MIN and p["q"] == 300.0     # the first reading at which the far bids are there
    # 29 far brackets and the two near the price: the far bracket not read for ten minutes is not sold
    assert p["first_legs"] == 31 and FAR[29] not in p["legs"]
    money = 29 * 3.0 + 150.0 + 120.0
    fees = 29 * rule.fee(300, 0.01) + rule.fee(300, 0.5) + rule.fee(300, 0.4)
    assert p["locked_at_sale"] == pytest.approx(money - fees - 300.0) and p["locked_at_sale"] >= rule.PATIENT
    # the open end, first quoted an hour and forty minutes before the end, is added once, at the size of the sale
    assert p["added"] == 1 and p["legs"][ABOVE]["sold"] == 300.0 and len(p["legs"]) == 32
    assert p["pays_at_most"] == 300.0 and p["locks"] == pytest.approx(money + 3.0 - fees - rule.fee(300, 0.01) - 300.0)
    assert p["margin"] == pytest.approx(30 * 297.0 + 150.0 + 180.0) and p["margin"] <= rule.MONEY
    assert rule.result(p, {NEAR[1]: 1.0}) == pytest.approx(p["locks"])           # a sold bracket pays: what was locked is kept
    assert rule.result(p, {FAR[29]: 1.0}) == pytest.approx(p["locks"] + 300.0)   # the one bracket never sold pays: nothing to pay out

    c = curve[curve["coin"] == "btc"].set_index("minutes_left")
    assert len(c) == 165 and c.loc[330.0, "with_bid"] == 2 and c.loc[330.0, "at_1c"] == 0 and c.loc[330.0, "best_locks"] < 0
    assert c.loc[200.0, "fresh"] == 32 and c.loc[200.0, "with_bid"] == 31 and c.loc[200.0, "at_1c"] == 29     # 33 brackets, one no longer read, one open end not yet quoted
    assert c.loc[200.0, "sum_best_bids"] == pytest.approx(0.29 + 0.9) and c.loc[200.0, "best_q"] == 300.0
    assert c.loc[100.0, "with_bid"] == 32 and c.loc[2.0, "locks_100"] == pytest.approx(rule.sale({**{s: [(0.01, 1000.0)] for s in FAR[:29] + [ABOVE]},
                                                                                              NEAR[0]: [(0.5, 300.0)], NEAR[1]: [(0.4, 300.0)]}, 100.0)["locks"])
    e = curve[curve["coin"] == "eth"].set_index("minutes_left")
    assert e.loc[200.0, "best_locks"] > rule.PATIENT                             # described as if the money were untouched: it would have sold


def test_with_more_money_both_ladders_sell_in_the_order_bitcoin_then_ether(tmp_path):
    evening(tmp_path)
    b, m = score.load(tmp_path)
    positions, _ = score.account(score.ladders(m), score.Books(b), money=20_000.0)
    assert [p["coin"] for p in positions] == ["btc", "eth"] and positions[1]["q"] == 300.0 and positions[1]["left"] == 200 * MIN
    # With less than both need, the second gets what is left. That is too little to lock $25,
    # so it waits, and sells in the last half hour, when $10 is enough
    positions, _ = score.account(score.ladders(m), score.Books(b), money=9_240.0 + 3_000.0)
    assert [p["coin"] for p in positions] == ["btc", "eth"] and positions[1]["left"] == 30 * MIN
    assert positions[1]["margin"] <= 3_000.0 + 1e-6 and 90.0 < positions[1]["q"] < 110.0 and 10.0 <= positions[1]["locks"] < 25.0


def test_an_evening_counts_once_recorded_and_settled_and_the_verdict_waits_for_five(tmp_path):
    evening(tmp_path)
    b, m = score.load(tmp_path)
    found = score.ladders(m)
    positions, curve = score.account(found, score.Books(b))
    paid = {s: 0.0 for x in found for s in x["slugs"]} | {NEAR[1]: 1.0, ETH_NEAR[0]: 1.0}
    ev = score.evenings(found, curve, positions, paid)
    assert len(ev) == 1 and bool(ev.loc[0, "recorded"]) and ev.loc[0, "btc_daily_readings"] == 165 and ev.loc[0, "sales"] == 1
    assert bool(ev.loc[0, "settled"]) and ev.loc[0, "kept"] == pytest.approx(positions[0]["locks"]) and ev.loc[0, "ladders_not_paying_one"] == ""
    assert score.verdict(ev, positions, paid).startswith("NOT YET JUDGED: 1 evenings recorded and settled")
    # five such evenings pass the bar; a ladder that paid on two brackets is named, and a loss fails it
    five = pd.concat([ev.assign(end=END + 86400 * i) for i in range(5)], ignore_index=True)
    assert score.verdict(five, positions, paid).startswith("PASSED: 5 evenings, a sale on 5")
    assert score.verdict(five.assign(kept=5.0), positions, paid).startswith("NOT PASSED")
    two = paid | {NEAR[0]: 1.0}
    bad = score.evenings(found, curve, positions, two)
    assert bad.loc[0, "ladders_not_paying_one"].startswith("btc daily") and bad.loc[0, "kept"] < 0
    assert "ladders with a loss: btc daily" in score.verdict(pd.concat([bad.assign(end=END + 86400 * i) for i in range(5)], ignore_index=True)
                                                              .assign(end=lambda d: [END] * 5), positions, two)
    # not settled yet: nothing is counted as kept
    assert pd.isna(score.evenings(found, curve, positions, {}).loc[0, "kept"])
    # a recording with too many holes does not count as an evening
    thin = curve[curve["minutes_left"] <= 200]
    assert not bool(score.evenings(found, thin, positions, paid).loc[0, "recorded"])


def test_the_script_runs_on_a_recording_and_writes_its_tables(tmp_path, monkeypatch, capsys):
    state, out = tmp_path / "state", tmp_path / "out"
    evening(state)
    b, m = score.load(state)
    slugs = [s for x in score.ladders(m) for s in x["slugs"]]
    pd.DataFrame({"slug": slugs, "settle": [1.0 if s in (NEAR[1], ETH_NEAR[0]) else 0.0 for s in slugs]}).to_csv(state / "settlements.csv", index=False)
    monkeypatch.setattr(sys, "argv", ["us_ladder_score.py", "--state", str(state), "--out", str(out)])
    assert score.main() == 0
    text = capsys.readouterr().out
    assert "NOT YET JUDGED" in text and "btc daily 12 Nov 22:00" in text and "no sale" not in text
    assert (out / "ld_summary.txt").read_text().strip().endswith(text.strip()[-40:])
    sales, legs, curve = pd.read_csv(out / "ld_sales.csv"), pd.read_csv(out / "ld_legs.csv"), pd.read_csv(out / "ld_curve.csv")
    assert len(sales) == 1 and len(legs) == 32 and legs["paid"].sum() == 1.0 and len(curve) == 330
    monkeypatch.setattr(sys, "argv", ["us_ladder_score.py", "--state", str(tmp_path / "nothing"), "--out", str(out)])
    assert score.main() == 0 and "Nothing has been recorded yet" in capsys.readouterr().out
