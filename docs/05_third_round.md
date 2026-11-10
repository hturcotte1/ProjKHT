# 05 — Third round: which side of the bet

*10 November 2026. Continues [04_second_round.md](04_second_round.md).*

## 1. Where the second round left things

One rule survives every test so far: buy the near-certain side of a news
market and hold it. It repeats in markets a fifth the size of the ones it was
found in, and it is larger there. Everything that tried to predict *which*
favourites lose (quietness, a volatility yardstick, stop-losses) failed its
test or added nothing.

The account, though, is still mostly idle. With one position per event and
positions of 2–4%, two-thirds of the money sits in cash. So the questions for
this round are about breadth and about what exactly is being bought:

1. Does the rule keep working in markets smaller still? (T5, fixed in round
   two and not yet read.)
2. Is it the same bet whichever side it is on? A 96¢ "Yes" and a 96¢ "No" are
   the same price. They may not be the same mistake.
3. Does it work further from the deadline, where the money is idle anyway?

## 2. What the markets already read say

Everything in this section was computed on the two universes that have been
read many times (news markets with 100,000 shares or more, and with 20,000 to
100,000). It is exploration. It chose the tests in section 3, which are run
on markets nobody has looked at.

### The same price on different sides

The first round's rule, 95–99¢ with 3 to 60 days to run, split by what kind
of contract was bought. A *stand-alone* market is a single yes/no question. A
*leg* is one outcome of an event with several ("Who wins?", "How many?"),
where at most one leg can pay.

| Bought | Big markets: trades | lost | return (t) | Thin markets: trades | lost | return (t) |
|---|---:|---:|---:|---:|---:|---:|
| Stand-alone, "No" | 1,941 | 30 | +1.52% (4.9) | 1,622 | 17 | +1.71% (6.2) |
| Stand-alone, "Yes" | 251 | 5 | +0.78% (0.7) | 207 | 4 | +0.75% (0.8) |
| Leg, "Yes": the leader of its event | 260 | 1 | +2.84% (7.1) | 366 | 3 | +2.15% (4.4) |
| Leg, "No": one of the also-rans | 1,358 | 33 | +0.07% (0.2) | 940 | 7 | +1.70% (5.9) |

Three things stand out, each in both universes.

**The stand-alone edge is on the "No" side.** Seven trades in eight are "No"
and they carry the result. The "Yes" side has never been distinguishable from
zero: six cells across two universes and three price bands, none with a t
above 1.1. The gap itself is not established (pooled, "No" minus "Yes" is
+2.2 points in the 90–98¢ band, t = 2.1, and +1.0 in 95–98¢, t = 1.1). The
first round tested "No only" as rule R2 on the holdout and it fell short at
t = 2.2.

Reading the questions explains it. A stand-alone "No" at 96¢ is almost always
*"will something happen by a date?"* priced at 4¢ that it will. A stand-alone
"Yes" at 96¢ is mostly the reverse: *something is expected to happen* (a rate
cut by a date, a model released by a date, a ceasefire announced) and the
market is nearly sure of it. The losers are things that were about to happen
and did not: "Iran closes its airspace by May 31?", "Will Amazon beat
quarterly earnings?". The crowd is too sure that things will happen, on both
sides of 50¢.

**The leader of a multi-way event is underpriced.** A 95–99¢ "Yes" in an
event with several outcomes lost 1 time in 260 and 3 times in 366, against
the 3% that its price implies (chance of so few losses if the price were
fair: 0.002 and 0.006). These are safe seats ("Will a Republican win
Wyoming?"), runaway front-runners, and the "nothing happens" bracket of a
count ("Will Israel strike Yemen 0 times by October 31?"). The paper accounts
have never traded them: they skip every leg.

**The also-rans are fairly priced where professionals are.** Betting against
one of several long shots earned nothing in the big markets and 1.7% in the
thin ones. In a multi-way event the legs can be converted into one another,
so arbitrage keeps the field's prices consistent in markets worth
arbitraging. No test is fixed on these; they are reported.

One way to say all three: what is underpriced is the outcome in which
*nothing surprising happens*, whichever label it carries. The stand-alone
"No", the leader, and the zero bracket are that outcome. The stand-alone
"Yes" at 96¢ is a forecast that something *will* happen, and it is not
underpriced.

### Further from the deadline

Every test so far bought with 3 to 60 days to run. The same contracts exist
months out, and nobody has looked at them. Stand-alone markets, 90–98¢,
bought with more than 60 and up to 180 days to the scheduled end, in markets
whose scheduled end had passed by 27 October 2026 (see the note below):

| | Big: trades | lost | return (t) | per 30 days held | Thin: trades | lost | return (t) | per 30 days held |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Both sides | 630 | 16 | +4.02% (6.2) | 1.23% | 271 | 6 | +4.06% (4.2) | 1.36% |
| "No" side | 522 | 7 | +5.40% (9.9) | 1.48% | 231 | 4 | +4.62% (4.9) | 1.38% |
| "Yes" side | 108 | 9 | −2.65% (−1.0) | | 40 | 2 | +0.84% (0.2) | |
| *For comparison: 3–60 days, both sides* | 2,115 | 83 | +1.82% (4.0) | 1.96% | 1,679 | 50 | +2.47% (5.6) | 3.29% |

A long-dated "No" earns four to five percent a trade and takes three months
to do it. Per day of money tied up that is less than the short rule earns,
and more than cash earns. Both sides together, it was positive in each year
(big markets: +2.0%, +4.8%, +3.6% for entries in 2024, 2025, 2026), at 60–120
days and at 120–180, and at 90–95¢ and 95–98¢. The "Yes" side is again where
the losses are.

This was a first look: three combinations of price and horizon were tried,
the first of them the thin account's band at the next horizon out, and that
is the one reported and tested below.

*The note on scheduled ends.* The research universes are markets that have
closed. A market scheduled to end next January is in them only if it closed
early, and a "by January" question closes early when the thing happened.
Recent entries are therefore tilted towards "No" bets that lost and "Yes"
bets that won. For 3-to-60-day trades this touches the last two months of
the sample and was small (the table's comparison row, with and without the
filter: +1.74% and +1.82% in big, +2.40% and +2.47% in thin, without it and
with it). For trades held
three months it matters more, so the long-dated numbers use only markets
whose scheduled end is behind us.

### Not only near certainty

The split by side was then run at every price, which no earlier round had
done: the first round's calibration pooled both sides, and a "Yes" that loses
six cents beside a "No" that gains five looks like nothing but trading costs.
Stand-alone Yes/No markets, 3 to 60 days to run, each side bought the first
time its ask enters the band; cents a share after fees, with t:

| Price paid | Big: "No" | Big: "Yes" | Thin: "No" | Thin: "Yes" |
|---|---:|---:|---:|---:|
| 3–10¢ | −2.3 (−1.9) | −2.9 (−5.9) | −0.6 (−0.4) | −4.2 (−10.0) |
| 10–20¢ | −1.5 (−0.7) | −2.3 (−2.0) | −3.7 (−1.6) | −7.1 (−7.6) |
| 20–35¢ | +1.4 (0.5) | −2.9 (−1.9) | −1.7 (−0.6) | −11.0 (−6.5) |
| 35–50¢ | +4.8 (1.9) | −5.8 (−2.7) | −0.6 (−0.2) | −11.4 (−4.2) |
| 50–65¢ | +3.8 (1.7) | −7.1 (−2.8) | +6.8 (2.5) | −5.0 (−1.5) |
| 65–80¢ | +1.3 (0.8) | −4.7 (−1.7) | +8.2 (4.4) | −4.0 (−1.2) |
| 80–90¢ | +0.9 (0.8) | +0.7 (0.4) | +6.4 (6.7) | +2.4 (1.0) |
| 90–95¢ | +1.8 (2.8) | +1.6 (1.0) | +3.5 (6.0) | −0.3 (−0.1) |
| 95–98¢ | +1.6 (4.7) | +1.2 (1.1) | +2.1 (6.4) | +0.5 (0.4) |

Buying "Yes" lost money in 13 of the 18 cells, by far more than a spread and
a fee below 80¢. Buying "No" as the favourite made money in all ten cells
from 50¢ up. The near-certain band this project has traded since the first
round is the top of something wider: on a question of the form "will this
happen?", the crowd pays too much for "Yes" at every price.

"No" bought at 50–90¢, one trade per market:

| | Trades | Events | Won | Average cost | Cents a share (t) | Return per trade (t) |
|---|---:|---:|---:|---:|---:|---:|
| Big markets | 1,428 | 937 | 77.1% | 74.5¢ | +2.5 (2.1) | +3.8% (2.1) |
| Thin markets | 998 | 715 | 82.4% | 75.6¢ | +6.7 (5.7) | +8.8% (5.0) |

In the thin markets it is positive in every category (culture +10.9¢,
geopolitics +7.0¢, finance +5.8¢, politics +5.0¢), with a fee and without,
and in every half-year except the last, which is the one the note on
scheduled ends says to distrust (with markets whose scheduled end has passed
only: +7.6¢, t = 6.4). It grows with the time left: +3.9¢ with 3–10 days to
run, +9.7¢ with 20–40. In the big markets it is one category: geopolitics,
which carries no fee, +5.7¢ (t = 3.8) on 733 trades, and nothing elsewhere
(−0.8¢). A resting bid does *worse* than paying the ask here (thin: +5.4¢
against +6.7¢): in the middle of the price range a bid fills when the news is
going the other way.

This is a different trade from the one the accounts make. A 97¢ contract
loses one time in fifty; a 75¢ contract loses one time in five or six, and
each loss is the whole position. The return per trade is four times larger
and so is the swing.

### Looked at and dropped

| Idea | What the two universes said |
|---|---|
| Questions settled by a number (finance, economics, weather) against questions settled by a story | No consistent difference: +0.9% against +1.1% in big markets, +1.1% against +1.9% in thin; finance is the weakest category at 3–60 days and among the best at 60–180 |
| The time of year | November entries were the best month in big markets (3 losses in 520) and among the worst in thin ones |
| Crowded months, when many contracts qualify at once | No relation to the return in either |

## 3. Tests fixed before the 5,000–20,000 markets were read

*Written at 19:49 UTC on 10 November 2026. The tapes of these markets were
still downloading and none had been opened.*

The universe is the one fixed for T5 in round two: resolved news markets
(outside sports and crypto, a life of two days or more) that traded at least
5,000 and fewer than 20,000 shares, each used once it has traded 5,000.
Entries at the next taker-buy print within three days, today's fee, held to
the result, standard errors clustered by event. "Yes" and "No" mean markets
whose two outcomes carry those names.

**T5** (unchanged from round two). R1d: 95–99¢, legs included, 3–60 days.
*Bar:* positive with |t| ≥ 3.

**T5-Y, the leader.** Among T5's own trades, those that bought the "Yes"
side of a leg. *Bar:* positive with |t| ≥ 3, and fewer losses than the price
paid implies with an exact binomial p below 0.01 (a t-statistic cannot judge
a group that almost never loses; that was the lesson of A1). *If it passes:*
the accounts may buy the leader of a multi-way event at 95–99¢, one position
per event as now.

**T5-L, long-dated "No".** Stand-alone markets scheduled to end on or before
27 October 2026; the "No" outcome with an ask above 90¢ and at most 98¢ and
more than 60 and at most 180 days to the scheduled end; one trade per market.
*Bar:* positive with |t| ≥ 3. With fewer than 150 trades the test cannot
settle anything and will be reported as such. *If it passes:* a paper account
of its own for long-dated positions.

**T5-N, which side.** The thin account's band (90–98¢, stand-alone, 3–60
days), split by the side bought. *Prediction:* "No" returns more than "Yes".
*Decision rule:* the accounts stop buying the stand-alone "Yes" side if the
gap has the predicted sign in T5 **and** the gap pooled over the three
universes has |t| ≥ 3. It stands at t = 2.1 before T5. Otherwise the
accounts are left alone and the forward test, which logs both sides, goes on
collecting.

**T5-TM, resting bids.** TM exactly as in round two (the thin account's
signals, skipping outcomes that ranged more than 15¢ in two weeks; a bid at
the signal day's bid, filled only if a later sale prints strictly below it
within three days, no fee), on these markets. *Bar:* positive with |t| ≥ 3
and above the same signals bought at the ask with |t| ≥ 2 on the gap.

**T5-H, the house.** *Added at 19:53 UTC, after the table "Not only near
certainty" above and with the tapes still downloading.* Stand-alone Yes/No
markets; the "No" outcome with an ask above 50¢ and at most 90¢ and 3 to 60
days to the scheduled end; one trade per market. *Bar:* return per trade
positive with |t| ≥ 3. *Predictions, not bars:* at least the thin markets'
+6.7¢ a share; more with 20–60 days left than with 3–20; and "Yes" bought at
10–50¢ in the same markets loses more than a spread and a fee. The bar is on
every market, which the note on scheduled ends says leans against "No"; the
version with scheduled ends behind us is reported beside it. *If it passes:*
a paper account that buys "No" at 50–90¢ in stand-alone news markets under
100,000 shares, with smaller positions than the others because a loss is the
whole position one time in five.

Reported without a bar: the also-rans ("No" legs), categories, years, the
dollars that traded in range, and the full table of side by price.

That makes 27 tests with a bar fixed in advance across the three rounds.

### A flaw in the universe, found before the data was read

*Written at 19:59 UTC, with the tapes still downloading and none opened.*

The mid-priced "No" result looked too good, and checking why exposed a
mistake that round two made and this section was about to repeat.

Round two chose its thin markets by the number of shares they had traded *by
the end*: 20,000 to 100,000. Nobody knows that number when a trade is made.
And it is not neutral: when the surprise happens, a market draws a burst of
trading on the way, and many end up over the line. "Markets that ended
between 20,000 and 100,000 shares" had therefore already handed many of their
losers to the bigger group. The first round's universe does not have the
problem (a market is used from the moment it has traded 100,000 shares, with
no upper limit), and the paper accounts do not have it either (they look at
the volume a market has today).

The measure of it: the same rules on the part of each bigger market's life
when it had traded 20,000 to 100,000 shares, which round two never looked at,
and on both together, which is what "thin" means to somebody trading.

| Rule | Markets that ended thin (round two) | Thin part of markets that ended bigger | Both: thin at the time |
|---|---:|---:|---:|
| R1d, 95–99¢, legs included | +1.69% (t 9.0), 31 lost of 3,135 | −0.96% (t −2.9), 121 of 3,351 | **+0.33% (t 1.7)**, 152 of 6,486 |
| Main rule, 95–98¢, stand-alone | +1.96% (t 6.0), 18 of 1,393 | −0.22% (t −0.3), 33 of 929 | **+1.09% (t 3.4)**, 51 of 2,322 |
| Thin account's rule, 90–98¢, calm | +2.52% (t 5.8), 46 of 1,637 | −1.29% (t −1.5), 89 of 1,336 | **+0.81% (t 1.7)**, 135 of 2,973 |
| The same with a resting bid (TM) | +3.57% (t 5.6) | −1.00% (t −1.0) | **+1.39% (t 2.3)** |
| "No" at 50–90¢ | +8.8% (t 5.0) | +2.0% (t 1.2) | **+4.6% (t 3.7)** |
| Long-dated "No", 90–98¢, 60–180 days | +4.6% (t 4.9) | +3.9% (t 4.9) | **+4.1% (t 6.4)** |

Round two's headline, that the edge is larger in thinner markets, was
produced by the way the markets were chosen. Thin at the time, the main rule
earns about what it earns in big markets, the wider 90–98¢ band does not
pass, and resting bids do not pass. The corrected numbers above come from
exploration code; section 4 will give them from a committed script, with
everything in round two that depended on them.

**What changes in the tests above.** The universe fixed for T5 has the same
flaw (markets that *ended* at 5,000 to 20,000 shares). Every test in this
section is therefore judged on the corrected universe: **news markets while
the shares they had traded so far were at least 5,000 and fewer than 20,000,
whatever they went on to trade.** That is the newly downloaded markets plus
the early life of every market already on disk, and nobody has looked at any
of them in that range. The universe as first fixed is reported beside it, as
a second measure of the flaw. The bars do not change. Where a test pools with
"the thin markets", it uses them thin at the time; the comparison figures
quoted as predictions (+1.69% for R1d, +6.7¢ for the house) are overstated
for the reason above and are not the standard any more: the standard is the
bar.
