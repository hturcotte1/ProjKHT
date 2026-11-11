"""The search over up-or-down crypto markets (scripts/crypto_updown.py, docs/11 section 7)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location("crypto_updown", Path(__file__).resolve().parents[1] / "scripts" / "crypto_updown.py")
ud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ud)

W0 = float(pd.Timestamp("2026-10-25 16:25:00").timestamp())


def five(yes_settle=1.0, w0=W0, coin="btc"):
    return {"slug": f"{coin}-{int(w0)}", "coin": coin, "length": "5m", "w0": w0, "w1": w0 + 300, "yes_settle": yes_settle}


def path(w0, books):
    """Stored points of a window: books[k] is the book k minutes after its start, stored under the label a minute earlier."""
    return {int(w0 + 60 * k - 60): b for k, b in books.items()}


def test_the_window_is_read_from_the_name():
    got = ud.SLUG.match("cpc-btc-updown-5m-2026-11-11-1625z")
    assert got.groups() == ("btc", "5m", "2026-11-11", "16", "25")
    assert ud.SLUG.match("cpcxrp-xrp-updown-15m-2026-11-12-0445z").group(1) == "xrp"
    assert ud.SLUG.match("cpc-btc-updown-1d-2026-11-10-2200z") is None and ud.SLUG.match("cpc-btc-above-hr-2026-11-11-1700z-74000") is None


def test_a_book_is_the_point_stored_a_minute_earlier_and_must_be_real():
    pts = path(W0, {1: (0.68, 0.33), 2: (0.97, 0.04), 3: (1.0, 0.0), 4: (0.50, 0.50), 5: (0.70, 0.45)})
    assert ud.book_at(pts, W0 + 60) == (0.68, 0.33)
    assert ud.book_at(pts, W0 + 120) == (0.97, 0.04)
    assert ud.book_at(pts, W0 + 180) is None                      # nobody offering "Up" at any price
    assert ud.book_at(pts, W0 + 240) is None                      # no spread: not a book
    assert ud.book_at(pts, W0 + 300) is None                      # 15c wide: not a book this test uses
    assert ud.book_at(pts, W0 + 30) is None


def test_rows_for_one_market():
    # "Up" dearer after one and two minutes, "Down" after three, then "Up" at 97c with a minute to go; it ended "Up"
    pts = path(W0, {1: (0.68, 0.33), 2: (0.61, 0.40), 3: (0.42, 0.59), 4: (0.97, 0.04)})
    rows = pd.DataFrame(ud.rows_for(five(1.0), pts, prev=0.0))
    assert sorted(rows["left"].unique()) == [1, 2, 3, 4] and len(rows) == 8
    r = rows.set_index(["left", "side"])
    assert r.loc[(4, 0), "ask"] == 0.68 and r.loc[(4, 1), "ask"] == 0.33 and r.loc[(4, 0), "spread"] == pytest.approx(0.01)
    assert r.loc[(4, 0), "fair"] == pytest.approx(0.675) and r.loc[(4, 1), "fair"] == pytest.approx(0.325)
    assert r.loc[(1, 0), "won"] == 1.0 and r.loc[(1, 1), "won"] == 0.0
    assert not r.loc[(4, 0), "led"] and not r.loc[(4, 0), "not_led"]            # the first minute has nothing before it
    assert r.loc[(3, 0), "led"] and r.loc[(3, 1), "not_led"]                    # after one minute "Up" had been dearer
    assert r.loc[(2, 0), "led"] and not r.loc[(2, 1), "led"]
    assert not r.loc[(1, 0), "led"] and r.loc[(1, 0), "not_led"] and r.loc[(1, 1), "not_led"]     # by then each side had been the dearer one once
    assert r.loc[(1, 1), "prev_same"] and r.loc[(1, 0), "prev_other"] and not r.loc[(1, 0), "prev_same"]   # the window before ended "Down"
    none = pd.DataFrame(ud.rows_for(five(1.0), pts, prev=None))
    assert not none["prev_same"].any() and not none["prev_other"].any()
    assert rows["hour"].nunique() == 1 and rows["split"].eq(0).all() and rows["slot"].eq(f"5m-{int(W0 + 300)}").all()
    late = pd.DataFrame(ud.rows_for(five(1.0, w0=float(pd.Timestamp("2026-11-05 10:00").timestamp())), path(float(pd.Timestamp("2026-11-05 10:00").timestamp()), {4: (0.97, 0.04)}), None))
    assert late["split"].eq(1).all() and list(late["left"].unique()) == [1]


def table(n=4000, seed=3, edge=0.0):
    """Purchases at 95c on a side that wins 95% of the time plus ``edge``."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        w0 = W0 + 300 * (i // 2) + (86400 * 12 if i >= n * 0.7 else 0)
        up = rng.random() < 0.95 + edge
        rows.append({"slug": f"m{i}", "coin": "btc" if i % 2 else "eth", "length": "5m", "left": 1, "side": 0, "ask": 0.95, "spread": 0.01, "fair": 0.945, "won": float(up),
                     "prev_same": bool(i % 3 == 0), "prev_other": bool(i % 3 == 1), "led": True, "not_led": False, "hour": np.floor((w0 + 300) / 3600),
                     "slot": f"5m-{int(w0 + 300)}", "split": 0 if w0 + 300 < ud.SPLIT else 1})
    return pd.DataFrame(rows)


def test_a_fair_price_makes_no_candidate_and_a_real_edge_does():
    fair = {("5m", 1): ud.UpDown(table())}
    res = ud.evaluate(fair)
    assert len(res) > 0 and not ud.fx.screen(res).any()
    top = res.loc[res["rule"] == "5m|1m left|all|up|90-95c|spread any|none"].iloc[0]
    assert top["n_d"] + top["n_v"] == 4000 and top["cost_d"] == pytest.approx(0.95 + 0.095 * 0.95 * 0.05)
    assert top["ret_d"] < 0.004                                                 # the fee and half the spread are lost, give or take luck
    rich = {("5m", 1): ud.UpDown(table(edge=0.045))}
    res = ud.evaluate(rich)
    assert ud.fx.screen(res).any()
    assert res.loc[ud.fx.screen(res), "rule"].str.contains("up").all()


def test_placebo_results_follow_the_prices_and_coins_in_one_window_move_together():
    t = ud.UpDown(table(n=6000))
    won = t.placebo(np.random.default_rng(1))
    assert abs(won.mean() - 0.945) < 0.01
    slot = pd.Series(won).groupby(t.slot).nunique()
    assert slot.max() == 1                                                       # the two coins of a window always share its draw at equal prices


def test_markets_in_scope_and_their_windows(tmp_path, monkeypatch):
    rows = [("cpc-btc-updown-5m-2026-11-02-2355z", 1.0), ("cpceth-eth-updown-15m-2026-11-10-2330z", 0.0), ("cpc-btc-updown-1h-2026-11-10-2200z", 1.0),
            ("cpc-btc-updown-1h-2026-11-10-2300z", 1.0),              # ends at midnight: not "by 23:59 on 10 November"
            ("cpc-btc-updown-5m-2026-11-05-0000z", None),             # not settled
            ("cpc-btc-updown-1d-2026-11-05-2200z", 1.0), ("cpc-btc-above-day-2026-11-05-70000", 1.0), ("cpc-btc-updown-5m-2026-11-05-0005z", 0.5)]
    pd.DataFrame(rows, columns=["slug", "yes_settle"]).to_parquet(tmp_path / "markets_crypto.parquet", index=False)
    monkeypatch.setattr(ud, "DATA", tmp_path)
    m = ud.markets().set_index("slug")
    assert set(m.index) == {"cpc-btc-updown-5m-2026-11-02-2355z", "cpceth-eth-updown-15m-2026-11-10-2330z", "cpc-btc-updown-1h-2026-11-10-2200z"}
    five = m.loc["cpc-btc-updown-5m-2026-11-02-2355z"]
    assert five["w0"] == pd.Timestamp("2026-11-02 23:55").timestamp() and five["w1"] == ud.SPLIT and five["coin"] == "btc" and five["length"] == "5m"
    quarter = m.loc["cpceth-eth-updown-15m-2026-11-10-2330z"]
    assert quarter["w1"] == pd.Timestamp("2026-11-10 23:45").timestamp() and quarter["coin"] == "eth"
    assert m.loc["cpc-btc-updown-1h-2026-11-10-2200z", "w1"] - m.loc["cpc-btc-updown-1h-2026-11-10-2200z", "w0"] == 3600
