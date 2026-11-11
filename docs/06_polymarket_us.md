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

Two things this settles and one it does not.

*The long-dated "No" is now confirmed on polymarket.com.* Round three found
it by looking and could only test it in the thinnest markets, where it fell
short. Here it was found in the pre-2026 half by a blind search and held in
the 2026 half against a family-wise bar. Twenty of the 32 survivors are
versions of it.

*A tight spread matters.* The plain first-round rule ("No" at 95–98¢, 3–60
days, any spread) is not a candidate in this pooled universe, which includes
the thin markets where round three found it weak: +0.74% in discovery, z of
1.2. With a spread of 2¢ or less and ten days or more to run it is. Round
three's after-the-fact note about spreads was right.

*Nothing new was found.* Thousands of rules were tried so that something
unexpected could show up, and nothing did. That is worth knowing: the one
mistake this crowd makes that survives costs is believing things will
happen.

