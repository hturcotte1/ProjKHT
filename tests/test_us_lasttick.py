"""The recorder of crypto markets in their last minutes (src/kht/trading/us_lasttick.py, docs/11 section 5)."""

from __future__ import annotations

import csv
import gzip
from datetime import datetime, timezone

from kht.trading import us_lasttick as lt

T0 = 1_794_420_000.0            # 11 November 2026, 18:00:00 UTC


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def market(slug, kind, horizon, end, coin="btc", start=None, strike=None, lower=None, upper=None, ptb=None, direction="UNSPECIFIED"):
    money = lambda x: None if x is None else {"value": str(x), "currency": "USD"}
    return {"slug": slug, "assetPriceTerms": {
        "marketType": "ASSET_PRICE_MARKET_TYPE_" + kind, "asset": {"assetClass": "ASSET_CLASS_CRYPTO", "symbol": coin}, "indexSymbol": "BRTI", "horizon": horizon,
        "windowStart": None if start is None else iso(start), "windowEnd": iso(end), "priceToBeat": money(ptb), "strike": money(strike),
        "rangeLower": money(lower), "rangeUpper": money(upper), "rangeKind": "ASSET_PRICE_RANGE_KIND_UNSPECIFIED",
        "direction": "ASSET_PRICE_DIRECTION_" + direction}}


def book(bid=(0.01, 1500.0), ask=(0.02, 100.0), traded="0.0000"):
    level = lambda px, qty: {"px": {"value": str(px), "currency": "USD"}, "qty": str(qty)}
    return {"bids": [level(*bid)] if bid else [], "offers": [level(*ask)] if ask else [], "state": "MARKET_STATE_OPEN",
            "transactTime": "2026-11-11T17:50:00.123456789Z", "stats": {"sharesTraded": traded}}


class Clock:
    def __init__(self, t):
        self.t = t

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


class FakeUS:
    def __init__(self, clock, markets):
        self.clock, self.markets, self.listed, self.read = clock, markets, 0, []

    def iter_markets(self, **filters):
        assert filters == {"closed": False, "categories": "crypto"}
        self.listed += 1
        return iter(self.markets(self.clock.t))

    def book(self, slug):
        self.read.append((round(self.clock.t), slug))
        if slug.endswith("broken"):
            raise RuntimeError("no book")
        return book()


def test_terms_reads_each_kind_of_market():
    above = lt.terms(market("cpc-btc-above-day-2026-11-11-78000", "ABOVE_BELOW", "daily", T0, strike=78000))
    assert above["kind"] == "above_below" and above["strike"] == 78000.0 and above["end"] == T0 and above["coin"] == "btc" and above["start"] is None
    bracket = lt.terms(market("cpc-btc-range-day-2026-11-11-74000", "RANGE", "daily", T0, lower=74000, upper=74249.99))
    assert (bracket["lower"], bracket["upper"]) == (74000.0, 74249.99) and bracket["strike"] is None
    hit = lt.terms(market("cpc-btc-hit-h-w-2026-11-13-85000", "ONE_TOUCH", "weekly", T0, start=T0 - 7 * 86400, strike=85000, direction="UP"))
    assert hit["kind"] == "one_touch" and hit["direction"] == "up"
    up = lt.terms(market("cpc-btc-updown-5m-2026-11-11-1755z", "UP_DOWN", "5m", T0, start=T0 - 300, ptb=74145.17))
    assert up["price_to_beat"] == 74145.17 and up["start"] == T0 - 300
    assert lt.terms({"slug": "tklc-something", "assetPriceTerms": None}) is None                       # not a price market
    assert lt.terms({"slug": "x", "assetPriceTerms": {"marketType": "ASSET_PRICE_MARKET_TYPE_RANGE"}}) is None    # no end


def test_the_index_is_the_price_to_beat_of_the_market_that_started_last():
    ms = [market("btc-5m-a", "UP_DOWN", "5m", T0 - 600, start=T0 - 900, ptb=74000.0), market("btc-5m-b", "UP_DOWN", "5m", T0 - 300, start=T0 - 600, ptb=74100.0),
          market("btc-5m-next", "UP_DOWN", "5m", T0, start=T0 - 300, ptb=None),                 # started, but its level is not out yet
          market("btc-5m-later", "UP_DOWN", "5m", T0 + 600, start=T0 + 300, ptb=99999.0),       # not started: whatever it carries is not a level
          market("eth-1h", "UP_DOWN", "1h", T0, coin="eth", start=T0 - 3600, ptb=2070.0),
          market("btc-ladder", "ABOVE_BELOW", "daily", T0, strike=78000)]
    levels = lt.index_levels({m["slug"]: m for m in map(lt.terms, ms)}, T0 - 200)
    assert levels["btc"] == {"level": 74100.0, "at": T0 - 600, "slug": "btc-5m-b"}
    assert levels["eth"]["level"] == 2070.0 and set(levels) == {"btc", "eth"}


def test_only_markets_about_to_end_are_followed_and_fast_ones_never():
    ms = [market("daily-near", "ABOVE_BELOW", "daily", T0, strike=78000), market("daily-far", "ABOVE_BELOW", "daily", T0 + 86400, strike=78000),
          market("hourly-updown", "UP_DOWN", "1h", T0, start=T0 - 3600, ptb=74000.0), market("five", "UP_DOWN", "5m", T0, start=T0 - 300, ptb=74000.0),
          market("fifteen", "UP_DOWN", "15m", T0, start=T0 - 900, ptb=74000.0), market("hourly-ladder", "ABOVE_BELOW", "hourly", T0, strike=74000),
          market("ended", "RANGE", "daily", T0 - 3600, lower=1, upper=2)]
    markets = {m["slug"]: m for m in map(lt.terms, ms)}
    assert lt.followed(markets, T0 - lt.FOLLOW - 1) == []
    assert lt.followed(markets, T0 - lt.FOLLOW + 1) == ["daily-near", "hourly-updown"]
    assert lt.followed(markets, T0 + lt.AFTER - 1) == ["daily-near", "hourly-updown"]
    assert lt.followed(markets, T0 + lt.AFTER + 1) == []


def test_a_run_writes_books_markets_and_index_levels(tmp_path):
    clock = Clock(T0 - 20 * 60)

    def listing(t):
        five = T0 - 300 * (int((T0 - t) // 300) + 1)                            # start of the five-minute window that t is in
        ms = [market("cpc-btc-updown-5m-now", "UP_DOWN", "5m", five + 300, start=five, ptb=74000.0 + (five - T0) / 300)]
        if t <= T0:                                                              # an ended market leaves the list of open ones at once
            ms += [market("cpc-btc-above-day-2026-11-11-78000", "ABOVE_BELOW", "daily", T0, strike=78000),
                   market("cpc-btc-above-day-2026-11-11-broken", "ABOVE_BELOW", "daily", T0, strike=79000),
                   market("cpc-btc-updown-1d-x", "UP_DOWN", "1d", T0, start=T0 - 86400, ptb=73755.82)]
        return ms + [market("cpc-btc-above-hr-2026-11-11-1800z-74000", "ABOVE_BELOW", "hourly", T0, strike=74000)]

    us = FakeUS(clock, listing)
    line = lt.run(tmp_path, minutes=22, us=us, now=clock.now, sleep=clock.sleep)
    run_dir = tmp_path / "runs" / line["run"]
    with gzip.open(run_dir / "books.csv.gz", "rt", newline="") as fh:
        books = list(csv.DictReader(fh))
    slugs = {b["slug"] for b in books}
    assert slugs == {"cpc-btc-above-day-2026-11-11-78000", "cpc-btc-updown-1d-x"}             # not the 5-minute market, not the hourly ladder
    lefts = sorted(float(b["left"]) for b in books if b["slug"].endswith("78000"))
    assert lefts[-1] <= lt.FOLLOW and lefts[-1] > lt.FOLLOW - 60                                # followed from 17 minutes before the end
    assert lefts[0] < 0 and lefts[0] >= -lt.AFTER                                                # and read once more after it, though it has left the list
    gaps = [a - b for a, b in zip(lefts[1:], lefts[:-1])]
    assert min(gaps) >= lt.SWEEP - 1e-6 and max(gaps) <= lt.SWEEP + 1                            # one reading every forty seconds
    first = books[0]
    assert (first["bid1"], first["bid_qty1"], first["ask1"], first["ask_qty1"], first["state"]) == ("0.01", "1500.0", "0.02", "100.0", "OPEN")
    assert first["tx"] == "2026-11-11T17:50:00.123" and first["run"] == line["run"]
    with (run_dir / "markets.csv").open(newline="") as fh:
        markets = {m["slug"]: m for m in csv.DictReader(fh)}
    assert set(markets) == slugs | {"cpc-btc-above-day-2026-11-11-broken"}
    assert markets["cpc-btc-above-day-2026-11-11-78000"]["strike"] == "78000.0" and markets["cpc-btc-updown-1d-x"]["price_to_beat"] == "73755.82"
    with (run_dir / "index.csv").open(newline="") as fh:
        index = list(csv.DictReader(fh))
    assert len(index) >= 4 and all(r["coin"] == "btc" for r in index)                           # a new level every five minutes
    ats = [float(r["at"]) for r in index]
    assert ats == sorted(ats) and len(set(ats)) == len(ats)
    assert all(float(r["ts"]) - float(r["at"]) <= 300 + lt.LIST_BUSY + lt.SWEEP for r in index[1:])   # and each is picked up within two minutes
    assert line["markets"] == 3 and line["ends"] == 1 and line["errors"] > 0                    # the book that could not be read is counted, not fatal
    assert line["books"] == len(books)
    status = (tmp_path / "STATUS.md").read_text()
    assert "2 markets had a best bid of 1¢ (3,000 contracts)" in status and "btc above below (daily) | 2" in status
    with (tmp_path / "log.csv").open(newline="") as fh:
        assert [r["run"] for r in csv.DictReader(fh)] == [line["run"]]


def test_a_listing_that_fails_does_not_stop_the_readings(tmp_path):
    clock = Clock(T0 - 10 * 60)
    calls = {"n": 0}

    def listing(t):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("gateway down")
        return [market("cpc-btc-above-day-2026-11-11-78000", "ABOVE_BELOW", "daily", T0, strike=78000)]

    us = FakeUS(clock, listing)
    line = lt.run(tmp_path, minutes=8, us=us, now=clock.now, sleep=clock.sleep)
    assert line["errors"] == 1 and line["listings"] >= 2 and line["books"] >= 8


def test_what_was_read_is_written_as_soon_as_the_markets_have_ended(tmp_path):
    clock = Clock(T0 - 5 * 60)                                                # the ten-minute writing would come five minutes after the end
    on_disk = {}

    def sleep(seconds):
        if clock.t > T0 + lt.AFTER and "rows" not in on_disk:                # the first pause that begins after the last reading: what is on disk?
            path = next((tmp_path / "runs").glob("*/books.csv.gz"), None)
            on_disk["at"] = clock.t - T0
            on_disk["rows"] = 0
            if path is not None:
                with gzip.open(path, "rt", newline="") as fh:
                    on_disk["rows"] = len(list(csv.DictReader(fh)))
        clock.sleep(seconds)

    us = FakeUS(clock, lambda t: [market("cpc-btc-above-day-2026-11-11-78000", "ABOVE_BELOW", "daily", T0, strike=78000)] if t <= T0 else [])
    line = lt.run(tmp_path, minutes=9, us=us, now=clock.now, sleep=sleep)     # ends four minutes after the settlement
    assert on_disk["at"] < 150 and on_disk["rows"] >= 7                       # written within two minutes of the end
    assert on_disk["rows"] == line["books"]


def test_the_second_copy_reads_brackets_only_from_hours_before_and_less_often(tmp_path):
    clock = Clock(T0 - 6 * 3600)
    ms = [market("cpc-btc-range-day-2026-11-11-74000", "RANGE", "daily", T0, lower=74000, upper=74249.99),
          market("cpc-btc-range-day-2026-11-11-above-81500", "RANGE", "daily", T0, lower=81500),
          market("cpc-btc-range-wk-2026-11-13-74000", "RANGE", "weekly", T0 + 2 * 86400, lower=74000, upper=74999.99),
          market("cpc-btc-above-day-2026-11-11-78000", "ABOVE_BELOW", "daily", T0, strike=78000),
          market("cpc-btc-updown-1d-x", "UP_DOWN", "1d", T0, start=T0 - 86400, ptb=73755.82),
          market("cpc-btc-range-hr-2026-11-11-1800z-74000", "RANGE", "hourly", T0, lower=74000, upper=74099.99)]
    us = FakeUS(clock, lambda t: ms if t <= T0 else [])
    line = lt.run(tmp_path, minutes=6 * 60 + 2, us=us, now=clock.now, sleep=clock.sleep, follow=19_800, sweep=120.0, kinds=frozenset({"range"}))
    with gzip.open(tmp_path / "runs" / line["run"] / "books.csv.gz", "rt", newline="") as fh:
        books = list(csv.DictReader(fh))
    assert {b["slug"] for b in books} == {"cpc-btc-range-day-2026-11-11-74000", "cpc-btc-range-day-2026-11-11-above-81500"}   # daily brackets, nothing else
    lefts = sorted(float(b["left"]) for b in books if b["slug"].endswith("-74000"))
    assert 19_800 - 130 < lefts[-1] <= 19_800                                    # from five and a half hours before the end
    gaps = [a - b for a, b in zip(lefts[1:], lefts[:-1])]
    assert min(gaps) >= 120 - 1e-6 and max(gaps) <= 121                          # every two minutes
    status = (tmp_path / "STATUS.md").read_text()
    assert status.startswith("# Crypto ladders before they settle") and "only range markets, from 330 minutes before their end" in status
    assert "us_ladder_score.py" in status and "btc range (daily) | 2" in status


def test_with_the_settings_left_alone_every_kind_is_followed_as_before():
    ms = [market("a-range", "RANGE", "daily", T0, lower=1, upper=2), market("b-above", "ABOVE_BELOW", "daily", T0, strike=78000),
          market("c-hit", "ONE_TOUCH", "weekly", T0, start=T0 - 7 * 86400, strike=85000, direction="UP")]
    markets = {m["slug"]: m for m in map(lt.terms, ms)}
    assert lt.followed(markets, T0 - 60) == ["a-range", "b-above", "c-hit"]
    assert lt.followed(markets, T0 - 60, lt.FOLLOW, None) == ["a-range", "b-above", "c-hit"]
    assert lt.followed(markets, T0 - 60, lt.FOLLOW, frozenset({"range"})) == ["a-range"]
    assert lt.followed(markets, T0 - 3600, 19_800, frozenset({"range"})) == ["a-range"] and lt.followed(markets, T0 - 3600) == []
