"""Polymarket trading fees (https://docs.polymarket.com/trading/fees).

    fee_usdc = shares * rate * (p * (1 - p)) ** exponent      (takers only)

Makers pay nothing. ``rate`` and ``exponent`` come from each market's
``feeSchedule``; they differ by category and have changed over time, so they
are always read per market rather than assumed. Maker rebates exist but are a
bonus paid daily out of a pool; they are deliberately ignored everywhere in
this code base so that results are conservative.
"""

from __future__ import annotations

FEE_DECIMALS = 5


def taker_fee(shares: float, price: float, rate: float, exponent: float = 1.0) -> float:
    """Fee in USDC for a taker fill of ``shares`` at ``price``."""
    if shares <= 0 or rate <= 0 or not (0.0 < price < 1.0):
        return 0.0
    fee = shares * rate * (price * (1.0 - price)) ** exponent
    return round(fee, FEE_DECIMALS)


def taker_fee_per_share(price: float, rate: float, exponent: float = 1.0) -> float:
    if rate <= 0 or not (0.0 < price < 1.0):
        return 0.0
    return rate * (price * (1.0 - price)) ** exponent
