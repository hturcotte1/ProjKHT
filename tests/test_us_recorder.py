import csv
import gzip
import json

import pytest

from kht.trading.twins import norm, pair_all, pair_event
from kht.trading.us_recorder import SNAPSHOT_FIELDS, gaps, parse_book, record, reward_state, reward_walk


def intl_market(mid, label, question="", outcomes=("Yes", "No")):
    return {"id": mid, "groupItemTitle": label, "question": question or f"Will {label} win?", "outcomes": json.dumps(list(outcomes)),
            "clobTokenIds": json.dumps([f"yes-{mid}", f"no-{mid}"]), "conditionId": f"0x{mid}"}


# ------------------------------------------------------------------ pairing
def test_norm_drops_case_accents_and_punctuation_but_keeps_what_changes_a_number():
    assert norm("  2028 Républican  Presidential Nominee? ") == "2028 republican presidential nominee"
    assert norm("70+") != norm("70")
    assert norm("<1.2M") != norm("1.2M") and norm("1.2M") != norm("12M")
    assert norm("1,200,000") == norm("1200000")
    assert norm("J.D. Vance") == norm("J D Vance")


def test_markets_pair_only_when_the_title_and_the_label_are_the_same():
    us = {"title": "Alaska Senate Election Winner", "markets": [{"slug": "ak-dem", "title": "Mary Peltola (D)"}, {"slug": "ak-rep", "title": "Dan Sullivan (R)"}]}
    intl = {"id": "9", "title": "Alaska Senate Election winner", "negRisk": True,
            "markets": [intl_market("1", "Mary Peltola (D)"), intl_market("2", "Sen. Dan Sullivan (R)")]}
    twins = pair_all([us], [intl])
    assert set(twins) == {"ak-dem"}                        # "Sen. Dan Sullivan (R)" is not the same label, so it is left alone
    tw = twins["ak-dem"]
    assert (tw.intl_id, tw.token_yes, tw.rule, tw.neg_risk) == ("1", "yes-1", "label", True)


def test_thresholds_are_not_paired_with_ranges_even_under_one_title():
    us = {"title": "Alabama Senate Election: Turnout", "markets": [{"slug": "al-gt12", "title": "Above 1.2M"}]}
    intl = {"id": "9", "title": "Alabama Senate Election: Turnout", "markets": [intl_market("1", "<1.2M"), intl_market("2", "1.2M-1.3M")]}
    assert pair_all([us], [intl]) == {}


def test_a_single_question_pairs_with_a_single_question_and_not_with_one_of_several():
    us = {"title": "GPT-6 released?", "markets": [{"slug": "gpt6", "title": ""}]}
    one = {"id": "5", "title": "GPT-6 released?", "markets": [intl_market("7", "")]}
    several = {"id": "6", "title": "GPT-6 released?", "markets": [intl_market("8", "June 30"), intl_market("9", "December 31")]}
    assert pair_event(us, [several]) == []
    assert [t.intl_id for t in pair_event(us, [several, one])] == ["7"]
    assert pair_event(us, [one])[0].rule == "single"


def test_of_two_events_with_the_same_title_the_one_that_pairs_more_answers_wins_then_the_nearer_end_date():
    us = {"title": "Fed Decision", "endDate": "2026-12-10T00:00:00Z", "markets": [{"slug": "cut", "title": "25 bps decrease"}, {"slug": "hold", "title": "No change"}]}
    old = {"id": "1", "title": "Fed decision", "endDate": "2026-09-17T00:00:00Z", "markets": [intl_market("a", "25 bps decrease"), intl_market("b", "No change")]}
    new = {"id": "2", "title": "Fed decision", "endDate": "2026-12-09T00:00:00Z", "markets": [intl_market("c", "25 bps decrease"), intl_market("d", "No change")]}
    thin = {"id": "3", "title": "Fed decision", "endDate": "2026-12-10T00:00:00Z", "markets": [intl_market("e", "No change"), intl_market("f", "Other")]}
    assert {t.intl_id for t in pair_event(us, [old, new, thin])} == {"c", "d"}


def test_a_label_used_twice_and_a_twin_claimed_twice_pair_with_nothing():
    us = {"title": "Race", "markets": [{"slug": "a", "title": "Smith"}]}
    intl = {"id": "1", "title": "Race", "markets": [intl_market("1", "Smith"), intl_market("2", "Smith")]}
    assert pair_all([us], [intl]) == {}
    us2 = {"title": "Race", "markets": [{"slug": "b", "title": "Jones"}, {"slug": "c", "title": "Jones"}]}
    intl2 = {"id": "2", "title": "Race", "markets": [intl_market("3", "Jones"), intl_market("4", "Other")]}
    assert pair_all([us2], [intl2]) == {}


def test_markets_that_are_not_yes_no_are_never_twins():
    us = {"title": "Game", "markets": [{"slug": "a", "title": "Lakers"}]}
    intl = {"id": "1", "title": "Game", "markets": [intl_market("1", "Lakers", outcomes=("Lakers", "Celtics")), intl_market("2", "Other")]}
    assert pair_all([us], [intl]) == {}


# ------------------------------------------------------------------ the book
BOOK = {"marketSlug": "m", "state": "MARKET_STATE_OPEN",
        "bids": [{"px": {"value": "0.0100"}, "qty": "499.01"}, {"px": {"value": "0.0200"}, "qty": "1.0000"}, {"px": {"value": "0.0150"}, "qty": "0"}],
        "offers": [{"px": {"value": "0.0800"}, "qty": "2.01"}, {"px": {"value": "0.0700"}, "qty": "20"}, {"px": {"value": "0.12"}, "qty": "63"},
                   {"px": {"value": "0.58"}, "qty": "56"}],
        "stats": {"lastTradePx": {"value": "0.0100"}, "lastTradeQty": "1.0", "sharesTraded": "420.03", "openInterest": "15.04",
                  "lastTradeSetTime": "2026-11-07T03:13:15.397628394Z"}}


def test_parse_book_puts_the_best_price_first_and_ignores_empty_levels():
    row = parse_book(BOOK)
    assert (row["bid1"], row["bid_qty1"], row["bid2"], row["bid3"]) == (0.02, 1.0, 0.01, None)
    assert (row["ask1"], row["ask_qty1"], row["ask2"], row["ask3"]) == (0.07, 20.0, 0.08, 0.12)
    assert (row["bid_levels"], row["ask_levels"], row["bid_total"], row["ask_total"]) == (2, 4, 500.01, 141.01)
    assert (row["last"], row["traded"], row["state"], row["last_ts"]) == (0.01, 420.03, "OPEN", "2026-11-07T03:13:15")


def test_an_empty_side_of_the_book_is_empty_not_a_price():
    row = parse_book({"bids": [], "offers": [{"px": {"value": "0.01"}, "qty": "600000"}], "stats": {}})
    assert row["bid1"] is None and row["bid_qty1"] is None and row["ask1"] == 0.01


def test_gaps_are_measured_after_the_fee_and_need_the_quote_on_the_right_side():
    row = {"ask1": 0.61, "bid1": 0.60, "intl_bid": 0.86, "intl_ask": 0.89}
    yes, no = gaps(row)
    assert yes == pytest.approx(0.86 - 0.61 - 0.095 * 0.61 * 0.39)      # "Yes" is 25c cheaper on US, less the fee
    assert no < 0                                                       # and "No" is not
    assert gaps({"ask1": None, "bid1": 0.06, "intl_bid": None, "intl_ask": 0.007}) == (None, pytest.approx(0.06 - 0.007 - 0.095 * 0.06 * 0.94))


# ------------------------------------------------------------------ rewards
def test_the_walk_scores_orders_up_to_the_target_size_and_nothing_beyond_it():
    bids = [(0.30, 1000.0), (0.29, 1000.0), (0.28, 1000.0), (0.27, 1000.0)]
    at, score = reward_walk(bids, target=2500, discount=0.30)
    assert at == 0.28                                         # the target is reached inside the third level
    assert score == pytest.approx(1000 + 300 + 90)            # the exchange's own example; the fourth level scores nothing
    assert reward_walk(bids, target=5000, discount=0.30)[0] is None      # a side smaller than the target is not paid
    assert reward_walk([], 500, 0.3) == (None, 0.0)


def test_a_far_order_makes_the_side_reach_the_target_but_earns_almost_none_of_it():
    asks = [(0.07, 20.0), (0.99, 500.0)]
    at, score = reward_walk(asks, target=500, discount=0.25)
    assert at == 0.99 and score == pytest.approx(20.0, abs=1e-6)


def test_with_a_maximum_spread_both_sides_must_reach_the_target_close_together():
    book = lambda bid, ask: {"bids": [{"px": {"value": str(bid)}, "qty": "500"}], "offers": [{"px": {"value": str(ask)}, "qty": "500"}]}  # noqa: E731
    prog = {"program": "p", "pool": 40.0, "target": 500, "discount": 0.25, "max_spread": 0.06}
    assert (reward_state(book(0.81, 0.93), prog)["rw_bid_ok"], reward_state(book(0.81, 0.93), prog)["rw_ask_ok"]) == (1, 1)    # exactly 12c apart still pays
    assert (reward_state(book(0.01, 0.99), prog)["rw_bid_ok"], reward_state(book(0.01, 0.99), prog)["rw_ask_ok"]) == (0, 0)
    one_sided = {"bids": [{"px": {"value": "0.95"}, "qty": "600"}], "offers": []}
    assert reward_state(one_sided, prog)["rw_bid_ok"] == 0                                   # nobody is paid, the full side included
    free = dict(prog, max_spread=None)
    assert (reward_state(one_sided, free)["rw_bid_ok"], reward_state(one_sided, free)["rw_ask_ok"]) == (1, 0)
    assert reward_state(book(0.01, 0.99), free)["rw_bid_at"] == 0.01


# ------------------------------------------------------------------ a cycle
class FakeUS:
    def __init__(self):
        self.asked = []

    def iter_events(self, **f):
        if f["categories"] != "politics":
            return iter(())
        quote = lambda v: {"value": v} if v else None                 # noqa: E731
        mk = lambda slug, label, bid, ask: {"slug": slug, "id": slug.upper(), "title": label, "question": "Who wins?", "category": "politics",  # noqa: E731
                                            "marketType": "futures", "endDate": "2027-01-15T00:00:00Z", "orderPriceMinTickSize": 0.01,
                                            "feeCoefficient": 0.095, "bestBidQuote": quote(bid), "bestAskQuote": quote(ask)}
        return iter([{"id": "E1", "title": "Minnesota Senate Special Election Winner", "endDate": "2027-01-15T00:00:00Z",
                      "markets": [mk("mn-dem", "Democratic Party", "0.60", "0.61"), mk("mn-rep", "Republican Party", "0.19", None),
                                  mk("mn-oth", "Other", None, None)]}])

    def iter_markets(self, **f):
        return iter(())

    def iter_incentives(self, **f):
        period = {"programId": "politics_mid", "programType": "liquidityProgram", "status": "active", "period": "daily_event", "rewardPool": 75,
                  "discountFactor": 0.2, "targetSize": 100}
        return iter([{"marketSlug": "mn-dem", "category": "POL", "timePeriods": [period]}, {"marketSlug": "mn-rep", "category": "POL", "timePeriods": [period]},
                     {"marketSlug": "mn-oth", "category": "POL", "timePeriods": [period]},
                     {"marketSlug": "a-game", "category": "SPR", "timePeriods": [dict(period, programId="nba_live")]}])

    def book(self, slug):
        self.asked.append(slug)
        if slug == "mn-dem":
            return {"bids": [{"px": {"value": "0.60"}, "qty": "40"}], "offers": [{"px": {"value": "0.61"}, "qty": "17"}], "stats": {}, "state": "MARKET_STATE_OPEN"}
        return {"bids": [{"px": {"value": "0.19"}, "qty": "103"}], "offers": [], "stats": {}, "state": "MARKET_STATE_OPEN"}


class FakeIntl:
    def iter_events(self, **f):
        return iter([{"id": "77", "title": "Minnesota Senate special election winner",
                      "markets": [dict(intl_market("11", "Democratic Party"), lastTradePrice=0.87), intl_market("12", "Republican Party")]}])

    def books(self, tokens):
        assert tokens == ["yes-11", "yes-12"]
        return [{"asset_id": "yes-11", "bids": [{"price": "0.80", "size": "5"}, {"price": "0.86", "size": "300"}], "asks": [{"price": "0.89", "size": "150"}]},
                {"asset_id": "yes-12", "bids": [], "asks": [{"price": "0.13", "size": "900"}]}]


def test_a_cycle_writes_the_books_the_twins_and_a_status_and_only_appends_to_the_directories(tmp_path):
    us = FakeUS()
    line = record(tmp_path, us=us, intl=FakeIntl(), now=1_794_300_000)
    assert sorted(us.asked) == ["mn-dem", "mn-rep"]                    # the market with no quote is not asked for
    assert (line["books_read"], line["two_sided"], line["twins"], line["twins_both_books"]) == (2, 1, 2, 1)
    assert (line["us_cheaper_yes"], line["us_cheaper_no"]) == (1, 0)
    snap = next((tmp_path / "snapshots").glob("*/*.csv.gz"))
    rows = {r["slug"]: r for r in csv.DictReader(gzip.open(snap, "rt"))}
    assert list(rows["mn-dem"]) == SNAPSHOT_FIELDS
    assert (rows["mn-dem"]["ask1"], rows["mn-dem"]["ask_qty1"], rows["mn-dem"]["intl_bid"], rows["mn-dem"]["intl_bid_qty"]) == ("0.61", "17.0", "0.86", "300.0")
    assert rows["mn-dem"]["intl_last"] == "0.87"
    assert rows["mn-rep"]["ask1"] == "" and rows["mn-rep"]["intl_bid"] == "" and rows["mn-rep"]["intl_ask"] == "0.13"
    status = (tmp_path / "STATUS.md").read_text()
    assert "Democratic Party" in status and "No orders are placed" in status
    # rewards: the programme wants 100 contracts a side; only the Republican bid (103) has them
    assert (rows["mn-dem"]["rw_program"], rows["mn-dem"]["rw_bid_ok"], rows["mn-dem"]["rw_ask_ok"]) == ("politics_mid", "0", "0")
    assert (rows["mn-rep"]["rw_bid_ok"], rows["mn-rep"]["rw_ask_ok"], rows["mn-rep"]["rw_bid_at"]) == ("1", "0", "0.19")
    prog = list(csv.DictReader((tmp_path / "rewards.csv").open()))
    assert len(prog) == 1                                             # the sports programme is not followed
    assert (prog[0]["program"], prog[0]["markets"], prog[0]["books"], prog[0]["bid_sides_paid"], prog[0]["ask_sides_paid"]) == ("politics_mid", "3", "2", "1", "0")
    assert (prog[0]["events"], prog[0]["events_with_none"]) == ("1", "0")
    assert "politics_mid" in status
    record(tmp_path, us=FakeUS(), intl=FakeIntl(), now=1_794_300_000 + 14_400)
    assert len(list(csv.DictReader((tmp_path / "markets.csv").open()))) == 2      # the same two markets, written once
    assert len(list(csv.DictReader((tmp_path / "twins.csv").open()))) == 2
    assert len(list(csv.DictReader((tmp_path / "log.csv").open()))) == 2
    assert len(list(csv.DictReader((tmp_path / "rewards.csv").open()))) == 2
    assert len(list((tmp_path / "snapshots").glob("*/*.csv.gz"))) == 2


def test_the_us_books_are_kept_when_polymarket_com_cannot_be_reached(tmp_path):
    class Down:
        def iter_events(self, **f):
            raise RuntimeError("no route")

    line = record(tmp_path, us=FakeUS(), intl=Down(), now=1_794_300_000)
    assert (line["books_read"], line["twins"], line["errors"]) == (2, 0, 1)
