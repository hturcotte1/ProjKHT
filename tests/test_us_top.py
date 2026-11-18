"""The half-minute recorder of single-market reward programmes (src/kht/trading/us_top.py) and its scorer (scripts/us_top_score.py)."""

from __future__ import annotations

import csv
import gzip
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from kht.trading import top_rule as rule
from kht.trading import us_top as top

spec = importlib.util.spec_from_file_location("us_top_score", Path(__file__).resolve().parents[1] / "scripts" / "us_top_score.py")
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)

T0 = 1_795_043_700.0            # 18 November 2026, 23:15:00 UTC
GOLD = "cpausp-gold-updown-1d-2026-11-18-2315z"
NEXT = "cpausp-gold-updown-1d-2026-11-18-2318z"      # in these tests the window after the first one starts three minutes later


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def entry(slug, program, pool=1000, target=5000, state="INSTRUMENT_STATE_OPEN", status="active", max_spread=0.03):
    return {"marketSlug": slug, "instrumentState": state,
            "timePeriods": [{"programId": program, "status": status, "rewardPool": pool, "targetSize": target, "discountFactor": 0.3, "maxSpread": max_spread,
                             "period": "daily_event"}]}


def level(px, qty):
    return {"px": {"value": str(px), "currency": "USD"}, "qty": str(qty)}


def book(state="MARKET_STATE_OPEN", traded="10.0"):
    return {"bids": [level(0.52, 300), level(0.51, 5000)], "offers": [level(0.54, 6000)], "state": state, "transactTime": "2026-11-18T23:15:30.123456789Z",
            "stats": {"sharesTraded": traded, "notionalTraded": {"value": "5.2", "currency": "USD"}, "lastTradePx": {"value": "0.52", "currency": "USD"},
                      "lastTradeSetTime": "2026-11-18T23:15:10Z", "openInterest": "10"}}


class Clock:
    def __init__(self, t):
        self.t = t

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


class FakeUS:
    """One gold market that stops being open after three minutes, and the one that follows it, whose book appears a minute late."""

    def __init__(self, clock):
        self.clock, self.schedule_reads, self.asked = clock, 0, []

    def iter_incentives(self, statuses=None):
        self.schedule_reads += 1
        return iter([entry(GOLD, "metals_gold_updown_1d_20261110"), entry("cpausp-gold-updown-1h-x", "metals_gold_updown_1h_20261110"),
                     entry("tec-something", "nba_winner_futures_20261110"), entry("closed-one", "metals_silver_updown_1d_20261110", state="INSTRUMENT_STATE_CLOSED")])

    def market(self, slug):
        nxt = T0 + 180.0 if slug == GOLD else T0 + 86_400.0
        return {"question": "Gold Up or Down Daily", "endDate": iso(T0 + 1800.0),
                "assetPriceTerms": {"windowStart": iso(T0), "windowEnd": iso(T0 + 180.0), "priceToBeat": {"value": "3852.56", "currency": "USD"},
                                    "nextWindowStart": iso(nxt)}}

    def book(self, slug):
        self.asked.append((round(self.clock.t - T0), slug))
        if slug == NEXT and self.clock.t < T0 + 240.0:
            raise RuntimeError("404: no such market yet")
        if slug == GOLD and self.clock.t >= T0 + 180.0:
            return book(state="MARKET_STATE_EXPIRED")
        return book()


def test_schedule_entries_and_names():
    found = top.from_schedule([entry(GOLD, "metals_gold_updown_1d_20261110"), entry("x-1h", "metals_gold_updown_1h_20261110"),
                               entry("old", "metals_silver_updown_1d_20261110", status="closed"), entry("eth", "crypto_alt_updown_1d_20261110", pool=150, target=2000, max_spread=0.05)])
    assert set(found) == {GOLD, "eth"}
    assert found[GOLD]["pool"] == 1000 and found[GOLD]["target"] == 5000 and found[GOLD]["discount"] == 0.3 and found[GOLD]["max_spread"] == 0.03
    assert top.wanted("metals_gold_updown_1d_20261110") == "metals_gold_updown_1d" and top.wanted("metals_gold_updown_1h_20261110") is None
    assert top.next_slug(GOLD, "2026-11-19T23:15:00Z") == "cpausp-gold-updown-1d-2026-11-19-2315z" and top.next_slug(GOLD, iso(T0 + 180.0)) == NEXT
    assert top.next_slug("cpc-btc-updown-1d-2026-11-17-2200z", "2026-11-18T22:00:00Z") == "cpc-btc-updown-1d-2026-11-18-2200z"
    assert top.next_slug("no-date-in-this", "2026-11-18T22:00:00Z") is None and top.next_slug(GOLD, None) is None


def test_a_side_of_a_book_survives_being_written_down():
    side = [(0.99, 164494.6), (0.98, 33.5), (0.975, 0.1)]
    assert top.encode(side) == "0.99:164494.6;0.98:33.5;0.975:0.1"
    assert top.decode(top.encode(side)) == side
    assert top.decode("") == [] and top.decode(float("nan")) == []
    assert len(top.decode(top.encode([(0.5 - i / 100, 1.0) for i in range(30)]))) == top.DEPTH


def test_the_recorder_follows_a_market_and_the_one_after_it(tmp_path):
    clock = Clock(T0)
    us = FakeUS(clock)
    line = top.run(tmp_path, minutes=7, us=us, now=clock.now, sleep=clock.sleep, background=False)
    assert line["errors"] == 0 and line["markets"] == 2 and line["schedule_reads"] >= 1
    with gzip.open(tmp_path / "runs" / line["run"] / "books.csv.gz", "rt") as fh:
        rows = list(csv.DictReader(fh))
    gold = [r for r in rows if r["slug"] == GOLD]
    nxt = [r for r in rows if r["slug"] == NEXT]
    assert [r["state"] for r in gold][:6] == ["OPEN"] * 6                    # every thirty seconds for three minutes
    assert gold[-1]["state"] == "EXPIRED" and float(gold[-1]["ts"]) - T0 <= 180 + top.AFTER + 30      # read a little after it closed, then left alone
    assert nxt and float(nxt[0]["ts"]) >= T0 + 240.0                        # the next one from the moment its book exists
    assert gold[0]["bids"] == "0.52:300;0.51:5000" and gold[0]["asks"] == "0.54:6000" and gold[0]["traded"] == "10.0"
    markets = {r["slug"]: r for r in csv.DictReader((tmp_path / "runs" / line["run"] / "markets.csv").open())}
    assert markets[GOLD]["program"] == "metals_gold_updown_1d_20261110" and float(markets[GOLD]["price_to_beat"]) == 3852.56
    assert float(markets[GOLD]["window_start"]) == T0 and markets[NEXT]["pool"] == markets[GOLD]["pool"]      # the follower inherits the programme's terms
    assert "Gold" in markets[GOLD]["question"] and (tmp_path / "STATUS.md").read_text().startswith("# The top of the book")


def recorded(slug, start, n, bids="0.52:300;0.51:5000", asks="0.54:6000", traded=None, notional=None, closes=True):
    """A market read every thirty seconds ``n`` times from ``start``, then once more closed."""
    rows = []
    for i in range(n):
        v = 0.0 if traded is None else traded(i)
        rows.append({"run": "r", "ts": start + 30.0 * i, "slug": slug, "state": "OPEN", "tx": "", "bids": bids, "asks": asks, "traded": v,
                     "notional": 0.0 if notional is None else notional(i), "last": None, "last_t": None, "low": None, "low_t": None, "high": None, "high_t": None,
                     "open_interest": 0})
    if closes:
        rows.append({**rows[-1], "ts": start + 30.0 * n, "state": "EXPIRED", "bids": "", "asks": ""})
    return rows


TERMS = {"program": "metals_gold_updown_1d_20261110", "pool": 1000.0, "target": 5000.0, "discount": 0.3, "max_spread": 0.03, "window_start": T0, "window_end": T0 + 3600.0}


def test_a_quiet_day_is_paid_its_share_of_the_pool():
    rows = recorded(GOLD, T0 + 60.0, 120)                                  # an hour, nothing trades
    days = {d["size"]: d for d in score.market_day(GOLD, rows, TERMS, 1.0)}
    d = days[100]
    share = (100 / 1900 + 100 / 6100) / 2                                  # the two sides, as in the rule's own test
    assert d["whole"] and d["fills"] == 0 and d["pnl_fills"] == 0.0
    assert d["share"] == pytest.approx(share) and d["qualifies"] == pytest.approx(3600.0 / 3600.0, abs=0.02)
    assert d["reward_formula"] == pytest.approx(1000.0 * share * 3600.0 / 3600.0, rel=0.02) and d["net"] == pytest.approx(d["reward_paid"])
    assert days[25]["reward_formula"] < d["reward_formula"] < days[500]["reward_formula"]


def test_fills_are_held_to_settlement_and_cut_the_orders():
    # after ten minutes 500 contracts trade at 52c: the bid of 100 is hit whole. From then on only the offer rests.
    traded = lambda i: 0.0 if i < 20 else 500.0
    notional = lambda i: 0.0 if i < 20 else 500.0 * 0.52
    rows = recorded(GOLD, T0 + 60.0, 120, traded=traded, notional=notional)
    lost = {d["size"]: d for d in score.market_day(GOLD, rows, TERMS, 0.0)}[100]
    won = {d["size"]: d for d in score.market_day(GOLD, rows, TERMS, 1.0)}[100]
    assert lost["bought"] == 100 and lost["sold"] == 0 and lost["held_at_end"] == 100
    assert lost["pnl_fills"] == pytest.approx(-52.0) and won["pnl_fills"] == pytest.approx(48.0)
    quiet = {d["size"]: d for d in score.market_day(GOLD, recorded(GOLD, T0 + 60.0, 120), TERMS, 0.0)}[100]
    assert lost["reward_formula"] < quiet["reward_formula"]                # holding the full size, the bid no longer rests and no longer scores
    assert lost["reward_cap_100"] == pytest.approx(min(lost["reward_formula"], 52.0)) and lost["reward_cap_10"] == pytest.approx(5.2)


def test_a_part_of_a_day_is_not_paid_as_a_whole_one():
    late = {d["size"]: d for d in score.market_day(GOLD, recorded(GOLD, T0 + 1800.0, 60), TERMS, 1.0)}[100]       # the first half hour was missed
    assert not late["whole"]
    full = {d["size"]: d for d in score.market_day(GOLD, recorded(GOLD, T0 + 60.0, 120), TERMS, 1.0)}[100]
    assert late["reward_formula"] == pytest.approx(full["reward_formula"] / 2, rel=0.05)
    unseen_close = {d["size"]: d for d in score.market_day(GOLD, recorded(GOLD, T0 + 60.0, 120, closes=False), TERMS, 1.0)}[100]
    assert not unseen_close["whole"]
    assert score.market_day(GOLD, [{**r, "state": "EXPIRED"} for r in recorded(GOLD, T0, 5)], TERMS, 1.0) == []


def test_the_verdict_waits_for_ten_market_days_on_six_dates():
    def day(i, net, program="metals_gold_updown_1d", whole=True, size=rule.JUDGED):
        return {"program": program, "size": size, "whole": whole, "net": net, "day": f"2026-11-{19 + i // 2:02d}"}
    few = pd.DataFrame([day(i, 40.0) for i in range(8)])
    assert score.verdict(few).startswith("NOT YET JUDGED: 8 market-days")
    good = pd.DataFrame([day(i, 40.0 + (i % 3)) for i in range(12)] + [day(i, -500.0, whole=False) for i in range(3)] + [day(i, -500.0, size=500) for i in range(3)]
                        + [day(i, -500.0, program="crypto_btc_updown_1d") for i in range(3)])
    assert score.verdict(good).startswith("PASSES: 12 market-days on 6 dates")
    thin = pd.DataFrame([day(i, 5.0 + (i % 3)) for i in range(12)])
    assert score.verdict(thin).startswith("DOES NOT PASS")              # sure of itself, but under twenty dollars a market-day
    noisy = pd.DataFrame([day(i, 200.0 if i % 2 else -150.0) for i in range(12)])
    assert score.verdict(noisy).startswith("DOES NOT PASS")             # twenty-five dollars on average, and nothing to tell it from luck


class GapUS(FakeUS):
    """The first market closes after three minutes; the window after it starts ten minutes in, and its book appears then."""

    LATER = "cpausp-gold-updown-1d-2026-11-18-2325z"

    def iter_incentives(self, statuses=None):
        self.schedule_reads += 1
        if self.clock.t >= T0 + 180.0:
            return iter([])                                             # between two markets the schedule lists none that is open
        return iter([entry(GOLD, "metals_gold_updown_1d_20261110")])

    def market(self, slug):
        nxt = T0 + 600.0 if slug == GOLD else T0 + 86_400.0
        return {"question": "Gold Up or Down Daily", "endDate": iso(T0 + 1800.0),
                "assetPriceTerms": {"windowStart": iso(T0), "windowEnd": iso(T0 + 180.0), "priceToBeat": {"value": "3852.56", "currency": "USD"},
                                    "nextWindowStart": iso(nxt)}}

    def book(self, slug):
        self.asked.append((round(self.clock.t - T0), slug))
        if slug == self.LATER:
            if self.clock.t < T0 + 600.0:
                raise RuntimeError("404: no such market yet")
            return book()
        return book(state="MARKET_STATE_EXPIRED" if self.clock.t >= T0 + 180.0 else "MARKET_STATE_OPEN")


def read_books(folder, line):
    with gzip.open(folder / "runs" / line["run"] / "books.csv.gz", "rt") as fh:
        return list(csv.DictReader(fh))


def test_the_next_market_is_found_long_after_the_one_before_it_closed(tmp_path):
    clock = Clock(T0)
    us = GapUS(clock)
    line = top.run(tmp_path, minutes=14, us=us, now=clock.now, sleep=clock.sleep, background=False)
    rows = read_books(tmp_path, line)
    later = [r for r in rows if r["slug"] == GapUS.LATER]
    assert later and T0 + 600.0 <= float(later[0]["ts"]) <= T0 + 630.0     # read from the first half minute of its window
    assert line["errors"] == 0                                             # looking for it a minute early is not an error
    asked = [t for t, s in us.asked if s == GapUS.LATER]
    assert min(asked) >= 540                                               # and not looked for before that
    gold = [r for r in rows if r["slug"] == GOLD]
    assert float(gold[-1]["ts"]) <= T0 + 180.0 + top.AFTER + 30.0          # the closed market is left alone meanwhile


def test_a_run_that_starts_between_two_markets_finds_the_next_from_the_last_one_read(tmp_path):
    # an earlier run read the first market to its end
    first = top.run(tmp_path, minutes=4, us=GapUS(Clock(T0)), now=(c := Clock(T0)).now, sleep=c.sleep, background=False)
    assert top.earlier(tmp_path) and list(top.earlier(tmp_path)) == [GOLD]
    # the next run starts five minutes in: nothing is open, and the schedule lists nothing
    clock = Clock(T0 + 300.0)
    us = GapUS(clock)
    line = top.run(tmp_path, minutes=8, us=us, now=clock.now, sleep=clock.sleep, background=False)
    rows = read_books(tmp_path, line)
    assert {r["slug"] for r in rows} == {GapUS.LATER}                      # the old market is not read again
    assert T0 + 600.0 <= float(rows[0]["ts"]) <= T0 + 630.0
    markets = list(csv.DictReader((tmp_path / "runs" / line["run"] / "markets.csv").open()))
    assert [m["slug"] for m in markets] == [GapUS.LATER] and float(markets[0]["pool"]) == 1000.0 and line["markets"] == 1
    assert first["run"] != line["run"] and line["errors"] == 0


def test_earlier_runs_give_the_last_market_of_each_kind(tmp_path):
    for run, slugs in (("20261118T151332Z", [GOLD, "cpc-btc-updown-1d-2026-11-17-2200z"]), ("20261118T201500Z", ["cpc-btc-updown-1d-2026-11-18-2200z", "tec-not-ours-2026-11-18-2200z"])):
        d = tmp_path / "runs" / run
        d.mkdir(parents=True)
        with (d / "markets.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=top.MARKET_FIELDS)
            w.writeheader()
            for s in slugs:
                program = "nba_winner_futures_20261110" if s.startswith("tec") else ("metals_gold_updown_1d_20261110" if "gold" in s else "crypto_btc_updown_1d_20261110")
                w.writerow({"run": run, "slug": s, "program": program, "pool": 400, "target": 10000, "discount": 0.3, "max_spread": 0.03, "period": "daily_event"})
    found = top.earlier(tmp_path)
    assert set(found) == {GOLD, "cpc-btc-updown-1d-2026-11-18-2200z"}       # the later Bitcoin market, and nothing that is not ours
    assert found[GOLD]["target"] == 10000 and found[GOLD]["max_spread"] == 0.03
    assert top.earlier(tmp_path / "nothing-here") == {}


class PricedUS(FakeUS):
    """As the first exchange, and it names the market's asset and serves its reference price in fifteen-second candles."""

    def __init__(self, clock):
        super().__init__(clock)
        self.price_calls = []

    def market(self, slug):
        m = super().market(slug)
        m["assetPriceTerms"]["asset"] = {"assetClass": "ASSET_CLASS_COMMODITY", "symbol": "gold"}
        return m

    def asset_prices(self, assets, start, end=0, bucket="15S"):
        self.price_calls.append((round(self.clock.t - T0), tuple(assets), int(start), bucket))
        first = int(start) - int(start) % 15
        last = int(self.clock.t) - int(self.clock.t) % 15                # the candle in progress is served too
        return {a: [{"ts": ts, "open": 3850.0, "high": 3851.0, "low": 3849.0, "close": 3850.0 + (ts - T0) / 15, "ticks": 14} for ts in range(first, last + 1, 15)] for a in assets}


def test_the_reference_price_is_kept_in_finished_candles_without_gaps_or_repeats(tmp_path):
    clock = Clock(T0)
    us = PricedUS(clock)
    line = top.run(tmp_path, minutes=5, us=us, now=clock.now, sleep=clock.sleep, background=False)
    assert line["errors"] == 0
    with gzip.open(tmp_path / "runs" / line["run"] / "prices.csv.gz", "rt") as fh:
        rows = list(csv.DictReader(fh))
    assert rows and {r["asset"] for r in rows} == {"commodity:gold"}
    stamps = [int(r["ts"]) for r in rows]
    assert stamps == sorted(set(stamps))                                  # each candle once
    assert all(b - a == 15 for a, b in zip(stamps, stamps[1:]))           # and none missed between two sweeps
    assert max(stamps) + 15 <= clock.t                                    # the candle in progress is never written down
    assert float(rows[-1]["close"]) == 3850.0 + (stamps[-1] - T0) / 15 and rows[0]["ticks"] == "14"
    assert all(c[3] == "15S" and c[1] == ("commodity:gold",) for c in us.price_calls) and len(us.price_calls) <= line["cycles"]
    markets = {r["slug"]: r for r in csv.DictReader((tmp_path / "runs" / line["run"] / "markets.csv").open())}
    assert markets[GOLD]["asset"] == "commodity:gold"


def test_a_failing_price_feed_does_not_stop_the_books(tmp_path):
    class Broken(PricedUS):
        def asset_prices(self, *a, **k):
            raise RuntimeError("503")

    clock = Clock(T0)
    line = top.run(tmp_path, minutes=3, us=Broken(clock), now=clock.now, sleep=clock.sleep, background=False)
    assert line["books"] >= 5 and line["errors"] >= 1
    with gzip.open(tmp_path / "runs" / line["run"] / "prices.csv.gz", "rt") as fh:
        assert list(csv.DictReader(fh)) == []


def test_a_last_tick_order_is_paid_half_the_pool_for_the_time_it_makes_the_book_qualify():
    # an hour: for the first half the book qualifies as it is; then the bids go and 6,900 stay offered at 3c
    rows = recorded(GOLD, T0 + 60.0, 120)
    for r in rows[60:120]:
        r["bids"], r["asks"] = "", "0.03:6900"
    d = score.last_tick_day(GOLD, rows, TERMS, 0.0)
    assert d["whole"] and d["fills"] == 0 and d["bought"] == 0
    assert d["resting"] == pytest.approx(0.5, abs=0.01)
    assert d["reward_formula"] == pytest.approx(1000.0 * 0.5 * 0.5, rel=0.02)        # half the hour, and the bid side is half of each second's pay
    assert d["net"] == pytest.approx(d["reward_paid"]) and d["pnl_fills"] == 0.0
    # while the book qualifies without us nothing rests: a day like that earns nothing here
    quiet = score.last_tick_day(GOLD, recorded(GOLD, T0 + 60.0, 120), TERMS, 0.0)
    assert quiet["resting"] == 0.0 and quiet["reward_paid"] == 0.0 and quiet["net"] == 0.0


def test_a_last_tick_fill_costs_a_cent_a_contract_and_stops_at_the_target():
    # somebody sells 9,000 at a cent in two lots: the order is filled for 5,000 and again for its whole 5,000? No: after the target has been bought it stops
    rows = recorded(GOLD, T0 + 60.0, 120, bids="", asks="0.03:6900", traded=lambda i: 0.0 if i < 10 else (4000.0 if i < 20 else 9000.0),
                    notional=lambda i: 0.0 if i < 10 else (40.0 if i < 20 else 90.0))
    lost = score.last_tick_day(GOLD, rows, TERMS, 0.0)
    assert lost["bought"] == 9000.0 and lost["fills"] == 2                        # 4,000, then the whole order once more: it rested while under the target
    assert lost["pnl_fills"] == pytest.approx(-90.0)
    assert lost["resting"] < 0.2                                                  # and nothing after that
    won = score.last_tick_day(GOLD, rows, TERMS, 1.0)
    assert won["pnl_fills"] == pytest.approx(9000.0 * 0.99)                       # the contracts bought at a cent are not always worthless
    assert score.last_tick_day(GOLD, [{**r, "state": "EXPIRED"} for r in recorded(GOLD, T0, 5)], TERMS, 1.0) is None


def test_the_last_tick_verdict_asks_for_money_on_several_days_and_cheap_fills():
    def day(i, reward, pnl=0.0, program="metals_gold_updown_1d", whole=True):
        return {"program": program, "whole": whole, "reward_paid": reward, "pnl_fills": pnl, "net": reward + pnl, "day": f"2026-11-{19 + i // 2:02d}"}
    assert score.verdict_last_tick(pd.DataFrame()).startswith("NOT YET JUDGED")
    assert score.verdict_last_tick(pd.DataFrame([day(i, 100.0) for i in range(8)])).startswith("NOT YET JUDGED: 8 market-days")
    good = pd.DataFrame([day(i, 120.0 if i % 2 else 0.0, -10.0 if i % 4 == 1 else 0.0) for i in range(12)])
    assert score.verdict_last_tick(good).startswith("PASSES: 12 market-days on 6 dates")
    one_big_day = pd.DataFrame([day(i, 600.0 if i == 0 else 0.0) for i in range(12)])
    assert score.verdict_last_tick(one_big_day).startswith("DOES NOT PASS")          # fifty dollars a market-day, all of it from one
    costly = pd.DataFrame([day(i, 100.0, -40.0) for i in range(12)])
    assert score.verdict_last_tick(costly).startswith("DOES NOT PASS")               # sixty a market-day, but the fills take two fifths of the reward
    small = pd.DataFrame([day(i, 10.0) for i in range(12)])
    assert score.verdict_last_tick(small).startswith("DOES NOT PASS")
