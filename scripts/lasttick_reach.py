"""How far a coin's price has gone within a few minutes: the reach table of test L1.

docs/11_crypto_us.md, section 5, "Out of reach", item 3:

    From one-minute prices of each coin since 1 January 2020, for a horizon
    of h minutes: take every minute as a start, and measure the largest move
    either way within the next h minutes, using each minute's high and low.
    For each calendar year take the move that only one start in 5,000
    exceeded. The reach for that coin and horizon is the largest of those
    yearly figures, and never less than 1%.

    python scripts/lasttick_reach.py fetch      # one-minute prices of four coins since 2020 -> data/crypto/minute_<coin>.parquet
    python scripts/lasttick_reach.py            # -> config/lasttick_reach.json, reports/research/ltr_*

That table is the yardstick of L1-strict. The same section, "A second
yardstick", defines L1-recent: the reach from 2023 to 2026 only, and a
brake on five-minute moves in the hour before. Its check is run here too:
the yardstick with its brake applied to every minute since 2020.

Prices: data/crypto/minute_<coin>.parquet, one-minute candles against USDT
from Binance's public data mirror. This uses no Polymarket data at all.
"""

from __future__ import annotations

import json
import sys
import time
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
RECENT = (2023, 2024, 2025, 2026)       # the years the second yardstick is made from
BRAKE_ONE_IN = 1_000                    # the five-minute change that one interval in this many exceeded, in those years
BRAKE_HOUR = 12                         # five-minute changes looked at before a reading: an hour of them
CHECK_ONE_IN = 1_000                    # the second yardstick fails if any year went beyond it more often than this
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)


SYMBOLS = {"btc": "BTCUSDT", "eth": "ETHUSDT", "sol": "SOLUSDT", "xrp": "XRPUSDT"}


def fetch(coins: tuple[str, ...] = COINS) -> None:
    """One-minute candles from Binance's public market-data mirror. About 3.6 million rows a coin; twenty minutes each."""
    import requests

    session = requests.Session()
    PRICES.mkdir(parents=True, exist_ok=True)
    for coin in coins:
        path = PRICES / f"minute_{coin}.parquet"
        if path.exists():
            print(f"{coin}: already there", flush=True)
            continue
        rows, cur, end = [], int(pd.Timestamp(FIRST, tz="UTC").timestamp() * 1000), int(pd.Timestamp(LAST, tz="UTC").timestamp() * 1000)
        while cur < end:
            for attempt in range(6):
                try:
                    r = session.get("https://data-api.binance.vision/api/v3/klines", headers={"User-Agent": "research-client"}, timeout=30,
                                    params={"symbol": SYMBOLS[coin], "interval": "1m", "startTime": cur, "endTime": end, "limit": 1000})
                    if r.status_code == 429 or r.status_code >= 500:
                        time.sleep(5 * (attempt + 1))
                        continue
                    r.raise_for_status()
                    batch = r.json()
                    break
                except requests.RequestException:
                    time.sleep(3 * (attempt + 1))
            else:
                raise RuntimeError(f"{coin}: the price source did not answer")
            if not batch:
                break
            rows += [(b[0] // 1000, float(b[1]), float(b[2]), float(b[3]), float(b[4])) for b in batch]
            cur = batch[-1][0] + 60_000
            if len(rows) % 300_000 == 0:
                print(f"{coin}: {pd.Timestamp(cur, unit='ms'):%Y-%m-%d}", flush=True)
            time.sleep(0.12)
        pd.DataFrame(rows, columns=["t", "open", "high", "low", "close"]).drop_duplicates("t").to_parquet(path, index=False)
        print(f"{coin}: {len(rows):,} minutes", flush=True)


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


def five_minute_changes(d: pd.DataFrame) -> pd.Series:
    """The change from one five-minute mark to the next, as a share of the earlier level, indexed by the later mark."""
    marks = d.loc[d.index % 300 == 0, "close"]
    return (marks / marks.shift(1) - 1.0).abs().dropna()


def brake_limit(d: pd.DataFrame) -> float:
    """The five-minute change that one interval in BRAKE_ONE_IN exceeded in the RECENT years."""
    ch = five_minute_changes(d)
    year = pd.to_datetime(ch.index.to_numpy(), unit="s").year
    return float(np.quantile(ch[np.isin(year, RECENT)].to_numpy(), 1.0 - 1.0 / BRAKE_ONE_IN))


def braked(d: pd.DataFrame, limit: float) -> np.ndarray:
    """For every minute: was any of the last BRAKE_HOUR five-minute changes, up to the mark at or before it, over ``limit``?"""
    ch = five_minute_changes(d)
    worst = ch.rolling(BRAKE_HOUR, min_periods=BRAKE_HOUR // 2).max()        # fewer than six changes known: no trade, so counted as braked below
    at_mark = (worst > limit) | worst.isna()
    flags = at_mark.reindex(d.index).ffill()                                  # a minute takes the flag of the last mark at or before it
    return flags.fillna(True).to_numpy(dtype=bool)


def check_recent(d: pd.DataFrame, reach: dict[int, float], limit: float) -> pd.DataFrame:
    """The second yardstick on every minute: of the starts the brake lets through, how many went beyond the reach, year by year."""
    year = pd.to_datetime(d.index.to_numpy(), unit="s").year.to_numpy()
    stop = braked(d, limit)
    rows = []
    for h in SHOWN:
        mv = moves(d, h)
        ok = np.isfinite(mv)
        for y in np.unique(year):
            sel = ok & (year == y)
            free = sel & ~stop
            over = free & (mv > reach[h])
            idx = np.flatnonzero(over)
            rows.append({"year": int(y), "h": h, "reach": reach[h], "starts": int(sel.sum()), "braked_share": float((sel & stop).sum() / max(1, sel.sum())),
                         "traded_starts": int(free.sum()), "over": int(over.sum()), "one_in": (free.sum() / over.sum()) if over.sum() else np.inf,
                         "occasions": int(1 + (np.diff(idx) > 60).sum()) if len(idx) else 0,
                         "over_without_brake": int((sel & (mv > reach[h])).sum())})
    return pd.DataFrame(rows)


def evenings(d: pd.DataFrame, reach: dict[int, float], limit: float | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The yardstick at the daily settlement itself: every evening's last h minutes before 5 pm New York.

    Two measures of the move. "furthest": the furthest the price went on the
    way, from each minute's high and low, which is what the reach is made
    from and what a "hit" market is exposed to. "ended": where the price
    was at 5 pm against where it had been, which is what a ladder settles
    on. Returns the counts, and the evenings on which either went beyond
    half the reach.
    """
    ny = pd.to_datetime(d.index.to_numpy(), unit="s", utc=True).tz_convert("America/New_York")
    stop = braked(d, limit) if limit is not None else np.zeros(len(d), bool)
    close = d["close"]
    counts, events = [], []
    for h in SHOWN:
        if h > 59:
            continue
        furthest = moves(d, h)
        ended = (close.shift(-h) / close - 1.0).abs().to_numpy()
        at = np.asarray((ny.hour == 16) & (ny.minute == 59 - h)) & np.isfinite(furthest)      # the h minutes that end with the minute closing at 17:00
        free = at & ~stop
        counts.append({"h": h, "reach": reach[h], "evenings": int(at.sum()), "braked": int((at & stop).sum()),
                       "furthest_over": int((free & (furthest > reach[h])).sum()), "ended_over": int((free & (ended > reach[h])).sum()),
                       "furthest_over_half": int((free & (furthest > reach[h] / 2)).sum()), "ended_over_half": int((free & (ended > reach[h] / 2)).sum())})
        for i in np.flatnonzero(free & (furthest > reach[h] / 2)):
            events.append({"date": pd.Timestamp(d.index[i], unit="s").strftime("%Y-%m-%d"), "h": h, "reach": reach[h], "furthest": float(furthest[i]), "ended": float(ended[i])})
    return pd.DataFrame(counts), pd.DataFrame(events)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    table: dict[str, dict[str, float]] = {}
    recent_table: dict[str, dict[str, float]] = {}
    brakes: dict[str, float] = {}
    all_checks = []
    all_evenings, all_events = [], []
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
        # the second yardstick: 2023 to 2026 only, with its brake, checked on every year since 2020
        recent = reach_from(by_year, list(RECENT))
        recent_table[coin] = {str(h): round(v, 5) for h, v in recent.items()}
        brakes[coin] = round(brake_limit(d), 5)
        chk = check_recent(d, {h: recent_table[coin][str(h)] for h in SHOWN}, brakes[coin])
        chk.insert(0, "coin", coin)
        all_checks.append(chk)
        lines.append("   second yardstick:  " + "  ".join(f"{100 * recent[h]:5.2f}%" for h in SHOWN) + f"   brake at a five-minute change of {100 * brakes[coin]:.2f}%")
        # both yardsticks at the settlement itself: the minutes before 5 pm New York on every evening
        for name, table_, limit in (("recent", {h: recent_table[coin][str(h)] for h in SHOWN}, brakes[coin]), ("strict", {h: table[coin][str(h)] for h in SHOWN}, None)):
            c, ev = evenings(d, table_, limit)
            all_evenings.append(c.assign(coin=coin, yardstick=name))
            if len(ev):
                all_events.append(ev.assign(coin=coin, yardstick=name))
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
    checks = pd.concat(all_checks, ignore_index=True)
    checks.to_csv(OUT / "ltr_recent_check.csv", index=False)
    worst = checks.loc[checks["one_in"].idxmin()]
    passed = bool(worst["one_in"] >= CHECK_ONE_IN)
    show = checks.assign(reach=(100 * checks["reach"]).round(2), braked_share=(100 * checks["braked_share"]).round(2)).round({"one_in": 0})
    lines += ["", f"the second yardstick (reach from {RECENT[0]}-{RECENT[-1]}, brake on five-minute moves in the hour before) on every minute since 2020",
              "'braked_share' is the percentage of starts the brake stops; 'over' counts the starts it lets through that went beyond the reach",
              show.to_string(index=False), "",
              f"its test (docs/11): no coin, year and horizon may go beyond the reach more often than one start in {CHECK_ONE_IN:,}",
              f"the worst: {worst['coin'].upper()} in {int(worst['year'])} at {int(worst['h'])} minutes, one start in {worst['one_in']:,.0f}: "
              + ("PASSED" if passed else "FAILED")]
    ev_counts = pd.concat(all_evenings, ignore_index=True)[["yardstick", "coin", "h", "reach", "evenings", "braked", "furthest_over", "ended_over",
                                                            "furthest_over_half", "ended_over_half"]]
    ev_counts.to_csv(OUT / "ltr_evenings.csv", index=False)
    ev_list = pd.concat(all_events, ignore_index=True)[["yardstick", "coin", "date", "h", "reach", "furthest", "ended"]] if all_events else pd.DataFrame()
    lines += ["", "the same yardsticks at the daily settlement itself: the last h minutes before 5 pm New York, every evening since 2020 (added after the history was read)",
              "'furthest' is the furthest the price went on the way; 'ended' is where it was at 5 pm against where it had been, which is what a ladder settles on",
              ev_counts.assign(reach=(100 * ev_counts["reach"]).round(2)).to_string(index=False)]
    if len(ev_list):
        over = ev_list[(ev_list["furthest"] > ev_list["reach"]) | (ev_list["ended"] > ev_list["reach"])].sort_values(["yardstick", "date", "coin", "h"])
        ev_list.sort_values(["yardstick", "date", "coin", "h"]).to_csv(OUT / "ltr_evenings_near.csv", index=False)
        lines += ["", "the evenings on which the price went beyond the reach (percent)",
                  over.assign(reach=(100 * over["reach"]).round(2), furthest=(100 * over["furthest"]).round(2), ended=(100 * over["ended"]).round(2)).to_string(index=False)]
    CONFIG.write_text(json.dumps({"what": "test L1 (docs/11_crypto_us.md, section 5): a result is out of reach if its gap is larger than reach[coin][minutes]",
                                  "made_by": "scripts/lasttick_reach.py", "prices": f"one-minute candles against USDT, {FIRST} to {LAST}", "one_in": ONE_IN,
                                  "floor": FLOOR, "reach": table,
                                  "recent": {"years": list(RECENT), "reach": recent_table, "brake": brakes, "brake_one_in": BRAKE_ONE_IN,
                                             "check_one_in": CHECK_ONE_IN, "check_passed": passed}}, indent=1) + "\n")
    text = "\n".join(lines) + "\n"
    (OUT / "lasttick_reach_output.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    if sys.argv[1:2] == ["fetch"]:
        fetch()
    else:
        main()
