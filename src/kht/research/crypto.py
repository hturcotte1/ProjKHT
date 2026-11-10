"""Crypto price markets: read the question, and work out what the bet is worth.

A market such as "Will the price of Bitcoin be above $70,000 on May 10?" or
"Will Ethereum dip to $2,200 in December?" has something most prediction
markets lack: an outside price. The distance to the target, the time left and
how much the coin moves give a probability that owes nothing to Polymarket's
own crowd. This module parses the question and computes that probability
under the textbook assumption (a driftless lognormal walk). The assumption is
known to be too thin in the tails, so the output is a *yardstick* to be
checked against outcomes and recalibrated, not a forecast to be believed.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np
from scipy.special import ndtr

COINS = {
    "bitcoin": "bitcoin", "btc": "bitcoin", "ethereum": "ethereum", "eth": "ethereum", "ether": "ethereum",
    "solana": "solana", "sol": "solana", "xrp": "xrp", "ripple": "xrp", "dogecoin": "dogecoin", "doge": "dogecoin",
    "bnb": "bnb",
}
_COIN = r"\$?(bitcoin|btc|ethereum|ether|eth|solana|sol|xrp|ripple|dogecoin|doge|bnb)"
_NUM = r"\$?\s?([0-9][0-9,]*(?:\.[0-9]+)?)\s?([kmb])?\b"
# questions that mention a price but are a different kind of bet
_NOT_A_PRICE_BET = re.compile(r"\bfirst\b|\bfdv\b|\betf\b|market cap|dominance|volatility index|all[- ]time high|\bath\b|"
                              r"microstrategy|\bflip\b|\bratio\b|\b(?:eth|sol|btc)/(?:btc|eth|usd)\b|up or down")

_PATTERNS = [
    ("between", re.compile(rf"^will the price of {_COIN} be between {_NUM} and {_NUM} on ")),
    ("above", re.compile(rf"^(?:will )?(?:the price of )?{_COIN} (?:be |close )?(?:above|greater than) {_NUM} on ")),
    ("below", re.compile(rf"^(?:will )?(?:the price of )?{_COIN} (?:be |close )?(?:below|less than) {_NUM} on ")),
    ("reach", re.compile(rf"^will {_COIN} (?:reach|hit) {_NUM}")),
    ("dip", re.compile(rf"^will {_COIN} (?:dip to|dip below|fall to|drop to) {_NUM}")),
]
_SCALE = {None: 1.0, "k": 1e3, "m": 1e6, "b": 1e9}


@dataclass(frozen=True)
class PriceQuestion:
    coin: str                       # bitcoin, ethereum, solana, xrp, dogecoin, bnb
    kind: str                       # above | below | between: the price at the end.  reach | dip: touched at any time
    strike: float
    strike_hi: float | None = None  # upper edge, for "between"


def _number(text: str, suffix: str | None) -> float:
    return float(text.replace(",", "")) * _SCALE[suffix]


def parse_question(question: str) -> PriceQuestion | None:
    """The bet a crypto price question describes, or None if it is some other kind of question."""
    q = " ".join(question.lower().replace("–", "-").split())
    if _NOT_A_PRICE_BET.search(q):
        return None
    for kind, pattern in _PATTERNS:
        m = pattern.match(q)
        if not m:
            continue
        coin = COINS[m.group(1)]
        if kind == "between":
            lo, hi = _number(m.group(2), m.group(3)), _number(m.group(4), m.group(5))
            if not 0 < lo < hi:
                return None
            return PriceQuestion(coin, kind, lo, hi)
        strike = _number(m.group(2), m.group(3))
        return PriceQuestion(coin, kind, strike) if strike > 0 else None
    return None


# --------------------------------------------------------------- the yardstick
def prob_above(spot, strike, sigma, years):
    """P(price at the end > strike) for a driftless lognormal walk. Arrays broadcast."""
    spot, strike, sigma, years = (np.asarray(x, dtype=float) for x in (spot, strike, sigma, years))
    vol = np.maximum(sigma * np.sqrt(np.maximum(years, 0.0)), 1e-12)
    return ndtr((np.log(spot / strike) - 0.5 * vol ** 2) / vol)


def prob_between(spot, lo, hi, sigma, years):
    return np.clip(prob_above(spot, lo, sigma, years) - prob_above(spot, hi, sigma, years), 0.0, 1.0)


def prob_touch(spot, barrier, sigma, years):
    """P(the price touches ``barrier`` at some time before the end), driftless lognormal walk.

    Works for a barrier on either side of the spot price; a barrier already
    reached gives 1. The formula is the reflection principle with the drift
    of the log price (minus half the variance) put back in.
    """
    spot, barrier, sigma, years = (np.asarray(x, dtype=float) for x in (spot, barrier, sigma, years))
    vol = np.maximum(sigma * np.sqrt(np.maximum(years, 0.0)), 1e-12)
    up = barrier >= spot
    b = np.abs(np.log(barrier / spot))                       # distance in log price, always >= 0
    half = 0.5 * vol ** 2
    # up: drift of the log price is -half;  down: drift of minus the log price is +half
    drift = np.where(up, -half, half)
    ratio = np.where(up, spot / barrier, spot / barrier)     # exp(2 * drift * b / vol^2) in both cases
    p = ndtr((-b + drift) / vol) + ratio * ndtr((-b - drift) / vol)
    return np.clip(np.where(b <= 0, 1.0, p), 0.0, 1.0)


def prob_yes(kind: str, spot, strike, sigma, years, strike_hi=None):
    """Model probability that the question resolves Yes, given the bet's kind."""
    if kind == "above":
        return prob_above(spot, strike, sigma, years)
    if kind == "below":
        return 1.0 - prob_above(spot, strike, sigma, years)
    if kind == "between":
        return prob_between(spot, strike, strike_hi, sigma, years)
    if kind in ("reach", "dip"):
        return prob_touch(spot, strike, sigma, years)
    raise ValueError(f"unknown kind {kind!r}")


def sigmas_away(spot, strike, sigma, years):
    """Distance from the spot price to the strike in units of the move expected over the time left."""
    spot, strike, sigma, years = (np.asarray(x, dtype=float) for x in (spot, strike, sigma, years))
    vol = np.maximum(sigma * np.sqrt(np.maximum(years, 0.0)), 1e-12)
    return np.log(strike / spot) / vol


HOURS_PER_YEAR = 24 * 365.0


def realised_vol(close: np.ndarray, halflife_hours: float = 24 * 14) -> np.ndarray:
    """Annualised volatility from hourly closes, exponentially weighted, using
    returns up to and including each hour (nothing later)."""
    r = np.diff(np.log(close), prepend=np.log(close[0]))
    alpha = 1.0 - math.exp(-math.log(2.0) / halflife_hours)
    var = np.empty_like(r)
    acc = float(np.mean(r[1:200] ** 2)) if len(r) > 200 else float(np.mean(r ** 2))
    for i, x in enumerate(r):
        acc = (1.0 - alpha) * acc + alpha * x * x
        var[i] = acc
    return np.sqrt(var * HOURS_PER_YEAR)
