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

> **Read the "thin" columns of this section with section 3's last part in
> mind.** They were written before the flaw described there was found, on
> round two's thin universe, which was chosen with hindsight and flatters
> every rule. The section is left as it was written because it is the record
> of what led to the tests. Section 6 gives the same tables on the corrected
> universes.

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

The first round had caught this same mistake in its first hour: its
opening pass used markets chosen by total volume, found a result, and threw
it out ([findings, section 2](02_research_findings.md#2-the-sample-that-lied)).
Round two walked into it again through a different door, because an upper
limit on volume looks like a harmless way to say "small".

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

**A second filter with hindsight in it** *(20:05 UTC, same state: nothing
opened).* Every universe so far also required "a life of two days or more",
to leave out daily markets. A market's life is not known in advance either.
On the three lists, 786 news markets resolved within two days of opening
although they were scheduled to run for more than three, and "Yes" won in
about half of them against a quarter of the rest. They are mostly questions
where the thing happened at once ("US strikes Iran by January 24?", "Paris
curfew by October 24?"), and a rule that buys "No" could have been caught in
some. They were never downloaded. They are being downloaded now and go back
into every universe: the filter becomes "a life of two days or more, *or*
scheduled to run more than three", which leaves out only markets no rule
here could have traded, since every rule needs more than three days to the
scheduled end. This one reaches the first round too, and section 4 will say
what it does to those numbers.

**What changes in the tests above.** The universe fixed for T5 has the same
flaw (markets that *ended* at 5,000 to 20,000 shares). Every test in this
section is therefore judged on the corrected universe: **news markets while
the shares they had traded so far were at least 5,000 and fewer than 20,000,
whatever they went on to trade, with the short-lived markets put back.** That is the newly downloaded markets plus
the early life of every market already on disk, and nobody has looked at any
of them in that range. The universe as first fixed is reported beside it, as
a second measure of the flaw. The bars do not change. Where a test pools with
"the thin markets", it uses them thin at the time; the comparison figures
quoted as predictions (+1.69% for R1d, +6.7¢ for the house) are overstated
for the reason above and are not the standard any more: the standard is the
bar.

## 4. What the two filters did to the earlier results

`scripts/run_corrections.py` reruns everything that depended on either
filter, old universe beside corrected (`cor_*.csv`, `corrections_output.txt`).

**The first round stands.** Its universe had no upper limit on volume, so
only the two-day filter touches it. Putting the 127 short-lived big markets
back adds seven trades to R1d and loses none of them.

| First round, big markets | As it was | Short-lived markets put back |
|---|---:|---:|
| R1d on the holdout, the confirmed test | +0.96% (t 3.62), 2,822 trades | +0.97% (t 3.64), 2,829 trades |
| Main rule on the holdout | +1.52% (t 3.68) | +1.52% (t 3.69) |
| Main rule, all three years | +1.64% (t 4.84) | +1.64% (t 4.86) |

**Round two's thin-market results do not.** "Thin at the time" is every news
market while it had traded 20,000 to 100,000 shares, whatever it traded
later, short-lived markets included.

| Rule | As round two had it | The thin part of markets that ended bigger | Thin at the time |
|---|---:|---:|---:|
| R1d, 95–99¢, legs included | +1.69% (t 9.0), 31 lost of 3,135 | −0.95% (t −2.9), 121 of 3,358 | **+0.33% (t 1.7)**, 152 of 6,502 |
| Main rule, 95–98¢, stand-alone | +1.96% (t 6.0), 18 of 1,393 | −0.20% (t −0.3), 33 of 933 | **+1.10% (t 3.4)**, 51 of 2,332 |
| 90–98¢, stand-alone | +2.40% (t 5.5), 53 of 1,744 | −1.41% (t −1.7), 97 of 1,415 | **+0.70% (t 1.5)**, 150 of 3,168 |
| 90–95¢, stand-alone | +3.24% (t 5.2), 41 of 1,073 | −2.42% (t −2.2), 88 of 962 | **+0.57% (t 0.9)**, 129 of 2,037 |
| The thin account's rule (90–98¢, calm) | +2.52% (t 5.8) | −1.26% (t −1.5) | **+0.83% (t 1.7)** |
| The same with a resting bid (TM) | +3.57% (t 5.6) | −0.97% (t −1.0) | **+1.42% (t 2.3)** |

What this takes back from [round two](04_second_round.md):

- *"The first round's rule repeats in thinner markets, and is larger there."*
  It repeats in the 95–98¢ band at about two-thirds of its size in big
  markets (+1.10% against +1.64%), and not in any wider form. Priced at the
  three-day average a larger order would pay, it is +0.84% (t 2.6).
- *"The 90–95¢ band, which failed in big markets, earns 3% in thin ones."* It
  earns nothing there either.
- *TM, "resting bids pass".* The bar was positive with |t| ≥ 3 and above the
  ask version with |t| ≥ 2. Thin at the time: +1.42% (t 2.3), 0.59 points
  above the ask (t 2.1). **Not passed.** Bid-first-then-ask earns 0.91% per
  first signal against 0.71% for the ask alone, where round two reported 2.63
  against 2.14.
- *"Adding the thinner markets lifts a 2% account from 6.7% to 9.6% a year."*
  Adding their 95–98¢ band lifts it to 8.9% (and to 12.4% from 12.1% at 4% a
  position). Adding the 90–98¢ band, which is what the thin paper account
  was trading, cuts it to about 2% a year and more than doubles the worst
  drawdown, to −10% at 2% a position and −20% at 4%.

A third thing was wrong in the same family, in the account simulation this
time. Lists of trades were combined by a fixed preference ("the big-market
trade if there is one"), which drops the early purchase of any market that
qualified again later and keeps the purchases of markets that never did.
Accounts now take each market at its earliest entry (`at_the_time.account`).
With universes that did not share markets, as in rounds one and two, the old
rule did no harm; with universes defined at the time it would have.

## 5. The tests

Run at 20:16 UTC on 10 November, on the corrected universe: 110,040 markets
while they had traded 5,000 to 20,000 shares (`thinner_output.txt`,
`t5_*.csv`). The universe as first fixed is in the last column to show what
the flaw is worth: every one of these numbers would have been reported in
good faith an hour earlier.

| Test | Bar | Result on the corrected universe | Verdict | On markets that *ended* at 5,000–20,000 |
|---|---|---|---|---|
| **T5** R1d, 95–99¢, legs included | positive, \|t\| ≥ 3 | −0.26% (t −1.3), 201 lost of 7,306 | **Not passed** | +1.58% (t 8.1), 19 of 2,410 |
| **T5-Y** the leader | positive, \|t\| ≥ 3, exact p < 0.01 | +1.07% (t 1.9), 9 lost of 536, p = 0.08 | **Not passed** | +1.31% (t 1.9) |
| **T5-L** long-dated "No" | positive, \|t\| ≥ 3 | +2.51% (t 2.7), 24 lost of 696 | **Not passed** | +4.47% (t 3.8), 92 trades |
| **T5-N** which side | sign here, pooled \|t\| ≥ 3 | "No" minus "Yes": +4.86 points (t 3.9); pooled over three universes +3.63 (t 4.4) | **Decision rule met: drop the "Yes" side** | +2.68 (t 1.9) |
| **T5-TM** resting bids | positive, \|t\| ≥ 3, above the ask with \|t\| ≥ 2 | +0.82% (t 1.2); 0.49 above the ask (t 1.1) | **Not passed** | +4.64% (t 3.6) |
| **T5-H** "No" at 50–90¢ | positive, \|t\| ≥ 3 | +1.96% (t 1.8), +1.65¢ a share (t 2.2), 3,846 trades | **Not passed** | +6.63% (t 3.2) |

Of the predictions written with T5-H, two held: more with 20–60 days left
(+3.68%, t 2.6) than with 3–20 (+0.02%), and "Yes" at 10–50¢ losing far more
than a spread and a fee (−18.6% a trade, t −6.1). The main rule in these
markets earns +0.64% (t 1.8), and +0.45% (t 1.3) at the three-day average.

Five bars missed and one decision rule met. The count of tests with a bar
across the three rounds is 27; two have passed cleanly (R1d in the first
round and the side comparison here), one met its bar on paper and was set
aside (A1), and one passed on a universe that turned out to be chosen with
hindsight and does not pass on the corrected one (TM).

## 6. Three sizes of market, measured the same way

The corrected universes side by side (`scripts/run_sides.py`, `s3_*.csv`, and
the T5 output). Big and thin had been read before; thinner is the out-of-
sample column. Return per trade with event-clustered t, then losses.

| Bought, 3–60 days to run unless stated | Big: 100,000 or more | Thin: 20,000–100,000 | Thinner: 5,000–20,000 |
|---|---:|---:|---:|
| R1d: 95–99¢, legs included | +1.05% (4.5) | +0.33% (1.7) | −0.26% (−1.3) |
| Main rule: 95–98¢, stand-alone | +1.64% (4.9) | +1.10% (3.4) | +0.64% (1.8) |
| Stand-alone "No", 95–99¢ | +1.52% (4.9), 30 of 1,944 | +1.06% (3.8), 46 of 2,589 | +0.67% (2.1), 50 of 2,576 |
| Stand-alone "Yes", 95–99¢ | +0.79% (0.7), 5 of 252 | −0.51% (−0.5), 12 of 369 | −1.23% (−1.3), 17 of 450 |
| Stand-alone "No", 90–98¢ | +1.94% (3.9) | +1.19% (2.4) | +1.28% (2.9) |
| Stand-alone "Yes", 90–98¢ | +1.08% (0.9) | −2.10% (−1.5) | −3.58% (−3.1) |
| The leader (leg, "Yes"), 95–99¢ | +2.85% (7.2), 1 of 265 | +1.04% (1.6), 10 of 510 | +1.07% (1.9), 9 of 536 |
| An also-ran (leg, "No"), 95–99¢ | +0.07% (0.2) | −0.31% (−1.1) | −1.00% (−3.5) |
| Long-dated "No": 90–98¢, 60–180 days | +5.41% (9.9), 7 of 524 | +4.11% (6.4), 16 of 691 | +2.51% (2.7), 24 of 696 |
| "No" at 50–90¢ | +3.77% (2.1) | +4.65% (3.7) | +1.96% (1.8) |
| "No" at 50–90¢ with 20–60 days left | +5.54% (2.5) | +6.78% (4.0) | +3.68% (2.6) |
| "Yes" at 10–50¢ | −21.0% (−4.2) | −22.4% (−6.2) | −18.6% (−6.1) |

**Every row that works fades as the markets get smaller.** Round two said
the opposite and had it backwards. The mistake this project trades is the
crowd's, and it is largest where the crowd is: in the markets people are
watching, with many small buyers of the long shot and a deep book to sell
them from. In a market that has traded 8,000 shares there is no crowd, the
spread is wider than the edge, and the last price may be days old.

**The stand-alone "Yes" never works.** Three universes, two bands, six
cells: four negative, none above t = 0.9.

**The long-dated "No" is the strongest thing found since the first round,
and it is not confirmed.** It was not tested in the two universes where it is
strong, only explored there, and where it was tested it fell short of its
bar. What it has going for it: the one out-of-sample number is positive at
t = 2.7 in the universe where nothing else reaches 2.1; the big-market
figure rests on seven losses in 524 trades, positive in each year (+4.9%,
+5.2%, +6.2%), at 60–120 days (+5.6%, t 12.8) and at 120–180 (+5.0%, t 5.2);
and the reason is ordinary. Nobody on Polymarket wants to lock up 94¢ for
three months to make 6¢, so the 6¢ is still there.

### Every price, each side

Cents a share after fees, stand-alone Yes/No markets, 3–60 days to run, each
side bought the first time its ask enters the band:

| Price paid | Big: "No" | Big: "Yes" | Thin: "No" | Thin: "Yes" | Thinner: "No" | Thinner: "Yes" |
|---|---:|---:|---:|---:|---:|---:|
| 3–10¢ | −2.3 | −2.9 | +1.0 | −2.4 | +1.9 | −2.2 |
| 10–20¢ | −1.7 | −2.2 | +2.8 | −3.6 | +2.9 | −3.8 |
| 20–35¢ | +1.6 | −2.9 | +4.3 | −4.5 | +4.8 | −4.7 |
| 35–50¢ | +4.9 | −5.9 | +4.7 | −6.7 | +4.1 | −3.7 |
| 50–65¢ | +3.9 | −7.1 | +3.6 | −8.9 | −0.1 | −7.8 |
| 65–80¢ | +1.3 | −5.0 | +2.3 | −7.6 | +2.2 | −7.8 |
| 80–90¢ | +0.9 | +0.9 | +2.1 | −4.6 | +1.8 | −3.9 |
| 90–95¢ | +1.8 | +1.6 | +1.1 | −2.7 | +1.8 | −4.5 |
| 95–98¢ | +1.6 | +1.2 | +1.2 | 0.0 | +1.0 | −1.7 |

"Yes" lost money in 23 of the 27 cells, at every price in the out-of-sample
column, and most of those with a t beyond −2.5. "No" made money in 24 of 27.
At 50–65¢ in the thin markets "No" won 62% of the time and "Yes" 50%, bought
at the same price. This is the plainest statement of what the crowd gets
wrong, and it is the thesis of the project turned over: the crowd's shifts
cannot be predicted, but its lean can. Asked "will this happen?", it pays
too much for "Yes".

It is not, so far, a second strategy. A "No" buyer has to pay the ask and the
fee out of that lean, and what is left is one to five cents a share with a t
near 2 in any one band. The test fixed for it (T5-H) did not pass. The part
that keeps appearing, "No" at 50–90¢ with three weeks or more to run, is
positive in all three universes (+5.5%, +6.8%, +3.7%); it is the first thing
to test on new data, and the forward log now records what is needed to do
that (section 8).

### Paying the ask or leaving a bid

Round two's test of resting bids rested on the flawed sample and is
withdrawn. On the corrected universes, for the "No" side only, and only for
signals whose bid and ask were within 3¢ of each other, which is what the
accounts require before they trade (`s3_bid_or_ask.csv`; exploratory):

| "No" bought | Big: at the ask | Big: resting bid | Thin: ask | Thin: bid | Thinner: ask | Thinner: bid |
|---|---:|---:|---:|---:|---:|---:|
| 95–98¢, 3–60 days | +1.76% (4.9) | +2.35% (5.8) | +1.38% (3.9) | +1.53% (3.3) | +1.50% (4.1) | +1.92% (3.6) |
| 90–98¢, 3–60 days | +1.88% (3.7) | +2.31% (4.1) | +1.30% (2.5) | +1.40% (2.2) | +1.65% (3.7) | +2.24% (4.0) |
| 90–98¢, 60–180 days | +4.75% (7.2) | +5.32% (7.2) | +3.77% (5.7) | +4.41% (5.6) | +2.08% (2.0) | +3.61% (3.6) |
| Share of the bids that filled | | 92–97% | | 82–93% | | 78–85% |

A bid left at the day's bid for three days did better than the ask in all
nine cells, by a tenth of a point to a point and a half, and most of the
bids filled. None of the differences would pass a test on its own. For the
long-dated account, where there is no hurry at all, it was enough to make it
bid first and pay the ask only after three days.

The same table shows something that was not looked for. With the spread
limit on, the thinnest markets do much better than in the tests of section 5,
which had no such limit: "No" at 95–98¢ earns +1.50% (t 4.1) there instead of
+1.01% (t 2.8). A wide gap between the last purchase and the last sale is a
sign that nobody is quoting the market, and the markets nobody quotes are
where the rule fails. This is an observation made after the fact on data
that has now been read, so it changes nothing by itself: no account trades
below 20,000 shares. It does mean the paper accounts, which have always
required a tight spread, are trading a slightly better rule than the one
that was backtested.

## 7. As accounts

`scripts/run_third_accounts.py` (`a3_*.csv`): $1,000, positions capped at a
tenth of what takers bought in range and priced at the three-day average, one
position per event, four per story, at most 80% invested, each market taken
at its earliest entry.

| Account | 2% a position | 3% | 4% | 5% | Worst drawdown (2%–5%) |
|---|---:|---:|---:|---:|---:|
| The main account as it was: big, 95–98¢, either side | 6.7% a year | 9.7% | 12.1% | 12.6% | −4.5% to −9.0% |
| "No" only | 6.7% | 9.4% | 10.2% | 11.1% | −3.7% to −8.1% |
| Long-dated "No" alone, 20,000 shares or more | 7.0% | 6.5% | 7.2% | 8.4% | −3.0% to −6.8% |
| "No" only plus long-dated "No", one account | 7.1% | 6.7% | 9.4% | 9.7% | −3.0% to −6.6% |
| The same plus thin 95–98¢ "No" | 5.9% | 6.9% | 6.6% | 7.3% | −4.2% to −8.7% |

Three things to take from it.

*Dropping the "Yes" side costs nothing and gains nothing in big markets*,
where "Yes" was the smaller part (197 of 1,838 trades) and roughly broke
even. The case for dropping it is the other two universes.

*The long-dated sleeve is a second income of about the same size, not an
addition to the first inside one account.* On its own it earns 6.5–8.4% a
year with half the money in use. Put into the main account it competes for
the same events and the same stories, holds each slot five times as long,
and the total barely moves. It pays as a separate pot of money: the main
rule leaves two-thirds of an account idle at 2% a position, and a second
$1,000 in long-dated positions earns its $70–90 a year where the first
$1,000 could not have used it.

*These are small numbers.* The honest range for the whole strategy is 7–12%
a year on a small account, with the losses of three particular years. The
per-trade statistics are strong; the money is limited by how many separate
events there are to bet on, not by how good each bet is.

One limit in that sentence is the account's own. It holds at most four
positions in any one story (a tag shared by a few markets: a war, a trial, an
election). In the history that limit cost about two points a year and bought
nothing visible (`a3_caps.csv`, "No" only, $1,000 at 2% a position):

| Positions allowed in one story | Trades taken | Per year | Worst drawdown |
|---|---:|---:|---:|
| 4 (the accounts today) | 635 | 6.7% | −3.7% |
| 8 | 754 | 8.5% | −3.6% |
| 16 | 835 | 9.6% | −3.6% |
| No limit | 888 | 9.6% | −3.6% |

The limit is insurance against one piece of news taking several positions at
once, and these three years hold 29 losses that did not come in clusters, so
the table cannot price it. It is left at four. It is a choice about risk, and
the cheapest one to revisit.

## 8. What changed in the system

- **Every account buys the "No" side only** (`no_side_only`, on by decision
  of T5-N). The "Yes" side is still logged, and `kht shadow` now scores the
  two sides apart, so the comparison runs forward on live prices.
- **The thin-market account trades 95–98¢** instead of 90–98¢. The wider band
  rested on round two's universe. Positions it already holds are kept to
  resolution.
- **The bid-first thin account is withdrawn.** TM did not pass on the
  corrected universe. It had not yet run a cycle.
- **A long-dated account is added** (`config/paper_long.json`,
  `state/paper-long/`): "No" at 90–98¢ with 60 to 180 days to run, in
  markets with 20,000 shares or more. It leaves a bid for three days and
  pays the ask after that. It is there because a forward test is the only
  clean test left for it, and a paper account costs nothing. On its first
  dry run against live books it found twelve contracts to buy ("US recession
  by end of 2026?", "9.0 or above earthquake before 2027?", "Friedrich Merz
  out as Chancellor before March 31, 2027?").
- **Mid-priced signals are logged on both sides** (`wide_watch_lo`, on in the
  main and thin accounts): stand-alone contracts from 50¢ up to the band the
  log already covered, never traded. `kht shadow` scores their "No" and
  "Yes" sides apart. On a dry run of the main account's next cycle this
  logged 62 of them, 50 on the "No" side. It is the forward test of the table
  in section 6: "No" at 50–90¢ missed its bar on history, and this is how it
  gets a second hearing on prices nobody has seen yet.
- `scripts/at_the_time.py` is now the only way a research universe is built.

## 9. Verdict on the third round

| Idea | Result |
|---|---|
| The rule in markets thinner still | No. It fades with size and is gone below 20,000 shares |
| Round two's "larger in thin markets" | Withdrawn: produced by choosing markets on their final volume |
| Resting bids in thin markets (TM) | Withdrawn: not passed on the corrected universe |
| **Buy "No", not "Yes"** | **Confirmed** on untouched markets (t 3.9) and pooled (t 4.4) |
| The leader of a multi-way event | Strong in big markets (1 loss in 265), not elsewhere; not passed |
| Long-dated "No" | t = 9.9 and 6.4 where explored, 2.7 where tested; not passed; in forward test |
| "No" at 50–90¢ | Positive everywhere, significant nowhere it was tested; not passed |
| The first round | Stands unchanged |

The strategy at the end of the third round: **in news markets that people
are watching, buy "No" on a stand-alone question when it is nearly certain,
and hold it.** Two ways to do that are running on paper, with 3–60 days to
go (confirmed) and with 60–180 (exploratory). It is a bet against the
crowd's belief that things will happen, which is a statement about
psychology and has now been found at every price, in three sizes of market,
on both sides of a pre-registered test.

What the round cost is the comfortable idea that a small account has a
private hunting ground in tiny markets. What it bought is a strategy that is
described correctly, and three specific ways the same mistake was made
(markets chosen on final volume; markets chosen on how long they lived;
trades chosen on what the market did later) with a tool that prevents the
first two. All three were found by distrusting a result that looked too
good, and two of them before the data they would have spoiled was read.

What would change the estimate fastest: the forward log. It records every
signal on both sides in four accounts, and on each cycle it adds live
evidence on the one claim that has passed a test this round.
