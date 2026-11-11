"""The scorer of the live last-minutes recordings (scripts/us_lasttick_score.py, docs/11 section 5)."""

from __future__ import annotations

import csv
import gzip
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from kht.trading.us_lasttick import BOOK_FIELDS, INDEX_FIELDS, MARKET_FIELDS

spec = importlib.util.spec_from_file_location("us_lasttick_score", Path(__file__).resolve().parents[1] / "scripts" / "us_lasttick_score.py")
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)

END = 1_794_434_400.0
REACH = {"btc": {h: 0.03 for h in range(1, 31)}}


def market_row(slug, strike, run="r1", kind="above_below", **kw):
    row = dict.fromkeys(MARKET_FIELDS, "")
    row.update({"run": run, "slug": slug, "kind": kind, "horizon": "daily", "coin": "btc", "index": "BRTI", "end": END, "strike": strike, "first_seen": END - 1000})
    row.update(kw)
    return row


def book_row(slug, left, bid=None, bid_qty=None, ask=None, ask_qty=None, run="r1"):
    row = dict.fromkeys(BOOK_FIELDS, "")
    row.update({"run": run, "ts": END - left, "slug": slug, "left": left, "state": "OPEN", "bid1": bid, "bid_qty1": bid_qty, "ask1": ask, "ask_qty1": ask_qty})
    return {k: ("" if v is None else v) for k, v in row.items()}


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


def test_the_rule_is_applied_to_what_the_recorder_wrote(tmp_path):
    index = [{"run": "r1", "ts": END - 1000, "coin": "btc", "level": 74_000.0, "at": END - 1100, "slug": "five-a"},
             {"run": "r1", "ts": END - 700, "coin": "btc", "level": 74_100.0, "at": END - 800, "slug": "five-b"}]
    markets = [market_row("far", 78_000), market_row("near", 74_500), market_row("deep", 70_000), market_row("nobody", 79_000), market_row("odd", 80_000)]
    books = [book_row("far", 960, bid=0.01, bid_qty=1500),                      # too early: not a reading the rule uses
             book_row("far", 900, bid=0.01, bid_qty=1500, ask=0.02, ask_qty=100),
             book_row("far", 860, bid=0.01, bid_qty=900),                       # the first reading that qualifies is the one traded
             book_row("near", 900, bid=0.01, bid_qty=1500), book_row("near", 300, bid=0.01, bid_qty=1500),
             book_row("deep", 880, bid=0.97, bid_qty=65), book_row("deep", 500, bid=0.97, bid_qty=65, ask=0.99, ask_qty=255),
             book_row("nobody", 600, ask=0.02, ask_qty=100),
             book_row("odd", 600, bid=0.40, bid_qty=10)]
    write_run(tmp_path, "r1", books, markets, index)
    b, m, i = score.load(tmp_path)
    trades, fate = score.apply(b, m, i, REACH)
    fate = fate.set_index("slug")["fate"].to_dict()
    assert fate == {"far": "trade", "near": "within reach", "deep": "trade", "nobody": "out of reach, nobody bidding", "odd": "out of reach, but the book disagrees"}
    by_slug = {t["slug"]: t for t in trades}
    assert by_slug["far"]["qty"] == 1500 and by_slug["far"]["left"] == 900 and by_slug["far"]["level"] == 74_000.0      # the level known at that moment
    assert by_slug["far"]["age"] == pytest.approx(200.0)
    assert by_slug["deep"]["side"] == "buy" and by_slug["deep"]["left"] == 500 and by_slug["deep"]["level"] == 74_100.0  # by then a newer level was out
    settle = pd.Series({"far": 0.0, "deep": 1.0})
    acc = score.account(trades, settle).set_index("slug")
    assert acc.loc["far", "pnl"] == pytest.approx(15.0 - 0.095 * 0.01 * 0.99 * 1500) and not acc.loc["far", "lost"]
    assert acc.loc["deep", "pnl"] == pytest.approx(255 * 0.01 - 0.095 * 0.99 * 0.01 * 255)
    lost = score.account(trades, pd.Series({"far": 1.0})).set_index("slug")
    assert lost.loc["far", "pnl"] == pytest.approx(-1485.0 - 0.095 * 0.01 * 0.99 * 1500) and bool(lost.loc["far", "lost"])
    assert pd.isna(lost.loc["deep", "pnl"])                                      # not settled yet: no result, and not a loss
    table = score.by(score.account(trades, settle), "day")
    assert table.loc[0, "trades"] == 2 and table.loc[0, "lost"] == 0 and table.loc[0, "settled"] == 2


def test_a_market_followed_in_two_runs_is_one_market(tmp_path):
    index = [{"run": "r1", "ts": END - 1000, "coin": "btc", "level": 74_000.0, "at": END - 1100, "slug": "five-a"}]
    up = dict(kind="up_down")
    write_run(tmp_path, "r1", [book_row("far", 1000, bid=0.01, bid_qty=1500), book_row("updown", 1000, bid=0.01, bid_qty=10)],
              [market_row("far", 78_000), market_row("updown", "", price_to_beat="", **up)], index)
    write_run(tmp_path, "r2", [book_row("far", 700, bid=0.01, bid_qty=1500, run="r2"), book_row("updown", 700, bid=0.01, bid_qty=10, run="r2")],
              [market_row("far", 78_000, run="r2", first_seen=END - 700), market_row("updown", "", run="r2", price_to_beat=77_000.0, first_seen=END - 700, **up)],
              [{"run": "r2", "ts": END - 750, "coin": "btc", "level": 74_050.0, "at": END - 800, "slug": "five-b"}])
    b, m, i = score.load(tmp_path)
    assert len(m) == 2 and m.set_index("slug").loc["updown", "price_to_beat"] == 77_000.0
    trades, fate = score.apply(b, m, i, REACH)
    assert sorted(t["slug"] for t in trades) == ["far", "updown"] and all(t["left"] == 700 and t["level"] == 74_050.0 for t in trades)


def test_settlements_are_remembered_and_only_asked_for_when_told_to(tmp_path):
    (tmp_path / "settlements.csv").write_text("slug,settle,checked\nfar,0.0,1\npending,,1\n")
    s = score.settlements(tmp_path, ["far", "pending", "new"], look_up=False)
    assert s.to_dict() == {"far": 0.0}
