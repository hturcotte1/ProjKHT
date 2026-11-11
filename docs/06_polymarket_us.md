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
| Maker fee | none (and no rebate below $10 million a month); resting orders can also be paid rewards, found later and described in `docs/08_rewards.md` | none |
| Tick, smallest order | 1¢ (0.5¢ and 0.1¢ on some); 0.01 of a contract | 1¢ or 0.1¢; 5 shares |
| Public data | every market's settlement; the order book's best prices on both sides, minute by minute, for any past day; one point a day for a market's whole life; total shares traded. (Section 7 found that these "best prices" are the last trade wherever a side of the book is empty) | every trade ever made |
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
The US table is every settled non-sports market on every day its order book
had real prices on both sides: 8,480 markets in 2,462 events, settled on 194
days from 12 April to 10 November 2026, one row per outcome per day, bought
at the next day's ask with the US fee. What "real" means was learned the
hard way and is in section 7.

**None of the 32 rules is confirmed. The honest reading is that Polymarket
US cannot say either way.**

Carrying a rule over needs the US equivalent of "a stand-alone question",
and the gateway has no flag for it, so each market's shape is read from what
is known without the result (`us_shape`):

| Shape | Settled markets in the table | What they are |
|---|---:|---|
| a single question, or a dated rung of one | 111 | "Putin meets with Zelenskyy? By September 30", "GPT-6 released?", a referendum |
| separate questions under one heading | 1,301 | thresholds ("gas above $4.07"), "who will be announced out", but also races the prices could not identify |
| one answer of several, only one of which can be right | 6,325 | temperature brackets, chart positions, candidates |
| too thinly quoted to tell | 743 | |

The table went through four versions, each a correction made after a result
had been seen. All four are reported for that reason, and none of them
confirms anything.

| Version of the US table | Rules with 100 trades | Bar | Best score | Confirmed |
|---|---:|---:|---:|---:|
| 1. As first coded: "stand-alone" is any market whose event's prices did not add to one that day | 19 of 32 | z ≥ 2.79 | 1.41 | 0 |
| 2. Shapes corrected: "stand-alone" is the first two rows above | 8 of 32 | z ≥ 2.59 | 2.10 | 0 |
| 3. And prices of 1¢ and 99¢ treated as no price | 8 of 32 | z ≥ 2.53 | 2.15 | 0 |
| 4. And only days with a real book on both sides (section 7) | 6 of 32 | z ≥ 2.61 | 2.06 | 0 |
| Strict: single questions and dated rungs only | none; the most any rule gets is 35 | | | cannot be judged |

Version 1 counted candidates and contestants as stand-alone questions ("Big
Brother 2nd place: Taylor Brown"), which is the one family stage 1 found
nothing in. Versions 3 and 4 fix errors in the prices themselves.

On the final table 30 of the 32 rules made money, the average is +3.0% a
trade, and the best has z of 2.06 on 120 trades with two losses. Under the
strict mapping no rule has more than 35 trades, and not one of those trades
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
  $1, so near-certain contracts pile up at 98¢ and 99¢. Of the 306
  purchases of the most active rule carried over, 145 were at 98¢, where a
  win pays 1.8% after the fee.

## 7. Stage 2b: the search on Polymarket US alone

`scripts/factory.py run-us` (`f_us_*.csv`, `factory_us_output.txt`).
Discovery is markets ending before 16 September 2026, validation from then
to 10 November.

**Nothing passes. The first run said eighteen rules did. They came from a
property of the price feed that took three attempts to pin down, and this
section replaces two earlier versions of itself.**

| | First run | 1¢ and 99¢ removed | Real two-sided books only | Worlds with no edge |
|---|---:|---:|---:|---:|
| Rules with 30 trades or more | 11,355 | 11,346 | 9,530 | |
| Candidates | 18 | 0 | **0** | 0.0 to 0.2 on average |
| Survivors | 18 | 0 | **0** | none in twenty worlds |

### What the price feed records

Polymarket US publishes no trades. Its price history gives, for each market
and moment, a "Yes" price and a "No" price, described as "normally" the
best ask and one minus the best bid. On 11 November the feed was compared
with the live order books of 400 open markets (396 had history):

- **Orders on both sides (328 markets):** the feed showed the best ask and
  one minus the best bid in 98% of them. Here it can be trusted.
- **One side empty (68 markets, and a second sample of 219):** the feed
  showed the **last trade** in place of the missing quote, in every one. A
  book with a bid of 95¢, no offer at all and a last trade at 43¢ was
  recorded as "Yes at 43¢". Nobody could buy it there.

So a price in the history may be one at which nothing could be bought, and
the history does not say which. Two kinds can be recognised afterwards. A
market that everybody has stopped trading last traded near 1¢ or 99¢, so the
filled-in price sits at the end of the range. And when the last trade
happened at the price of the surviving quote, the two "sides" show no spread
at all, which a real book cannot have.

### The eighteen that were not there

All eighteen were one rule with small variations: buy "No" at about 99¢ on
one answer of several, with one to three days left. Mostly temperature
brackets. Discovery: 3,245 trades, 4 lost, +0.90% a trade (z 5.1).
Validation: 2,333 trades, 4 lost, +1.18% (z 4.9). It passed the judge of
section 4 cleanly.

The order books of all 146 open weather markets were read on 11 November.
In the highest-temperature markets of three cities, five to seven hours
before settlement, when the answer is known:

| | Bids for "Yes" | Offers of "Yes" |
|---|---|---|
| A bracket that has lost (15 of them) | none | 1¢, for 20,000 to 730,000 contracts |
| The bracket that has won (3) | 99¢, for 21,000 to 197,000 contracts | none |

Buying "No" on a losing bracket means selling its "Yes" to somebody, and
nobody is bidding. Its last trade was at 1¢, so the history says "No at
99¢". **The rule was buying from nobody.**

What is really there is the opposite of an opportunity. Professionals
already do this trade, with resting orders, in a size no small account can
get in front of: they offer every loser at 1¢ and bid 99¢ for the winner,
hundreds of thousands of contracts deep, pay no fee, and are filled only
when somebody makes a mistake.

### The rules that follow

1. **A day of US history is used only if its book looks real on both
   sides:** both prices between 2¢ and 98¢, at least one tick apart, at
   most 20¢ apart. Of 230,545 market-days this keeps 88,859.
2. **What is left is still about 2% filled-in prices.** Of 1,306 live books
   that would have passed that filter on 11 November, 25 had an empty side
   and a last trade close enough to the other quote to look like a spread.
   Nothing in the history identifies these.
3. **Nothing measured on Polymarket US is called a result until it has been
   checked against live order books, with sizes.** The judge of section 4
   did not ask for that and now does.

The two versions of this section committed before this one were each wrong.
The first explained the eighteen as one-contract bids left at 1¢ in
brackets that "had traded between nothing and 101 contracts"; that was read
off markets two days from settlement, and the median settled weather
bracket traded 5,592 contracts. The second said the feed shows 99¢ for an
empty side, when it shows the last trade, and reported that "Yes" on a
stand-alone question at 95–98¢ had lost 14%. That loss was the feed again:
35 of those 131 purchases showed no spread, were filled-in prices, and lost
half their money. Without them the same rule is flat.

### What the US history does say

Every outcome on every day with a real book at most 5¢ wide, by its asking
price:

| Ask | Outcome-days | Average ask | Share that paid |
|---|---:|---:|---:|
| up to 10¢ | 39,880 | 5.6¢ | 1.3% |
| 10–50¢ | 31,617 | 26.5¢ | 22.8% |
| 50–90¢ | 30,872 | 74.3¢ | 76.5% |
| 90–95¢ | 15,431 | 93.4¢ | 97.5% |
| 95–98¢ | 25,400 | 97.2¢ | 99.2% |

Long shots pay less often than their price says and favourites more often,
in every row. It is the shape found on polymarket.com.

The same thing as rules (whole history, one purchase a market, after the
fee, spread at most 5¢, 3 to 60 days left unless stated):

| Bought at 90–98¢ | Trades | Events | Settlement days | Lost | Return | z | Share settled 3–5 November |
|---|---:|---:|---:|---:|---:|---:|---:|
| "No" on a stand-alone question | 392 | 117 | 58 | 6 | +2.1% | 2.1 | 16% |
| "Yes" on a stand-alone question | 131 | 58 | 37 | 6 | −0.6% | −0.3 | 9% |
| The leader of several answers | 500 | 499 | 38 | 6 | +3.7% | 3.5 | 84% |
| An also-ran ("No") | 891 | 583 | 48 | 10, and 13 closed at 50¢ | +2.3% | 1.6 | 60% |
| An also-ran with 1 to 3 days left | 240 | 213 | 22 | 2 | +2.7% | 2.2 | 85% |

"No" on a stand-alone question makes money and "Yes" does not, as on
polymarket.com. Favourites and the "No" of also-rans make money too. **None
of this is a result,** for four reasons.

- **Most of it is one night.** 84% of the leader's trades are House, Senate
  and governor races settled on 3 to 5 November. The score treats each race
  as a separate bet. They are not: one bad night for the polls would have
  sunk dozens together, and this night was a good one for favourites.
- **The rows were chosen after looking.** The judge fixed in advance passed
  none of them: before 16 September there were too few trades to make any
  rule a candidate.
- **There are no sizes.** A real price on both sides says somebody was
  there. It does not say for how many contracts.
- **About one price in fifty was never there at all.**

The first row is the one that carries over from the earlier rounds, and it
is the least dependent on the election: 58 settlement days, 117 events. At
its pace of about 55 trades a month, a forward test would need most of a
year to confirm an edge of 2% a trade. Polymarket US lists too few of these
questions for anything faster.

## 8. What replaces the history: the live order books

Stage 3 of section 4 assumed the venue's price history could score a
rulebook on any later day. Section 7 shows it cannot. So from 11 November
the order books themselves are written down.

`kht us-record` (`src/kht/trading/us_recorder.py`) runs with the paper
accounts every cycle and saves, for every open market outside sports and
crypto that shows any quote, the three best prices on each side with their
sizes, the last trade, the contracts traded and the open interest. It reads
public data only, places no orders and needs no key. Files are in
`state/us/`; `state/us/STATUS.md` is the latest cycle in words.

A trial cycle read 2,616 order books in five minutes, 2,153 of them with
orders on both sides. They are small. In half of the two-sided books the
best offer of "Yes" could be taken whole for less than $8, and the best
price for "No" for less than $50; in a tenth, for more than $312 and
$17,000.

Any rule in the grid can later be scored against what was really on offer,
and at what size. One rule is named now, so that it cannot be chosen later:

**F2, the rule that carries over.** The first time a market that is a
stand-alone question (a single question, a dated rung of one, or one of
several separate questions under a heading) shows "No" on offer at 90¢ to
98¢, in a book at most 5¢ wide, with 3 to 60 days to its end date: buy "No"
at the next snapshot if it is still in that range, for what is on offer at
the best price up to $50, pay the fee, hold to settlement. It is confirmed
if its mean return is positive with z ≥ 2.58, each event one bet, on at
least 300 purchases. At the pace of section 7 that is most of a year away.

The same recorder also captures something that could be judged much sooner,
which is the subject of `docs/07_two_venues.md`.

## 9. Sports, fixed before the quotes are read

Sports are seven-eighths of what Polymarket US lists, and the only part of
it with a deep history: 754,742 settled main-line markets since November
2025 (149,959 on who wins, 244,152 point spreads, 276,702 totals, 83,929
three-way). At the time of writing no sports result has been tabulated.
While checking that pre-game quotes exist, about thirty markets were
printed with their quotes and results side by side; nothing was counted.

What is expected: nothing. The earlier rounds found no edge in sports on
polymarket.com, sports prices are anchored by professional bookmakers, and
the US fee is 2.4¢ a contract at 50¢. It is tested because it is most of
the exchange, and because a year of games is the one place where
Polymarket US has enough independent results to say something firmly.

### What is tested

**Moneylines only**: the 149,959 settled markets on who wins a game or
match. Spreads and totals are bets close to 50¢ by construction, where the
fee alone is 4.75% of the stake. A rule that pays the ask there would need a
mistake larger than any this project has found anywhere, so they are left
out. That is a decision not to look, not a finding.

**The data.** For each market, the stored observations of its order book
over the three hours before its recorded start. Three quotes are taken: 180,
60 and 5 minutes ahead, each the last observation at or before that moment
and unused if more than 30 minutes old. A quote is used only if it passes
the filter of section 7 (real prices on both sides).

**A rule:**

> In family F, buy side S when its ask 60 minutes ahead is in band B, the
> spread is at most W, and over the two hours before that the price did C.
> Buy 5 minutes ahead, at that moment's ask, if it is still in the band. Pay
> the fee. Hold to settlement. A market closed at 50¢ pays 50¢.

| Part | Values | Count |
|---|---|---:|
| Family | all; tennis, main tours; tennis, lower tours; table tennis; e-sports; the US leagues (NBA, MLB, NHL, NFL, college football and basketball, WNBA); everything else | 7 |
| Side | the first-named side; the second-named. In US team sports the first-named is the visiting team | 2 |
| Price band | the twenty bands of section 3 | 20 |
| Spread | at most 1¢; at most 3¢; any real book | 3 |
| What the price did | no condition; quiet (moved under 1¢); rose 3¢ or more; fell 3¢ or more | 4 |

That is 3,360 rules (`scripts/sports_us.py`).

### The judge

The judge of section 4 as corrected, unchanged in form:

- discovery is games starting before 1 September 2026 (70,182 moneylines),
  validation from then to 10 November (79,777);
- a candidate has, in discovery, at least 150 trades, a mean return after
  the fee of at least +0.5%, and z ≥ 3 with each game as one bet;
- a survivor has, in validation, at least 100 trades and a z by day of the
  game at or above the 95th percentile of the best validation z among the
  candidates over 500 worlds in which every price is right (one draw a
  game, so its two sides cannot both win);
- the whole funnel is also run on 20 such worlds.

A survivor is not a result until its sizes have been read off live order
books (section 7, rule 3) and it has been scored on games played after
today.

### What will be reported whatever happens

The counts at each step, the placebo counts, and for each family the plain
table of asking price against how often that side won.

### One thing that cannot be fixed

The recorded start is sometimes the scheduled time and sometimes later than
the real one. A quote "60 minutes ahead" of a late start may come from a
game already under way. That puts no hindsight into a rule's return, since
the purchase is still made at a price quoted at that moment. It does change
what the rule means. The share of markets whose price moved 30¢ or more
between the two quotes is reported for each family as a measure of it.

## 10. Sports: nothing

*Run on 11 November 2026 at 09:10 UTC, after the quotes of every settled
moneyline had been downloaded. Nothing in section 9 was changed.*

**No rule passed the first step.** Of 3,360 rules, 2,217 made 30 trades or
more and 1,173 made the 150 trades in discovery that a candidate needs. Not
one of them reached z = 3 there. The best reached 1.74. With no candidate
there is nothing to judge in validation and no threshold to compute. The
same funnel run on 20 worlds in which every price is right also produced no
candidate, every time.

### The counts

| Step | Games |
|---|---:|
| Settled moneylines listed | 149,959 |
| Settled, with a recorded start before 11 November | 149,597 |
| A real book 60 minutes ahead | 118,339 |
| and 5 minutes ahead | 112,607 |
| and 180 minutes ahead | 108,317 |
| In the table: before 1 September / from then | 56,301 / 62,038 |

The games run from 31 October 2025 to 10 November 2026, over 372 days. In
three quarters of the books the spread 60 minutes ahead was one cent or
less.

Of the rules with 150 trades in discovery, 148 had a positive mean return
there and 1,025 a negative one. The average rule lost 7.4% a trade in
discovery and 7.0% in validation. That is the fee and the spread, and it is
the same in both halves.

The fifteen rules closest to the bar in discovery were nearly all one idea:
the heavy favourite at 90¢ to 99¢. Eleven of the fifteen then lost money in
validation.

### Asking price against what the side paid

All families together, both sides of every game. "Paid" is the average
payout of the side: 1 if it won, 0 if it lost, and whatever the exchange
settled at when a game was called off (below). The last two columns are for
the purchases a rule would make 5 minutes ahead, after the fee.

| Ask 60 minutes ahead | Quotes | Average ask | Middle of the book | Paid | Bought | Return after fee | z by day |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2–5¢ | 1,178 | 4.3¢ | 3.7¢ | 2.9¢ | 830 | −33.0% | −2.0 |
| 5–10¢ | 5,085 | 8.0¢ | 7.3¢ | 6.3¢ | 3,756 | −29.2% | −5.4 |
| 10–20¢ | 12,772 | 15.8¢ | 14.8¢ | 14.4¢ | 10,264 | −17.1% | −7.7 |
| 20–35¢ | 34,205 | 28.9¢ | 27.9¢ | 27.9¢ | 29,050 | −10.1% | −10.4 |
| 35–50¢ | 62,148 | 43.5¢ | 42.6¢ | 42.9¢ | 52,726 | −6.1% | −11.3 |
| 50–65¢ | 65,023 | 57.5¢ | 56.4¢ | 56.2¢ | 55,259 | −6.2% | −16.8 |
| 65–80¢ | 35,455 | 72.1¢ | 71.1¢ | 71.0¢ | 30,086 | −4.2% | −10.7 |
| 80–90¢ | 13,176 | 85.2¢ | 84.1¢ | 84.6¢ | 10,491 | −1.6% | −3.9 |
| 90–95¢ | 5,684 | 93.0¢ | 91.7¢ | 92.6¢ | 4,165 | −0.7% | −1.6 |
| 95–98¢ | 1,940 | 96.8¢ | 95.1¢ | 95.8¢ | 1,361 | −0.9% | −1.7 |

Two things can be read off it.

- **The middle of the book is right.** Between 20¢ and 80¢ the middle of
  the book an hour before a game and what the side went on to pay differ by
  less than half a cent, on tens of thousands of games in each row. A buyer
  pays that price plus half the spread plus the fee, and loses exactly that.
- **The ends lean the way everything else in this project leans.** Long
  shots pay less than the middle of their book (3.7¢ against 2.9¢, 7.3¢
  against 6.3¢) and heavy favourites pay more (91.7¢ against 92.6¢). The
  lean is smaller than the spread and the fee together, so a buyer of the
  favourite still loses.

By family (`reports/research/sp_calibration.csv`) the picture is the same.
Among cells with a hundred purchases or more, the only ones with a positive
return after the fee are heavy favourites at 90¢ to 98¢ in the main tennis
tours (+0.9% and +1.7%, z of 0.8 and 1.3) and in the US leagues (+2.0% and
+1.1%, z of 1.8 and 1.1), and table tennis at 80¢ to 90¢ (+0.9%, z of 0.8).
None is distinguishable from nothing, none was a candidate, and five cells
picked from about sixty after the fact are not evidence.

### Two checks on the data

**The recorded start.** Section 9 warned that a recorded start can be later
than the real one, so that a "pre-game" quote comes from a game under way.
The share of games whose price moved 30¢ or more between the quotes 60 and
5 minutes ahead:

| Family | Share |
|---|---:|
| US leagues | 0.03% |
| Tennis, main tours | 0.12% |
| Table tennis | 0.20% |
| Tennis, lower tours | 0.34% |
| Everything else | 0.47% |
| E-sports | 0.72% |

It is rare everywhere. The quotes are pre-game quotes.

**Games called off.** Of the 149,597 moneylines, 3,408 settled at exactly
50¢ and 1,314 at some other price between 0 and 1, such as 44¢. Twelve of
the second kind and six of the first were looked up at the exchange's
settlement endpoint, and all eighteen agreed with the list. They are mostly tennis and e-sports: a match
abandoned or a walkover, settled at a price rather than for a winner. The
test pays a purchase what the exchange paid.

### What it means

For somebody who buys at the asking price, sports on Polymarket US is
closed. That was expected, and it is now measured on a year of games rather
than assumed: 118,339 games, no rule out of 3,360 near the bar, and a
price-against-result table that leaves a buyer nothing but the cost.

It says something else for somebody who rests orders instead. A resting
order pays no fee and is filled at its own price, not across the spread.
The table says the middle of the book is a fair price before a game, and
that where it is not fair it errs in favour of whoever sells the long shot.
Whether resting orders before games make or lose money depends on who fills
them and when, which this table cannot show. The exchange also pays
rewards for resting orders in every one of these games. That is taken up in
`docs/08_rewards.md`.
