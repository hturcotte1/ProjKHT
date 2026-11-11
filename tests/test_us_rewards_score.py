"""The scoring of the paper orders before games (scripts/us_rewards_score.py, docs/09 section 5)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from kht.trading.us_rewards import GAME_FIELDS, GRID, HIT_FIELDS, PULL, WINDOW

spec = importlib.util.spec_from_file_location("us_rewards_score", Path(__file__).resolve().parents[1] / "scripts" / "us_rewards_score.py")
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)

START = 1_794_400_000          # a game that started long before `NOW`
NOW = START + 3 * 86_400
FULL = WINDOW - PULL             # the most a game can be watched: its six hours less the last ten minutes
PART = FULL / WINDOW            # so the most of its pool that can be earned


def game_row(slug, date="2026-11-11", run="r1", program="itf_moneyline_dayof_1", pool=12.0, n=1, share_bid=0.5, share_ask=0.25, seconds=FULL, start=START, last_ts=None, mid=0.5):
    row = dict.fromkeys(GAME_FIELDS, 0.0)
    row.update({"run": run, "slug": slug, "date": date, "program": program, "pool": pool, "markets_in_event": n, "target": 7500, "discount": 0.35, "max_spread": np.nan,
                "start": start, "first_ts": start - WINDOW, "last_ts": last_ts or start - 600, "polls": 10, "obs_s": seconds, "quote_s": seconds, "cap_s": seconds * 0.98,
                "mid_first": mid, "mid_last": mid, "state_last": "MARKET_STATE_OPEN"})
    for x in GRID:
        row[f"acc_bid_{x}"] = seconds * share_bid
        row[f"acc_ask_{x}"] = seconds * share_ask
    return row


def hit_row(slug, side, px, dv, t1, cross_qty=np.nan, program="itf_moneyline_dayof_1"):
    row = dict.fromkeys(HIT_FIELDS, np.nan)
    row.update({"run": "r1", "slug": slug, "program": program, "start": START, "t0": t1 - 120, "t1": t1, "side": side, "px": px, "dv": dv, "cross_qty": cross_qty, "crossed": 0, "mid1": px})
    return row


def test_reward_follows_the_formula_and_the_dollar_minimum():
    g = pd.DataFrame([game_row("a"),                                                    # half of one side, a quarter of the other, all six hours
                      game_row("b", share_bid=0.05, share_ask=0.05),                    # a twentieth of each side: 60 cents, under the minimum
                      game_row("c", date="2026-11-10", seconds=FULL / 2, share_bid=0.3, share_ask=0.0),     # split across two US dates,
                      game_row("c", date="2026-11-11", seconds=FULL / 2, share_bid=0.3, share_ask=0.0)])    # each part under a dollar
    d, facts = score.per_game_day(g), score.game_facts(g)
    per, _ = score.account(d, facts, pd.DataFrame(), pd.Series({"a": 1.0, "b": 0.0, "c": 1.0}), 100, NOW)
    per = per.set_index("slug")
    assert per.loc["a", "reward_formula"] == pytest.approx(12.0 * (0.5 + 0.25) / 2 * PART) and per.loc["a", "reward_paid"] == pytest.approx(4.5 * PART)
    assert per.loc["b", "reward_formula"] == pytest.approx(0.6 * PART) and per.loc["b", "reward_paid"] == 0.0
    assert per.loc["c", "reward_formula"] == pytest.approx(1.8 * PART) and per.loc["c", "reward_paid"] == 0.0   # under 90 cents on each date
    assert per.loc["a", "net"] == pytest.approx(4.5 * PART) and bool(per.loc["a", "over"])


def test_runs_are_added_together_and_a_shared_pool_is_split():
    g = pd.DataFrame([game_row("a", run="r1", seconds=FULL / 2, last_ts=START - 12_000), game_row("a", run="r2", seconds=FULL / 2, last_ts=START - 600, mid=0.6),
                      game_row("t", program="table_tennis_moneyline_day_of_1", pool=5.0, n=3)])
    d, facts = score.per_game_day(g), score.game_facts(g)
    assert len(d) == 2 and d.set_index("slug").loc["a", "obs_s"] == pytest.approx(FULL)
    assert facts.loc["a", "mid_pull"] == 0.6                                             # from the run that watched it last
    per, _ = score.account(d, facts, pd.DataFrame(), pd.Series({"a": 1.0, "t": 0.0}), 100, NOW)
    per = per.set_index("slug")
    assert per.loc["a", "reward_formula"] == pytest.approx(4.5 * PART)
    assert per.loc["t", "reward_formula"] == pytest.approx(5.0 / 3 * 0.75 / 2 * PART)


def test_fills_are_capped_valued_at_settlement_and_cost_the_side_its_reward():
    g = pd.DataFrame([game_row("a"), game_row("b"), game_row("off")])
    h = pd.DataFrame([hit_row("a", "bid", 0.40, 60.0, START - 5000), hit_row("a", "bid", 0.38, 70.0, START - 4000), hit_row("a", "bid", 0.30, 500.0, START - 3000),
                      hit_row("b", "ask", 0.70, 0.0, START - 4000, cross_qty=30.0), hit_row("off", "bid", 0.45, 20.0, START - 4000)])
    f = score.fills(h, 100)
    assert f[f.slug == "a"]["qty"].tolist() == [60.0, 40.0]                              # a side is filled 100 at most, in the order it happened
    d, facts = score.per_game_day(g), score.game_facts(g)
    per, f = score.account(d, facts, h, pd.Series({"a": 1.0, "b": 1.0, "off": 0.5}), 100, NOW)
    per = per.set_index("slug")
    assert per.loc["a", "pnl_settle"] == pytest.approx(60 * 0.60 + 40 * 0.62)
    assert per.loc["a", "reward_formula"] == pytest.approx(12.0 * 0.25 / 2 * PART)       # the bid was filled whole: only the offer earns
    assert per.loc["b", "pnl_settle"] == pytest.approx(30 * (0.70 - 1.0)) and per.loc["b", "reward_formula"] == pytest.approx(4.5 * PART)
    assert per.loc["b", "pnl_mid"] == pytest.approx(30 * (0.70 - 0.5))
    assert per.loc["off", "reward_formula"] == 0.0 and bool(per.loc["off", "called_off"])  # a game called off earns nothing
    assert per.loc["off", "pnl_settle"] == pytest.approx(20 * (0.5 - 0.45))
    assert per.loc["a", "net"] == pytest.approx(1.5 * PART + 60.8)


def test_a_fill_without_a_settlement_leaves_the_game_unjudged():
    g = pd.DataFrame([game_row("a")])
    h = pd.DataFrame([hit_row("a", "bid", 0.40, 60.0, START - 5000)])
    per, _ = score.account(score.per_game_day(g), score.game_facts(g), h, pd.Series(dtype=float), 100, NOW)
    assert np.isnan(per.loc[0, "net"]) and per.loc[0, "filled"] == 60.0


def test_clustered_z_counts_a_group_once():
    values = np.array([1.0, 1.0, 1.0, 1.0, -1.0, -1.0, 3.0, 3.0])
    mean, z, k = score.clustered_z(values, np.array(["a", "a", "a", "a", "b", "b", "c", "c"]))
    assert mean == pytest.approx(1.0) and k == 3
    sums = np.array([0.0, -4.0, 4.0])                                                    # each group's sum of deviations from the mean
    assert z == pytest.approx(1.0 / np.sqrt(3 / 2 * (sums**2).sum() / 64))
    assert np.isnan(score.clustered_z(values, np.array(["a"] * 8))[1])                   # one group says nothing about its own spread


def test_the_filed_wording_gives_the_same_when_both_sides_are_always_paid_and_more_when_they_are_not():
    full = game_row("a")
    for col in ("paid_bid_s", "paid_ask_s", "paid_bid_alone_s", "paid_ask_alone_s"):
        full[col] = FULL                                                                 # both sides paid for every second watched
    half = game_row("b")
    for col in ("paid_bid_s", "paid_bid_alone_s"):
        half[col] = FULL                                                                 # the bid always, the offer never
    half.update({f"acc_ask_{x}": 0.0 for x in GRID})
    spread = dict(game_row("c"), max_spread=0.07)                                        # with a maximum spread the two readings are one
    for col in ("paid_bid_s", "paid_ask_s"):
        spread[col] = FULL / 2
    g = pd.DataFrame([full, half, spread])
    per, _ = score.account(score.per_game_day(g), score.game_facts(g), pd.DataFrame(), pd.Series({"a": 1.0, "b": 0.0, "c": 1.0}), 100, NOW)
    per = per.set_index("slug")
    assert per.loc["a", "reward_rule"] == pytest.approx(per.loc["a", "reward_formula"])
    assert per.loc["b", "reward_formula"] == pytest.approx(12.0 * 0.5 / 2 * PART)        # a fixed slice a second: half of one side's half
    assert per.loc["b", "reward_rule"] == pytest.approx(12.0 * 0.5 * PART)               # the whole pool goes to the side that is paid
    assert per.loc["c", "reward_rule"] == pytest.approx(per.loc["c", "reward_formula"])


def test_seconds_watched_twice_are_not_counted_twice():
    g = pd.DataFrame([game_row("a", run="r1"), game_row("a", run="r2")])                 # two runs that somehow watched the same six hours
    d = score.per_game_day(g)
    assert d.loc[0, "obs_s"] == pytest.approx(FULL) and d.loc[0, "acc_bid_100"] == pytest.approx(FULL * 0.5)
