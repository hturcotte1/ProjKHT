"""Crypto price questions: parsing and the lognormal yardstick."""

import math

import numpy as np
import pytest

pytest.importorskip("scipy")

from kht.research.crypto import (PriceQuestion, parse_question, prob_above, prob_between, prob_touch, prob_yes,  # noqa: E402
                                 realised_vol, sigmas_away)


@pytest.mark.parametrize("question, expected", [
    ("Will the price of Bitcoin be above $62,000 on February 23?", PriceQuestion("bitcoin", "above", 62_000.0)),
    ("Bitcoin above $124000 on August 15?", PriceQuestion("bitcoin", "above", 124_000.0)),
    ("Will the price of Ethereum be greater than $3,600 on January 18?", PriceQuestion("ethereum", "above", 3_600.0)),
    ("Will the price of Solana be less than $150 on March 3?", PriceQuestion("solana", "below", 150.0)),
    ("Will the price of Bitcoin be between $102K and $104K on June 13?", PriceQuestion("bitcoin", "between", 102_000.0, 104_000.0)),
    ("Will the price of Ethereum be between $3,100 and $3,200 on December 31?", PriceQuestion("ethereum", "between", 3_100.0, 3_200.0)),
    ("Will Bitcoin reach $100,000 January 5-11?", PriceQuestion("bitcoin", "reach", 100_000.0)),
    ("Will Solana reach $240 September 8–14?", PriceQuestion("solana", "reach", 240.0)),
    ("Will Bitcoin dip to $50,000 in August?", PriceQuestion("bitcoin", "dip", 50_000.0)),
    ("Will Ethereum dip to $2,200 in December?", PriceQuestion("ethereum", "dip", 2_200.0)),
    ("Will XRP hit $3.50 by March 31, 2026?", PriceQuestion("xrp", "reach", 3.5)),
    ("Will Bitcoin reach $1M before 2027?", PriceQuestion("bitcoin", "reach", 1_000_000.0)),
    ("Will Dogecoin reach $0.25 in May?", PriceQuestion("dogecoin", "reach", 0.25)),
])
def test_price_questions_are_read(question, expected):
    assert parse_question(question) == expected


@pytest.mark.parametrize("question", [
    "Will Bitcoin hit $80k or $100k first?",
    "Lighter FDV above $2B one day after launch?",
    "Solana ETF approved by July 31?",
    "Bitcoin Up or Down - November 10, 5PM ET",
    "Will Bitcoin reach a new all time high in 2026?",
    "Will MicroStrategy sell any Bitcoin in 2025?",
    "Will the Bitcoin Volatility Index dip to 40 by June 30?",
    "Will Trump say Bitcoin during his speech?",
])
def test_other_questions_are_left_alone(question):
    assert parse_question(question) is None


def test_above_is_a_half_at_the_money_and_moves_the_right_way():
    assert prob_above(100, 100, 0.5, 1e-9) == pytest.approx(0.5, abs=1e-3)
    assert prob_above(110, 100, 0.5, 7 / 365) > 0.9
    assert prob_above(90, 100, 0.5, 7 / 365) < 0.1
    # more time or more volatility pulls a likely outcome back towards even odds
    assert prob_above(110, 100, 0.5, 30 / 365) < prob_above(110, 100, 0.5, 7 / 365)
    assert prob_above(110, 100, 1.0, 7 / 365) < prob_above(110, 100, 0.5, 7 / 365)


def test_between_is_the_difference_of_two_aboves():
    p = prob_between(100, 95, 105, 0.6, 7 / 365)
    assert p == pytest.approx(prob_above(100, 95, 0.6, 7 / 365) - prob_above(100, 105, 0.6, 7 / 365))
    assert 0 < p < 1


def test_touch_matches_a_simulation():
    rng = np.random.default_rng(3)
    sigma, years, steps, paths = 0.6, 30 / 365, 2_000, 20_000
    dt = years / steps
    steps_ = rng.standard_normal((paths, steps)) * sigma * math.sqrt(dt) - 0.5 * sigma ** 2 * dt
    log_path = np.cumsum(steps_, axis=1)
    for barrier in (1.10, 1.25, 0.90, 0.80):
        hit = (log_path.max(axis=1) >= math.log(barrier)) if barrier > 1 else (log_path.min(axis=1) <= math.log(barrier))
        model = float(prob_touch(1.0, barrier, sigma, years))
        # a path watched at 2,000 points touches slightly less often than one watched continuously
        assert hit.mean() == pytest.approx(model, abs=0.02), barrier
        assert hit.mean() <= model + 0.005


def test_touch_edge_cases():
    assert float(prob_touch(100, 100, 0.5, 0.1)) == 1.0                  # already there
    assert float(prob_touch(100, 300, 0.5, 1 / 365)) < 1e-6              # far away, no time
    assert float(prob_touch(100, 110, 0.5, 0.1)) > float(prob_above(100, 110, 0.5, 0.1))   # touching is easier than ending above
    assert float(prob_touch(100, 90, 0.5, 0.1)) > 1.0 - float(prob_above(100, 90, 0.5, 0.1))


def test_prob_yes_dispatches_and_rejects_unknown_kinds():
    assert float(prob_yes("below", 100, 90, 0.5, 0.1)) == pytest.approx(1 - float(prob_above(100, 90, 0.5, 0.1)))
    assert float(prob_yes("dip", 100, 90, 0.5, 0.1)) == pytest.approx(float(prob_touch(100, 90, 0.5, 0.1)))
    with pytest.raises(ValueError):
        prob_yes("sideways", 100, 90, 0.5, 0.1)


def test_sigmas_away_is_signed():
    assert float(sigmas_away(100, 110, 0.5, 0.1)) > 0 > float(sigmas_away(100, 90, 0.5, 0.1))


def test_realised_vol_recovers_a_known_volatility_and_uses_no_future():
    rng = np.random.default_rng(1)
    true = 0.60
    r = rng.standard_normal(20_000) * true / math.sqrt(24 * 365)
    close = 100 * np.exp(np.cumsum(r))
    est = realised_vol(close)
    assert est[5_000:].mean() == pytest.approx(true, rel=0.05)
    bumped = close.copy()
    bumped[10_000:] *= 1.5                                  # a jump later on
    assert np.allclose(realised_vol(bumped)[:10_000], est[:10_000])
