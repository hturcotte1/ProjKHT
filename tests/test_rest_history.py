"""The measure of being run over before past games (scripts/rest_history.py, docs/09 section 4)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location("rest_history", Path(__file__).resolve().parents[1] / "scripts" / "rest_history.py")
rh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rh)

START = 1_794_400_000.0
MINUTES = np.arange(START - rh.WINDOW - 300, START + 1, 60.0)          # one stored price a minute


def path(bid: float, ask: float):
    return np.full(len(MINUTES), ask), np.full(len(MINUTES), 1.0 - bid)  # the feed stores the ask of "Yes" and the ask of "No"


def test_a_book_that_stands_still_is_rested_in_and_never_filled():
    yes, no = path(0.45, 0.47)
    out = rh.simulate(MINUTES, yes, no, START, 0.01)
    assert out["quoted"] == out["readings"] == 176 and out["blind"] == 0      # every two minutes from six hours to ten minutes before
    assert np.isnan(out["bid_px"]) and np.isnan(out["ask_px"]) and out["mid_last"] == pytest.approx(0.46)


def test_a_market_that_falls_through_the_bid_fills_it_at_the_bid():
    yes, no = path(0.45, 0.47)
    drop = MINUTES >= START - 3600                                            # an hour before the start the book moves to 41 / 43
    yes[drop], no[drop] = 0.43, 1.0 - 0.41
    out = rh.simulate(MINUTES, yes, no, START, 0.01)
    assert out["bid_px"] == pytest.approx(0.45) and out["bid_lead"] == pytest.approx(3600.0) and np.isnan(out["ask_px"])
    assert out["mid_last"] == pytest.approx(0.42)


def test_a_market_that_rises_through_the_offer_fills_it_and_a_touch_counts():
    yes, no = path(0.45, 0.47)
    up = MINUTES >= START - 7200
    yes[up], no[up] = 0.49, 1.0 - 0.47                                        # the new bid stands exactly at our offer
    out = rh.simulate(MINUTES, yes, no, START, 0.01)
    assert out["ask_px"] == pytest.approx(0.47) and out["ask_lead"] == pytest.approx(7200.0) and np.isnan(out["bid_px"])


def test_a_wide_book_is_not_rested_in_and_an_unreadable_next_reading_fills_nothing():
    yes, no = path(0.30, 0.45)                                                # fifteen cents wide
    out = rh.simulate(MINUTES, yes, no, START, 0.01)
    assert out["quoted"] == 0 and out["readings"] == 176
    yes, no = path(0.45, 0.47)
    gone = MINUTES >= START - 3600                                            # one side empties and the feed shows a last trade in its place
    yes[gone], no[gone] = 0.40, 1.0 - 0.40                                    # zero wide: not a real book
    out = rh.simulate(MINUTES, yes, no, START, 0.01)
    assert np.isnan(out["bid_px"]) and out["blind"] == 1 and out["quoted"] == 150


def test_no_stored_prices_means_nothing_rested():
    out = rh.simulate(np.array([]), np.array([]), np.array([]), START, 0.01)
    assert out["quoted"] == 0 and np.isnan(out["mid_last"])
    old = np.array([START - rh.WINDOW - 4000.0])                              # one price, far too old to use
    assert rh.simulate(old, np.array([0.47]), np.array([0.55]), START, 0.01)["readings"] == 0


def test_the_whole_run_on_made_up_games(tmp_path, monkeypatch, capsys):
    import argparse

    import pandas as pd

    sp, out = tmp_path / "us_sports", tmp_path / "reports"
    (sp / "paths").mkdir(parents=True)
    out.mkdir()
    day = 86_400.0
    starts = {"aec-itfme-a-b-2026-10-01": START - 30 * day, "aec-itfme-c-d-2026-10-02": START - 29 * day, "aec-utr-e-f-2026-10-03": START - 28 * day}
    settle = {"aec-itfme-a-b-2026-10-01": 0.0, "aec-itfme-c-d-2026-10-02": 1.0, "aec-utr-e-f-2026-10-03": 1.0}
    pd.DataFrame([{"market_id": i, "slug": s, "market_type": "moneyline", "game_start_ts": starts[s], "yes_settle": settle[s], "tick": 0.01}
                  for i, s in enumerate(starts)]).to_parquet(sp / "markets_sports.parquet", index=False)
    rows = []
    for slug, start in starts.items():
        minutes = np.arange(start - rh.WINDOW - 300, start + 1, 60.0)
        yes, no = np.full(len(minutes), 0.47), np.full(len(minutes), 0.55)
        if slug.startswith("aec-itfme-a"):                    # the market falls through the bid an hour before, and "Yes" then loses
            late = minutes >= start - 3600
            yes[late], no[late] = 0.43, 1.0 - 0.41
        rows.append({"slug": slug, "ts": minutes.astype(np.int64), "yes": yes.astype(np.float32), "no": no.astype(np.float32)})
    pd.DataFrame(rows).to_parquet(sp / "paths" / "p_0of1_0_0.parquet", index=False)
    monkeypatch.setattr(rh, "SP", sp)
    monkeypatch.setattr(rh, "OUT", out)
    monkeypatch.setattr(rh, "LAST", START)
    rh.cmd_run(argparse.Namespace())
    t = pd.read_csv(out / "rh_by_programme.csv").set_index("programme")
    assert t.loc["all", "games"] == 3 and t.loc["ITF", "games"] == 2 and t.loc["UTR", "games"] == 1
    assert t.loc["ITF", "games_filled_pct"] == pytest.approx(50.0)
    assert t.loc["ITF", "dollars_a_game"] == pytest.approx(-45.0 / 2)             # 100 contracts bought at 45c that paid nothing, over two games
    assert t.loc["ITF", "cents_a_filled_contract"] == pytest.approx(-45.0)
    assert t.loc["ITF", "dollars_a_game_at_last_mid"] == pytest.approx(100 * (0.42 - 0.45) / 2)
    assert t.loc["UTR", "dollars_a_game"] == 0.0
    assert "hours before the start" in (out / "rest_history_output.txt").read_text()
