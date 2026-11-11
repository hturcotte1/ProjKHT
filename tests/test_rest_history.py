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
