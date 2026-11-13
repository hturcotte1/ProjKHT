"""How far a coin's price has stood from where it was, hours later: the yardstick of test L3.

docs/11_crypto_us.md, section 13, "Far enough":

    From one-minute prices of each coin since 1 January 2020, for a horizon
    of h minutes: take every minute as a start and measure how far the
    price stood from there h minutes later, close to close. For each
    calendar year take the distance that only one start in 500 ended
    beyond. The reach for that coin and horizon is the largest of those
    yearly figures, never less than 1%, and never less than the reach of a
    shorter horizon.

    python scripts/lasthours_reach.py      # -> config/lasthours_reach.json, reports/research/lhr_*

This is not the yardstick of L1. That one measures the furthest the price
went on the way, one start in 5,000, because a level that is touched can
cost a hundred sales. A bracket pays on where the price ends, and of all
the brackets sold in one ladder at most one can pay.

The brake is L1's own, read from config/lasttick_reach.json and copied.
Prices: data/crypto/minute_<coin>.parquet (scripts/lasttick_reach.py fetch).
This uses no Polymarket data at all.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
CONFIG = ROOT / "config" / "lasthours_reach.json"
L1_CONFIG = ROOT / "config" / "lasttick_reach.json"
HORIZONS = tuple(range(5, 346, 5))          # minutes: the recorder follows a ladder for 330, and a reading may add a quarter of an hour
ONE_IN = 500
FLOOR = 0.01
SHOWN = (30, 60, 90, 120, 180, 240, 300, 330)
EVENINGS = (60, 120, 180, 240, 300)
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)

_spec = importlib.util.spec_from_file_location("lasttick_reach", Path(__file__).resolve().parent / "lasttick_reach.py")
l1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(l1)
COINS = l1.COINS


def ended(d: pd.DataFrame, h: int) -> np.ndarray:
    """For every minute: how far the close stood from this minute's close ``h`` minutes later, as a share of this minute's close."""
    close = d["close"]
    return (close.shift(-h) / close - 1.0).abs().to_numpy()


def yearly(d: pd.DataFrame, horizons: tuple[int, ...] = HORIZONS, one_in: int = ONE_IN) -> pd.DataFrame:
    """For each year and horizon: the distance that one start in ``one_in`` ended beyond."""
    year = pd.to_datetime(d.index.to_numpy(), unit="s").year.to_numpy()
    rows = []
    for h in horizons:
        e = ended(d, h)
        ok = np.isfinite(e)
        for y in np.unique(year):
            x = e[ok & (year == y)]
            if len(x) >= 10 * one_in:
                rows.append({"h": h, "year": int(y), "starts": len(x), "one_in": float(np.quantile(x, 1.0 - 1.0 / one_in))})
    return pd.DataFrame(rows)


def reach_from(by_year: pd.DataFrame, floor: float = FLOOR) -> dict[int, float]:
    """The largest yearly figure for each horizon, at least ``floor``, and never smaller than for a shorter horizon."""
    worst = by_year.groupby("h")["one_in"].max().sort_index()
    out, so_far = {}, floor
    for h, v in worst.items():
        so_far = max(so_far, float(v))
        out[int(h)] = round(so_far, 5)
    return out


def exceeded(d: pd.DataFrame, reach: dict[int, float], limit: float | None, horizons: tuple[int, ...] = SHOWN) -> pd.DataFrame:
    """How often a start ended beyond the reach, by year: every start, and only the starts the brake lets through."""
    year = pd.to_datetime(d.index.to_numpy(), unit="s").year.to_numpy()
    stop = l1.braked(d, limit) if limit is not None else np.zeros(len(d), bool)
    rows = []
    for h in horizons:
        e = ended(d, h)
        ok = np.isfinite(e)
        over = e > reach[h]
        for y in np.unique(year):
            m = ok & (year == y)
            free = m & ~stop
            rows.append({"h": h, "year": int(y), "starts": int(m.sum()), "beyond": int((m & over).sum()),
                         "free_starts": int(free.sum()), "free_beyond": int((free & over).sum())})
    return pd.DataFrame(rows)


def evenings(d: pd.DataFrame, reach: dict[int, float], limit: float | None, horizons: tuple[int, ...] = EVENINGS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The yardstick at the daily settlement itself: from h minutes before 5 pm New York to 5 pm, every evening since 2020."""
    ny = pd.to_datetime(d.index.to_numpy(), unit="s", utc=True).tz_convert("America/New_York")
    last = np.flatnonzero(np.asarray((ny.hour == 16) & (ny.minute == 59)))          # the minute that closes at 17:00
    close = d["close"].to_numpy()
    stop = l1.braked(d, limit) if limit is not None else np.zeros(len(d), bool)
    counts, events = [], []
    for h in horizons:
        end = last[last - h >= 0]
        start = end - h
        move = np.abs(close[end] / close[start] - 1.0)
        free = ~stop[start]
        counts.append({"h": h, "reach": reach[h], "evenings": len(end), "braked": int((~free).sum()), "beyond": int((free & (move > reach[h])).sum()),
                       "beyond_half": int((free & (move > reach[h] / 2)).sum()), "largest": float(move[free].max()) if free.any() else np.nan})
        for i in np.flatnonzero(free & (move > reach[h] * 0.75)):
            events.append({"date": pd.Timestamp(d.index[end[i]], unit="s").strftime("%Y-%m-%d"), "h": h, "reach": reach[h], "ended": float(move[i])})
    return pd.DataFrame(counts), pd.DataFrame(events)


def main() -> int:
    brake = {c: float(v) for c, v in json.loads(L1_CONFIG.read_text())["recent"]["brake"].items()}
    lines: list[str] = []

    def say(text: str = "") -> None:
        print(text)
        lines.append(text)

    say("The yardstick of test L3 (docs/11_crypto_us.md, section 13): how far a coin has stood from where it was, h minutes later")
    say(f"one-minute closes, {l1.FIRST} to {l1.LAST}; for each year the distance one start in {ONE_IN} ended beyond; the reach is the largest year's, at least {FLOOR:.0%}")
    reach: dict[str, dict[int, float]] = {}
    by_year_all, exceeded_all, counts_all, events_all = [], [], [], []
    for coin in COINS:
        d = l1.minutes(coin)
        by_year = yearly(d)
        reach[coin] = reach_from(by_year)
        by_year_all.append(by_year.assign(coin=coin))
        exceeded_all.append(exceeded(d, reach[coin], brake.get(coin)).assign(coin=coin))
        counts, events = evenings(d, reach[coin], brake.get(coin))
        counts_all.append(counts.assign(coin=coin))
        events_all.append(events.assign(coin=coin))
    by_year = pd.concat(by_year_all, ignore_index=True)
    ex = pd.concat(exceeded_all, ignore_index=True)
    counts = pd.concat(counts_all, ignore_index=True)
    events = pd.concat(events_all, ignore_index=True)

    say()
    say("the reach, as a share of the price, by coin and minutes ahead:")
    say(pd.DataFrame({c: {h: reach[c][h] for h in SHOWN} for c in COINS}).T.rename(columns=lambda h: f"{h} min").map(lambda v: f"{v:.2%}").to_string())
    worst = by_year.loc[by_year.groupby(["coin", "h"])["one_in"].idxmax()]
    say()
    say("the year that sets it (the year with the largest figure at that horizon):")
    say(worst[worst["h"].isin(SHOWN)].pivot(index="coin", columns="h", values="year").reindex(COINS).rename(columns=lambda h: f"{h} min").to_string())
    say()
    say("the same figure year by year, Bitcoin:")
    say(by_year[(by_year["coin"] == "btc") & by_year["h"].isin(SHOWN)].pivot(index="year", columns="h", values="one_in").rename(columns=lambda h: f"{h} min")
        .map(lambda v: f"{v:.2%}").to_string())

    ex["share"] = ex["beyond"] / ex["starts"]
    ex["free_share"] = ex["free_beyond"] / ex["free_starts"].where(ex["free_starts"] > 0)
    say()
    say(f"how often a start ended beyond the reach, the worst coin, year and horizon: every start, one in {1 / ex['share'].max():,.0f}; "
        f"starts the brake lets through, one in {1 / ex['free_share'].max():,.0f}")
    w = ex.loc[ex["free_share"].idxmax()]
    say(f"   (the worst with the brake: {w['coin']}, {int(w['year'])}, {int(w['h'])} minutes ahead: {int(w['free_beyond']):,} of {int(w['free_starts']):,} starts)")
    passed = bool(ex["free_share"].max() <= 1.0 / ONE_IN + 1e-12)
    say(f"the check fixed with the yardstick: with the brake, no coin, year and horizon beyond the reach more often than one start in {ONE_IN}: {'holds' if passed else 'DOES NOT HOLD'}")
    say("   by year, all coins and the horizons shown, starts the brake lets through:")
    t = ex.groupby("year").agg(starts=("free_starts", "sum"), beyond=("free_beyond", "sum"))
    t["one in"] = (t["starts"] / t["beyond"].where(t["beyond"] > 0)).round(0)
    say(t.to_string())

    say()
    say("at the daily settlement itself: from h minutes before 5 pm New York to 5 pm, every evening since 2020, evenings the brake lets through")
    say(counts.assign(reach=lambda x: x["reach"].map(lambda v: f"{v:.2%}"), largest=lambda x: x["largest"].map(lambda v: f"{v:.2%}"))
        [["coin", "h", "reach", "evenings", "braked", "beyond", "beyond_half", "largest"]].to_string(index=False))
    if len(events):
        say()
        say("evenings on which the price ended further than three quarters of the reach:")
        say(events.assign(reach=lambda x: x["reach"].map(lambda v: f"{v:.2%}"), ended=lambda x: x["ended"].map(lambda v: f"{v:.2%}"))[["date", "coin", "h", "reach", "ended"]]
            .sort_values(["date", "coin", "h"]).to_string(index=False))

    OUT.mkdir(parents=True, exist_ok=True)
    by_year.to_csv(OUT / "lhr_by_year.csv", index=False)
    ex.to_csv(OUT / "lhr_exceeded.csv", index=False)
    counts.to_csv(OUT / "lhr_evenings.csv", index=False)
    events.to_csv(OUT / "lhr_evenings_near.csv", index=False)
    (OUT / "lasthours_reach_output.txt").write_text("\n".join(lines) + "\n")
    CONFIG.write_text(json.dumps({
        "what": "test L3 (docs/11_crypto_us.md, section 13): a bracket is far enough if its nearer edge is further from the index than reach[coin][minutes], "
                "minutes being the time left rounded up to the next figure listed",
        "made_by": "scripts/lasthours_reach.py", "prices": f"one-minute closes against USDT, {l1.FIRST} to {l1.LAST}",
        "measure": "how far the price stood from where it was, minutes later", "one_in": ONE_IN, "floor": FLOOR, "check_passed": passed,
        "reach": {c: {str(h): v for h, v in reach[c].items()} for c in COINS},
        "brake": brake, "brake_from": "config/lasttick_reach.json, the brake of L1's second yardstick, unchanged"}, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
