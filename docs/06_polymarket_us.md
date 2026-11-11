# 06 — Polymarket US, and a wide search with a judge it cannot reach

*Started 11 November 2026. Sections 1 to 4 were written and committed before
any Polymarket US outcome had been tabulated; the commit time is the evidence.
Results are added from section 5 on.*

## 1. Why this round exists

Two things changed.

**The venue.** The account will be on Polymarket US, because that is where
its owner lives. Polymarket US is not polymarket.com with a different login.
It is a separate exchange, regulated by the CFTC, with its own markets, order
books, fees, crowd and API. Everything in rounds one to three was measured on
polymarket.com. None of it is known to hold on the US exchange, and section 2
shows that most of what the confirmed rule traded does not exist there.

**The method asked for.** The owner's proposal: backtest and paper trade
thousands of strategies and keep what is most viable. Done naively that is
the surest way to lose money that statistics offers. Among thousands of rules
with no edge at all, the best few will show t-statistics near 4, and this
project fooled itself three times in round two with far fewer tries than
that. Done with a wall between the search and the judge, it is a good way to
find things nobody thought to look for. This document fixes the wall first.

## 2. What Polymarket US is, measured on 11 November 2026

From its public gateway (`https://gateway.polymarket.us`, no key needed;
`src/kht/api/polymarket_us.py`), its documentation (docs.polymarket.us) and
its fee schedule.

| | Polymarket US | polymarket.com, for comparison |
|---|---|---|
| Open markets | 73,798, of which 63,870 sports, 4,985 politics, 2,409 culture, 1,510 crypto, 507 macro, 239 technology, 173 climate, 68 finance, 27 geopolitics | news markets in every category; geopolitics alone was half of the confirmed rule's trades |
| Quoted on both sides right now | 40,663, of which 37,914 sports | |
| Settled markets | over 400,000 crypto (nearly all hourly and shorter price ladders), 6,317 climate, 3,065 finance, 2,795 culture, 2,731 politics, 990 macro, 104 technology; sports counted in section 5 | 160,000 with tapes on disk |
| History | Sports from November 2025; everything else from spring 2026; the midterm elections of 3 November 2026 are four-fifths of the politics | three years |
| Shape of a market | Almost every market is one answer to a question with several answers: a candidate in a race, a temperature bracket, a price rung, a team. Stand-alone "will this happen by a date?" questions are rare | the confirmed rule lives on stand-alone "by a date" questions |
| Taker fee | 0.095 × price × (1 − price) a contract for an account under $10,000 of monthly volume: 0.36¢ at 96¢, 2.4¢ at 50¢ | 0 to 0.07 × price × (1 − price): at most 0.15¢ at 96¢ in politics, nothing in geopolitics |
| Maker fee | none (and no rebate below $10 million a month) | none |
| Tick, smallest order | 1¢ (0.5¢ and 0.1¢ on some); 0.01 of a contract | 1¢ or 0.1¢; 5 shares |
| Public data | every market's settlement; the order book's best prices on both sides, minute by minute, for any past day; one point a day for a market's whole life; total shares traded | every trade ever made |
| Not public | individual trades | |

Three consequences.

1. **The confirmed rule has almost nothing to buy there.** It buys "No" on a
   stand-alone question about whether something dramatic will happen by a
   date. Polymarket US lists 27 geopolitics markets. What it lists instead
   are races, brackets, ladders and games, where rounds one to three found
   the edge weak (the leader), absent (the also-rans) or absent (sports).
2. **Paying the ask costs two to three times more.** A rule that earned 1.6¢
   a share at 96¢ on polymarket.com keeps about 1.2¢ there after the US fee,
   if the same mistake exists there at all. In the middle of the price range
   the fee alone is 2.4¢, which rules out almost anything that pays the ask.
   Resting orders pay nothing, so anything that works there is likely to
   work by waiting.
3. **The history is short and lumpy.** Five to eight months of non-sports
   markets, dominated by one election night. Sports are a year of
   independent games. Tests on US data will be weak for everything except
   sports and the daily markets (weather, fuel prices, weekly charts).

## 3. The search space

A strategy here is a rule of one fixed form, so that thousands of them can be
generated, run and counted:

> In markets of family F, buy side S when its ask is in band B, with time T
> left, spread at most W, and condition C on how it got there. Buy at the
> next observed ask if it is still in the band. Pay the venue's fee. Hold to
> settlement. One purchase per market.

| Part | Values |
|---|---|
| Family | category, crossed with the shape of the market: a stand-alone question, the leader of a question with several answers, one of the rest |
| Side | "Yes", "No" |
| Price band | a ladder of bands from 2¢ to 99¢, narrow and wide |
| Time left | from hours to six months, in bands |
| Spread | at most 1¢, 2¢, 3¢, 5¢, or any |
| How it got there | no condition; quiet (little movement over the last week or two); just rose; just fell |

The exact grid is the code in `scripts/factory.py`; the number of rules it
generates is printed with every result, and every one of them counts as a
test. Exits other than holding, resting orders, and position sizing are left
out of the search on purpose: each multiplies the count, and rounds one to
three found that none of them changes which contracts are worth holding.

What the search cannot contain is anything that needs hindsight. A market's
final volume, how long it turned out to live, and whether it later qualified
for something else were the three mistakes of round three. Liquidity is
measured by the spread at the time. Universes are built by
`scripts/at_the_time.py`.

## 4. The judge, fixed before the search is run

**Three stages, each on data the one before it never touched.**

*Stage 1: search on polymarket.com.* Three years, 110,000 news markets with
tapes, plus sports. Split by time on each market's scheduled end:

- discovery: markets scheduled to end before 1 January 2026;
- validation: markets scheduled to end from 1 January 2026.

A rule goes forward if, in discovery, it has at least 150 trades, a mean
return after fees of at least +0.5% a trade, and a t-statistic of at least
3.0 clustered by event. Call these the candidates. Each candidate is then run
on validation, where it gets a one-sided p-value from a t-statistic clustered
by week of entry. Candidates that pass the Benjamini–Hochberg procedure at a
false-discovery rate of 10% across all candidates, with at least 100
validation trades, are the survivors of stage 1.

*Stage 2: confirmation on Polymarket US.* Every stage 1 survivor is run
unchanged on the settled markets of Polymarket US (scheduled to end by
10 November 2026), with the US fee at 0.095. Same procedure:
Benjamini–Hochberg at 10% across the survivors, at least 100 trades,
clustered by day of settlement, because one election night settles
thousands of markets at once. What passes is **confirmed on the venue's own
history**.

*Stage 2b: a search on Polymarket US alone,* for the families that barely
exist on polymarket.com or have enough data of their own (sports, weather
brackets, daily price ladders, weekly charts). Discovery is markets ending by
15 September 2026, validation from 16 September to 10 November 2026, same
thresholds and same procedure.

*Stage 3: forward.* Whatever passes stage 2 or 2b is written to a rulebook
file with the date, and scored on markets that settle afterwards. Polymarket
US keeps its order-book history, so the rulebook can be scored on any later
day without a logger of our own; a handful of rules also get paper accounts,
to exercise the placing and filling of orders. **Only stage 3 can make a
rule eligible for real money.**

**How many discoveries to expect from nothing.** The whole funnel is also run
on placebo outcomes: every contract's result redrawn at random with the
chance its own price implies, so that prices are exactly right and every rule
loses its costs. The number of rules that "survive" on placebo data, averaged
over 100 redraws, is reported next to the number that survive on the real
data. If the two are close, nothing has been found.

**What will be reported whatever happens:** the number of rules generated,
candidates, survivors at each stage, the placebo counts, and for every
survivor its trades, return and t-statistic in each stage and by year. A
round in which nothing survives is a result and will be written up as one.

**What a survivor is not.** It is not a tuned rule. Its parameters are grid
points; nothing is adjusted after stage 1. And it is not a prediction of
profit: with five months of US history, stage 2 can confirm that a mistake
exists there, not what it will be worth.

### The judge, corrected on its first run (11 November, 04:40 UTC)

The judge above was run once on polymarket.com as written and had to be
changed, before any Polymarket US data was looked at. What happened is part
of the record.

*As written* it passed 351 candidates and 285 survivors. It also passed 1.6
survivors on average in placebo worlds, with at least one in half of them,
which is far more than a 10% false-discovery rate allows. The cause was the
one round two met as test A1: a rule that buys at 98¢ and happens not to lose
in the sample has returns that hardly vary, so its t-statistic is enormous
(the top survivor scored 99.97) whether or not there is anything there.

*A first repair* floored the variance at what fair prices would imply, with
every bet in one event assumed to win or lose together. That let nothing
through, the first round's confirmed rule included, and was too strict: it
is only true of some events.

*The judge as it now stands,* and as it will be applied to Polymarket US:

- **The score.** z = mean return ÷ standard error, where the variance of the
  mean is the larger of the sample's clustered variance and the variance the
  prices paid would imply if they were fair (a purchase at cost c has a
  return of variance (1 − c)/c). A rule cannot score well by not having
  lost yet.
- **Candidates,** as before: in discovery, 150 trades or more, +0.5% a trade
  or more, z of 3.0 or more by event.
- **Survivors.** The candidates' purchases are fixed. Their outcomes in the
  validation half are redrawn 500 times in a world where every price is
  right, one draw per *event*, so that markets in one event win and lose
  together as much as their prices allow. In each world the best validation
  z among the candidates is recorded. A candidate survives if its real
  validation z, on 100 trades or more, is above the 95th percentile of those
  best scores. This asks one plain question: did it beat the luckiest of
  that many worthless rules?
- **Discoveries from nothing,** as before: the whole funnel run in placebo
  worlds, counting what gets through.

Every change makes the judge stricter than the one first written. Nothing
that failed the first version passes this one.

## 5. Stage 1: 53,760 rules on polymarket.com

`scripts/factory.py run-intl` (`f_intl_*.csv`, `factory_intl_output.txt`).
The table is every news market with tapes on disk from the moment it had
traded 5,000 shares: 110,986 markets, 2.6 million outcome-days, split almost
evenly between markets scheduled to end before 2026 (discovery) and in 2026
(validation). The fast engine was first checked against the backtest used in
every earlier round and bought exactly the same contracts on four rules.

| | Real data | Worlds with no edge |
|---|---:|---:|
| Rules in the grid | 53,760 | |
| With 30 trades or more | 28,382 | |
| Candidates | **76** | 6.7 on average, 30 at most |
| Score a candidate must beat in validation | z ≥ 3.21 | (median best score 1.87) |
| Survivors | **32** | 0.1 on average; one world in twenty had any |

The search was wide and what it found is narrow. **All 76 candidates, and so
all 32 survivors, are the same thing: "No" on a stand-alone question.** Not
one rule on the "Yes" side, not one on a leg of a multi-way event, not one in
the middle of the price range, in any category, made it through the first
half of the data. The survivors come in two kinds, both already known:

| Rule (one of each kind; the rest are neighbours) | Discovery: trades | return | z | Validation: trades | return | z | lost |
|---|---:|---:|---:|---:|---:|---:|---:|
| "No" at 90–99¢, 10–60 days left, spread 2¢ or less | 2,208 | +1.51% | 3.1 | 2,274 | +2.42% | 4.2 | 61 |
| "No" at 95–99¢, 3–60 days, quiet for a week | 1,532 | +1.23% | 3.0 | 1,120 | +1.78% | 4.0 | 5 |
| "No" at 90–98¢, 60–180 days left | 912 | +2.92% | 3.4 | 470 | +4.94% | 4.0 | 9 |
| "No" at 90–95¢, 60–180 days left | 744 | +3.62% | 3.6 | 413 | +5.44% | 4.0 | 9 |
| "No" at 80–95¢, 60–180 days, quiet, spread 2¢ or less | 493 | +4.96% | 3.5 | 219 | +7.91% | 3.8 | 3 |

The grid as a whole says the same thing more bluntly. Among the 6,140 rules
with enough trades in both halves to judge:

| What the rule buys | Rules | Made money in both halves | Lost money in both halves |
|---|---:|---:|---:|
| "No" on a stand-alone question | 2,000 | 77% | 1% |
| "Yes" on a stand-alone question | 1,350 | 1% | 89% |
| "No" on one answer of a multi-way event | 1,682 | 14% | 39% |
| "Yes" on one answer of a multi-way event | 1,108 | 14% | 39% |

Whatever band, horizon, spread, category or condition is chosen, "No" on a
stand-alone question tends to pay and "Yes" tends to lose: 124 rules lose
reliably in both halves (z of −3 or worse), and every one of them buys
"Yes" on a stand-alone question. In multi-way events neither side has
anything.

Two things this settles and one it does not.

*The long-dated "No" is now confirmed on polymarket.com.* Round three found
it by looking and could only test it in the thinnest markets, where it fell
short. Here it was found in the pre-2026 half by a blind search and held in
the 2026 half against a family-wise bar. Twenty-three of the 32 survivors
are versions of it.

*A tight spread matters.* The plain first-round rule ("No" at 95–98¢, 3–60
days, any spread) is not a candidate in this pooled universe, which includes
the thin markets where round three found it weak: +0.74% in discovery, z of
1.2. With a spread of 2¢ or less and ten days or more to run it is. Round
three's after-the-fact note about spreads was right.

*Nothing new was found.* Thousands of rules were tried so that something
unexpected could show up, and nothing did. That is worth knowing: the one
mistake this crowd makes that survives costs is believing things will
happen.

## 6. Stage 2: the survivors on Polymarket US

`scripts/factory.py build-us` and `confirm-us` (`f_us_confirmation*.csv`).
The US table is every settled non-sports market that showed a real price on
at least one side on at least one day: 11,967 markets in 2,633 events,
settled on 195 days from 12 April to 10 November 2026, one row per outcome
per day, bought at the next day's ask with the US fee. 9,334 of those
markets showed a real book on both sides on some day. What "real" means was
learned the hard way and is in section 7.

**None of the 32 rules is confirmed. The honest reading is that Polymarket
US cannot say either way.**

Carrying a rule over needs the US equivalent of "a stand-alone question",
and the gateway has no flag for it, so each market's shape is read from what
is known without the result (`us_shape`):

| Shape | Settled markets | With a two-sided book on some day | What they are |
|---|---:|---:|---|
| a single question, or a dated rung of one | 209 | 160 | "Putin meets with Zelenskyy? By September 30", "GPT-6 released?", a referendum |
| separate questions under one heading | 2,556 | 1,767 | thresholds ("gas above $4.07"), "who will be announced out", but also races the prices could not identify |
| one answer of several, only one of which can be right | 8,208 | 6,597 | temperature brackets, chart positions, candidates |
| too thinly quoted to tell | 994 | 810 | |

| Version of the US table | Rules with 100 trades | Bar | Best score | Confirmed |
|---|---:|---:|---:|---:|
| As first coded: "stand-alone" is any market whose event's prices did not add to one that day | 19 of 32 | z ≥ 2.79 | 1.41 | 0 |
| Shapes corrected: "stand-alone" is the first two rows above | 8 of 32 | z ≥ 2.59 | 2.10 | 0 |
| Shapes corrected, and prices at the two ends of the range treated as no price (section 7) | 8 of 32 | z ≥ 2.53 | 2.15 | 0 |
| Strict: the first row only | none; the most any rule gets is 37 | | | cannot be judged |

The first version was wrong in a way the losing trades made obvious: it
counted candidates and contestants as stand-alone questions ("Big Brother
2nd place: Taylor Brown"), which is the one family stage 1 found nothing in.
The third fixes an error in the prices themselves. Both corrections were made
after a result had been seen, and all the versions are reported for that
reason. None of them confirms anything.

On the final table 30 of the 32 rules made money, the average is +2.4% a
trade, and the best has z of 2.15 on 127 trades with two losses. Under the
strict mapping no rule has more than 37 trades, and not one of those trades
lost. That is the right direction and nowhere near a test.

Two things about the venue came out of the losing trades.

- **Markets can be closed early at 50¢.** 78 settled markets paid something
  between 0 and 1. Fifty-three of them were the "2028 vice-presidential
  nominee" markets, listed on 22 September, closed on 20 October and paid
  50¢ to both sides. Anyone who had bought a long shot's "No" at 98¢ lost
  half of it. polymarket.com has nothing like this in three years of data.
  It is a risk that falls hardest on exactly the contracts this project
  buys.
- **The tick is a cent.** Most US markets cannot be quoted between 99¢ and
  $1, so near-certain contracts pile up at 98¢ and 99¢. Of the 342
  purchases of the most active rule carried over, 158 were at 98¢, where a
  win pays 1.8% after the fee. None could be made at 99¢, for the reason in
  section 7.

## 7. Stage 2b: the search on Polymarket US alone

`scripts/factory.py run-us` (`f_us_*.csv`, `factory_us_output.txt`).
Discovery is markets ending before 16 September 2026, validation from then
to 10 November.

**Nothing passes. The first run said eighteen rules did. They were an
artefact of the price feed, and this section replaces the one that reported
them.**

| | First run | With prices at the ends treated as no price | Worlds with no edge |
|---|---:|---:|---:|
| Rules with 30 trades or more | 11,355 | 11,346 | |
| Candidates | 18 | **0** | 0.2 on average |
| Survivors | 18 | **0** | none in twenty worlds |

### The eighteen that were not there

All eighteen were one rule with small variations: buy "No" at about 99¢ on
one answer of several, with one to three days left. Mostly temperature
brackets. Discovery: 3,245 trades, 4 lost, +0.90% a trade (z 5.1).
Validation: 2,333 trades, 4 lost, +1.18% (z 4.9). It passed the judge of
section 4 cleanly.

The price history has no sizes, so before believing it the live order books
of all 146 open weather markets were read on 11 November. In the
highest-temperature markets of three cities, five to seven hours before
settlement, when the answer is known:

| | Bids for "Yes" | Offers of "Yes" |
|---|---|---|
| A bracket that has lost (15 of them) | none | 1¢, for 20,000 to 730,000 contracts |
| The bracket that has won (3) | 99¢, for 21,000 to 197,000 contracts | none |

Buying "No" on a losing bracket means selling its "Yes" to somebody, and
nobody is bidding. The history shows "No at 99¢" for it all the same,
because that is what the feed displays for an empty side of a book. **The
rule was buying from nobody.**

What is really there is the opposite of an opportunity. Professionals
already do this trade, with resting orders, in a size no small account can
get in front of: they offer every loser at 1¢ and bid 99¢ for the winner,
hundreds of thousands of contracts deep, pay no fee, and are filled only
when somebody makes a mistake.

Two rules follow, and they apply to everything after this point.

1. **On Polymarket US a price of 1¢ or 99¢ in the history is no price.** A
   real quote there cannot be told from an empty book. A side can be bought
   only between 2¢ and 98¢, and a spread is known only when both sides are.
   The table was rebuilt and both stages rerun; the first run's files are
   kept as `*_with_end_prices.*`.
2. **Nothing measured on Polymarket US is called a result until it has been
   checked against the sizes in a live book.** The judge of section 4 did
   not ask for that and now does.

The version of this section that was committed first explained the eighteen
differently: as one-contract bids left at 1¢, in brackets that "had traded
between nothing and 101 contracts". That was read off markets two days from
settlement, where the books are still nearly empty, and it was wrong about
the rest. The median settled weather bracket traded 5,592 contracts.

### What the US history does say

Days with a price on one side only are worthless as evidence. Where one
side alone was quoted between 95¢ and 98¢, that side went on to pay 80% of
the time: it is an offer somebody left in an empty book, not the market's
opinion. Rules with no spread condition pick these up and lose badly on
them ("Yes" at 95–98¢ on stand-alone questions: 310 purchases, 121 lost).
Everything below uses only days with both sides quoted at most 5¢ apart.

Every outcome on every such day, by its asking price:

| Ask | Outcome-days | Average ask | Share that paid |
|---|---:|---:|---:|
| up to 10¢ | 41,596 | 5.4¢ | 1.5% |
| 10–50¢ | 33,263 | 27.5¢ | 23.7% |
| 50–90¢ | 31,661 | 74.2¢ | 76.8% |
| 90–95¢ | 15,562 | 93.4¢ | 97.5% |
| 95–98¢ | 26,478 | 97.3¢ | 98.9% |

Long shots pay less often than their price says and favourites more often,
in every row. It is the shape found on polymarket.com.

The same thing as rules (whole history, one purchase a market, after the
fee, 3 to 60 days left unless stated):

| Bought | Trades | Events | Settlement days | Lost | Return | z |
|---|---:|---:|---:|---:|---:|---:|
| "No" on a stand-alone question at 90–95¢ | 181 | 84 | 42 | 4 | +4.1% | 2.2 |
| "No" on a stand-alone question at 95–98¢ | 380 | 117 | 60 | 7 | +0.6% | 0.7 |
| "Yes" on a stand-alone question at 95–98¢ | 131 | 57 | 39 | 21 | −14.0% | −1.8 |
| The leader of several answers at 90–95¢ | 371 | 370 | 28 | 6 | +4.8% | 3.1 |
| The leader at 95–98¢ | 428 | 427 | 32 | 3, and 1 closed at 50¢ | +2.0% | 2.4 |
| An also-ran ("No") at 95–98¢ | 785 | 535 | 48 | 6, and 11 closed at 50¢ | +1.1% | 0.9 |
| An also-ran ("No") at 90–98¢ with 1 to 3 days left | 523 | 429 | 122 | 4 | +2.4% | 3.1 |

"No" on a stand-alone question makes money and "Yes" loses it, as on
polymarket.com. Favourites and the "No" of also-rans make money too. **None
of this is a result,** for three reasons.

- **It is mostly one night.** 86% of the leader's trades are House, Senate
  and governor races settled on 3 to 5 November. The score treats each race
  as a separate bet. They are not: one bad night for the polls would have
  sunk dozens together, and this night was a good one for favourites.
- **The rows were chosen after looking.** The judge fixed in advance passed
  none of them: before 16 September there were too few trades to make any
  of them a candidate.
- **There are no sizes.** A real price on both sides says somebody was
  there. It does not say for how many contracts, and the books read live on
  11 November held between one and a few hundred contracts at the best
  price in weather markets a day from settlement.

The last row is the one worth following. It is spread over 122 settlement
days instead of one, about half of it is weather and awards, and it settles
within three days, so new evidence on it arrives daily. It goes into the
forward test of section 8 with the sizes recorded.
