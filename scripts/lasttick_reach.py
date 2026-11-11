"""How far a coin's price has gone within a few minutes: the reach table of test L1.

docs/11_crypto_us.md, section 5, "Out of reach", item 3:

    From one-minute prices of each coin since 1 January 2020, for a horizon
    of h minutes: take every minute as a start, and measure the largest move
    either way within the next h minutes, using each minute's high and low.
    For each calendar year take the move that only one start in 5,000
    exceeded. The reach for that coin and horizon is the largest of those
    yearly figures, and never less than 1%.

    python scripts/lasttick_reach.py            # -> config/lasttick_reach.json, reports/research/ltr_*

Prices: data/crypto/minute_<coin>.parquet, one-minute candles against USDT
from Binance's public data mirror. This uses no Polymarket data at all.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRICES = ROOT / "data" / "crypto"
OUT = ROOT / "reports" / "research"
CONFIG = ROOT / "config" / "lasttick_reach.json"
COINS = ("btc", "eth", "sol", "xrp")
HORIZONS = tuple(range(1, 31))          # minutes
ONE_IN = 5_000
FLOOR = 0.01
FIRST, LAST = "2020-01-01", "2026-11-11"            # prices from the first day up to, not including, the last
SHOWN = (3, 6, 10, 16, 22, 30)
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)


def minutes(coin: str) -> pd.DataFrame:
    """One row a minute with no gaps: a minute the source does not have repeats the last close."""
    d = pd.read_parquet(PRICES / f"minute_{coin}.parquet").drop_duplicates("t").set_index("t").sort_index()
    d = d[(d.index >= pd.Timestamp(FIRST).timestamp()) & (d.index < pd.Timestamp(LAST).timestamp())]
    full = np.arange(int(d.index[0]), int(d.index[-1]) + 60, 60)
    missing = len(full) - len(d)
    d = d.reindex(full)
    d["close"] = d["close"].ffill()
    for c in ("high", "low"):
        d[c] = d[c].fillna(d["close"])
    d.attrs["missing"] = missing
    return d


def moves(d: pd.DataFrame, h: int) -> np.ndarray:
    """For every minute: the largest move either way within the next ``h`` minutes, as a share of that minute's close."""
    close = d["close"].to_numpy()
    # the highest high and lowest low of minutes t+1 .. t+h: a window of h ending at t+h, read back at t
    hi = d["high"].rolling(h).max().shift(-h).to_numpy()
    lo = d["low"].rolling(h).min().shift(-h).to_numpy()
    return np.fmax(hi / close - 1.0, 1.0 - lo / close)


def yearly(d: pd.DataFrame) -> pd.DataFrame:
    """For each year and horizon: the move one start in ONE_IN exceeded, the largest move, and the number of starts."""
    year = pd.to_datetime(d.index.to_numpy(), unit="s").year.to_numpy()
    rows = []
    for h in HORIZONS:
        mv = moves(d, h)
        for y in np.unique(year):
            v = mv[(year == y) & np.isfinite(mv)]
            if len(v) >= 100_000:                       # a year with under ten weeks of prices does not set a figure
                rows.append({"year": int(y), "h": h, "starts": len(v), "one_in": float(np.quantile(v, 1.0 - 1.0 / ONE_IN)), "largest": float(v.max())})
    return pd.DataFrame(rows)


def reach_from(by_year: pd.DataFrame, years: list[int] | None = None) -> dict[int, float]:
    g = by_year if years is None else by_year[by_year["year"].isin(years)]
    return {int(h): max(FLOOR, float(v)) for h, v in g.groupby("h")["one_in"].max().items()}


def exceed(d: pd.DataFrame, reach: dict[int, float], years: list[int]) -> pd.DataFrame:
    """How often the moves of ``years`` went further than ``reach``."""
    year = pd.to_datetime(d.index.to_numpy(), unit="s").year.to_numpy()
    rows = []
    for h in SHOWN:
        mv = moves(d, h)
        for y in years:
            v = mv[(year == y) & np.isfinite(mv)]
            if len(v):
                over = v > reach[h]
                # separate occasions: a start that is over, with none over in the hour before it
                idx = np.flatnonzero(over)
                occasions = int(1 + (np.diff(idx) > 60).sum()) if len(idx) else 0
                rows.append({"year": y, "h": h, "reach": reach[h], "starts": len(v), "over": int(over.sum()), "one_in": (len(v) / over.sum()) if over.sum() else np.inf,
                             "occasions": occasions})
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    table: dict[str, dict[str, float]] = {}
    lines = [f"The reach table of test L1 (docs/11, section 5): the move that one start in {ONE_IN:,} exceeded, in the worst year, never under {100 * FLOOR:g}%",
             f"prices: one-minute candles against USDT, {FIRST} to {LAST} (not included)", ""]
    all_years, all_oos, all_full = [], [], []
    for coin in COINS:
        d = minutes(coin)
        by_year = yearly(d)
        by_year.insert(0, "coin", coin)
        all_years.append(by_year)
        reach = reach_from(by_year)
        table[coin] = {str(h): round(v, 5) for h, v in reach.items()}
        years = sorted(by_year["year"].unique())
        first = pd.Timestamp(d.index[0], unit="s").strftime("%Y-%m-%d")
        lines.append(f"{coin.upper()}: {len(d):,} minutes from {first}, {d.attrs['missing']:,} filled in; years {years[0]} to {years[-1]}")
        worst = by_year.loc[by_year.groupby("h")["one_in"].idxmax()].set_index("h")
        lines.append("   horizon (minutes): " + "  ".join(f"{h:>6d}" for h in SHOWN))
        lines.append("   reach:             " + "  ".join(f"{100 * reach[h]:5.2f}%" for h in SHOWN))
        lines.append("   set by the year:   " + "  ".join(f"{int(worst.loc[h, 'year']):>6d}" for h in SHOWN))
        # in sample, year by year: how often each year went further than the table
        full = exceed(d, reach, [int(y) for y in years])
        full.insert(0, "coin", coin)
        all_full.append(full)
        # out of sample: the table as it would have been at the end of 2024, against 2025 and 2026
        early = [int(y) for y in years if y <= 2024]
        late = [int(y) for y in years if y >= 2025]
        if early and late:
            oos = exceed(d, reach_from(by_year, early), late)
            oos.insert(0, "coin", coin)
            all_oos.append(oos)
    by_year = pd.concat(all_years, ignore_index=True)
    by_year.to_csv(OUT / "ltr_by_year.csv", index=False)
    full = pd.concat(all_full, ignore_index=True)
    full.to_csv(OUT / "ltr_exceeded.csv", index=False)
    lines += ["", "each year against the table (starts that went further than the reach; 'occasions' are more than an hour apart)",
              full.assign(reach=(100 * full["reach"]).round(2)).round({"one_in": 0}).to_string(index=False)]
    if all_oos:
        oos = pd.concat(all_oos, ignore_index=True)
        oos.to_csv(OUT / "ltr_out_of_sample.csv", index=False)
        lines += ["", "out of sample: the table made from 2020-2024 only, against 2025 and 2026",
                  oos.assign(reach=(100 * oos["reach"]).round(2)).round({"one_in": 0}).to_string(index=False)]
        worst = oos.loc[oos["one_in"].idxmin()]
        lines += ["", f"the worst case out of sample: {worst['coin'].upper()} in {int(worst['year'])} at {int(worst['h'])} minutes, one start in {worst['one_in']:,.0f} "
                      f"(the table allows one in {ONE_IN:,})"]
    CONFIG.write_text(json.dumps({"what": "test L1 (docs/11_crypto_us.md, section 5): a result is out of reach if its gap is larger than reach[coin][minutes]",
                                  "made_by": "scripts/lasttick_reach.py", "prices": f"one-minute candles against USDT, {FIRST} to {LAST}", "one_in": ONE_IN,
                                  "floor": FLOOR, "reach": table}, indent=1) + "\n")
    text = "\n".join(lines) + "\n"
    (OUT / "lasttick_reach_output.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
