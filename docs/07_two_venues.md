# 07 — Two exchanges, one question

*Started 11 November 2026. Sections 1 to 3 were written and committed before
the two exchanges' prices had been compared with any outcome; the commit time
is the evidence. Results are added from section 4 on.*

## 1. The idea

Polymarket US and polymarket.com list many of the same questions, under the
same titles, with the same answers. They are separate exchanges with
separate order books and separate crowds. A US resident may trade only the
first. Everyone else may trade only the second. Almost nobody can trade
both, so nothing forces the two prices together.

Anyone can read both.

This project's thesis is that what a crowd believes can be traded more
reliably than what will happen. Two crowds quoting the same event side by
side is the cleanest case of it there is. polymarket.com is the older and
much larger market. If the larger crowd's price is the better forecast, then
whenever the two disagree the smaller exchange is mispriced, in a direction
known at the time, and a US account can take the cheap side.

This is not arbitrage. The other leg cannot be traded from the United
States, and this project never sends an order to polymarket.com from
anywhere. It is a bet that the other crowd is right, made only where the
price difference is larger than the fee. Reading polymarket.com's public
prices is not trading there.

Three things have to be true for it to be worth anything:

1. the prices differ by more than the US fee often enough;
2. when they differ, polymarket.com is right more often than Polymarket US;
3. there is something to buy at the US price.

The first can be seen today (section 2). The second needs outcomes, and is
what section 3 fixes a test for. The third needs order books with sizes,
which only the recorder of docs/06, section 8, can supply.

## 2. What can be seen before any test

**The same markets exist on both.** Pairing is strict (`kht.trading.twins`):
the event titles must be equal once case and punctuation are removed, and so
must the answer's label. That rule exists because look-alikes are common. On
"Alabama Senate Election: Turnout" the US contracts are thresholds ("Above
1.2M") and the polymarket.com contracts are ranges ("1.2M–1.3M"). On House
races the US lists candidates and polymarket.com lists parties, which is not
the same thing where two candidates of one party meet. Neither is paired.

In a trial cycle of the recorder on 11 November, 325 of the 2,616 US markets
showing a quote had a twin: 198 in politics, 101 in culture, 26 elsewhere.

**The prices disagree.** Of those twins, 210 had orders on both sides of
both books.

| | |
|---|---:|
| Twins with both books two-sided | 210, in 98 events |
| Of those, both spreads at most 10¢ | 138 |
| Middle prices at least 2¢ apart | 49 of the 138 |
| At least 5¢ apart | 18 of the 138 |
| US price the higher one / the lower one | 81 / 51 |
| Twins where a US quote is beyond the polymarket.com quote by more than the US fee | 54 of the 210 |
| of which the cheap side on US is "No" / "Yes" | 39 / 15 |

In one twin in four, somebody on Polymarket US was offering to sell below
what somebody on polymarket.com was bidding, or the reverse, after the fee.

**The US price leans high.** The US "Yes" is the dearer one more often than
not, and the cheap side on US is "No" in 39 cases of 54. That is the
direction every earlier round found: crowds pay too much for "Yes". Here
the smaller crowd pays more than the larger one.

**The amounts are small.** Taking all 54 gaps at the best US price would
have cost $103,600, nearly all of it in long shots bid at 1¢ against a
polymarket.com price of a fraction of a cent, which are worth almost
nothing. The 21 gaps of 3¢ or more could have been bought for $473, and if
polymarket.com's prices were exactly right they were worth $50. What matters
is how fast gaps like these reappear, and one snapshot cannot say.

**What a gap might be instead of a mistake.** The two contracts may have
different rules: Polymarket US can close a market at 50¢, and its
resolution sources are not always the same. The polymarket.com price may
itself be stale where that market is thin. And some of the largest gaps are
in markets about an election that has already been held, where one book
simply has an order nobody has cancelled.

## 3. The tests, fixed before any is run

### The data

- **Pairs.** Every settled Polymarket US market outside sports whose
  question has a twin on polymarket.com under the strict rule; the twin is
  looked for by searching polymarket.com for the US event's title
  (`scripts/two_venues.py pairs`). Every pair is kept, including pairs whose
  two contracts turned out to pay different sides. Those count against the
  idea, as they should: the trader holds the US contract and is paid by its
  rules. How often the two agree is reported.
- **The US price** is the daily price history, on days that pass the filter
  of docs/06, section 7: both prices between 2¢ and 98¢, one tick to 20¢
  apart. About one such day in fifty is still a filled-in price.
- **The polymarket.com price** is its hourly price series for the twin's
  "Yes" token. The value used at a US observation is the last one stamped at
  least one hour earlier, and no more than a day earlier. Nothing later than
  the US quote is ever used.

At a US observation write a for the US ask of "Yes", b for the US ask of
"No" (one minus the bid for "Yes"), P for the polymarket.com price of "Yes",
and fee(p) = 0.095 × p × (1 − p). The gap on the "Yes" side is
P − a − fee(a). The gap on the "No" side is (1 − P) − b − fee(b). They
cannot both be positive.

### T6-B, the main test: does buying the cheap exchange pay?

Each market is bought once: on the first observation where either gap is at
least g, the side with the gap, at the US ask of that same observation plus
the fee, and held to settlement. The return is what the US contract paid,
less the cost, over the cost.

- **The threshold is g = 3¢.** Also reported, not tested: 1¢, 2¢, 5¢, 10¢,
  and gaps between 3¢ and 10¢.
- **The score** is the mean return with the z of docs/06, section 4
  (variance never below what the prices paid imply), clustered by US event
  and, separately, by day of settlement.

It passes on history if all of these hold:

1. at 3¢ the mean return is positive with z ≥ 2.58 under both clusterings;
2. **the other side loses.** At the same observations, buying the side
   polymarket.com says is dear must return less than zero. If both sides
   earn about the same, the gap carried no information;
3. **it survives a day's delay.** The same rule buying one observation
   later, at that day's US ask, if the gap is still at least 3¢ on that
   day's prices, is positive with z ≥ 2 by event. A filled-in price is the
   likeliest thing to produce a large false gap, and the likeliest thing to
   be gone a day later;
4. **it does not live only in the largest gaps.** Gaps between 3¢ and 10¢
   alone are positive with z ≥ 2 by event;
5. it is positive without the markets settled on 3 to 5 November.

### T6-A: which price is the better forecast?

On the first observation of each market where P and the middle of the US
book differ by at least 3¢, compare the two squared errors against what the
US contract paid. The mean difference, clustered by event and by settlement
day, says which exchange was closer. This uses no asks and no fee, so it is
less exposed to filled-in prices than T6-B, and it is the direct statement
of condition 2 of section 1.

### T6-C: who moves?

On consecutive daily observations, regress the next day's change in the US
middle price on today's difference P − (US middle), and the next day's
change in P on the same difference. If Polymarket US follows polymarket.com,
the first slope is positive and the second is near zero. No outcome enters
this at all, so one election night cannot drive it.

### What will be reported whatever happens

The number of pairs, how often the two contracts paid the same side, every
threshold, both clusterings, the split by category and by the size of the
polymarket.com market (under and over $10,000 traded), and the failures.

### What a pass would and would not mean

A pass makes this a candidate, not a strategy. The US history has no sizes,
and its filled-in prices could gather exactly where gaps look largest. The
decisive test is forward, on real order books of both exchanges read at the
same moment, and it is fixed now.

### F1, the forward test

From the recorder's snapshots (`state/us/`), a paper purchase is made the
first time a US market shows, against a polymarket.com book that is
two-sided and at most 10¢ wide:

- "Yes": (polymarket.com bid) − (US ask) − fee ≥ 3¢, or
- "No": (US bid) − (polymarket.com ask) − fee ≥ 3¢,

for the contracts on offer at the best US price, up to $50. One purchase a
market. Each is scored three ways:

1. **after 1, 3 and 7 days, at what it could be sold for on Polymarket US**
   (the US bid for that side, less the fee). This is realisable profit and
   does not wait for settlement;
2. after the same intervals, at the middle of the polymarket.com book;
3. at settlement.

It is confirmed if the first score, at 7 days, is positive with z ≥ 2.58
clustered by event on at least 100 purchases. The recorder also counts how
many dollars of new gaps appear each day, which is the capacity of the
whole idea.

## 4. Result: it fails

`scripts/two_venues.py` (`reports/research/tv_tests.csv`,
`tv_trades_3c.csv`, `two_venues_output.txt`). Run on 11 November at
06:24 UTC, seven minutes after section 3 was committed.

**Buying the side that looked cheap on Polymarket US lost money. On this
history the polymarket.com price was not the better forecast.**

### The sample

| | |
|---|---:|
| Settled US markets paired with a polymarket.com twin | 2,462, in 1,074 events |
| Both contracts settled at 0 or 1 | 1,920 |
| Paid the same side | 1,917 (99.84%) |
| US market-days with a real book | 60,258, in 2,235 markets |
| Of those, with a polymarket.com price 1 to 24 hours older | 20,316, in 1,534 markets and 804 events |

The pairing is sound. The three pairs that paid different sides were events
with the same title from another year or season, whose price series do not
overlap and so produce no observations. The sample is politics: 1,472
markets, against 48 in culture and 14 in economics.

The two prices differ by 3¢ or more on 15% of days and by 10¢ or more on
3.5%. On average they are the same to a tenth of a cent.

### T6-B: the main test

| Gap after the fee | Trades | Events | Return of the cheap side | z by event | z by day | Return of the other side |
|---|---:|---:|---:|---:|---:|---:|
| 1¢ or more | 943 | 569 | −20.0% | −2.5 | −2.0 | −40.1% |
| 2¢ or more | 618 | 344 | −20.4% | −2.1 | −1.2 | −26.9% |
| **3¢ or more** | **505** | **279** | **−19.8%** | **−1.8** | **−1.1** | −21.8% |
| 5¢ or more | 363 | 209 | −15.2% | −1.1 | −0.6 | −23.0% |
| 10¢ or more | 214 | 127 | +19.9% | 0.9 | 0.5 | −32.1% |

| Condition fixed in section 3 | Result | |
|---|---|---|
| 1. Positive at 3¢ with z ≥ 2.58 both ways | −19.8%, z −1.8 and −1.1 | **fails** |
| 2. The other side loses | −21.8% | holds, but the cheap side loses as much |
| 3. Survives a day's delay | −46.9% on 124 trades (z −1.8) | **fails** |
| 4. Positive between 3¢ and 10¢ | −42.8% on 352 trades (z −3.4) | **fails** |
| 5. Positive without 3 to 5 November | +67.1% on 95 trades (z 1.8) | holds |

Per contract, the purchases cost 43.7¢. polymarket.com said they were worth
54.8¢. They paid 43.0¢. The US price was the right one.

### T6-A and T6-C

- **Which price was closer.** On the first day the two were 3¢ apart,
  polymarket.com was the closer one in 63% of 790 markets, but the
  difference in squared error is small (0.009; t 2.0 by event, 1.1 by
  settlement day). Over all paired markets the two exchanges are equally
  accurate: mean squared error 0.0356 for Polymarket US and 0.0360 for
  polymarket.com, on 1,497 markets taken once each with at least three days
  left. (That last comparison was made after the tests and was not fixed in
  advance.)
- **Who moves.** Each day the US price closes 16% of the gap (z 3.5) and
  the polymarket.com price closes 18% of it (z 4.3). They move towards each
  other at the same pace. Neither leads.

### Why it failed

Two things, read off the losing trades after the fact.

**For most of these questions polymarket.com is the smaller market.** The
idea rested on its being the larger crowd. Half of the twins traded in T6-B
had done under $8,000 of business on polymarket.com in their whole life,
and a tenth under $700. A recorded "price" of 38¢ on a contract that has
traded $63 is the middle of an empty book, while Polymarket US was quoting
the same thing at 4¢ against 98¢ and was right. Of the 505 purchases, 124
were long shots that cost under 10¢ on US: polymarket.com had them at 18¢
on average, and 1.6% of them paid.

**Where polymarket.com was large, it was wrong on the night.** In the 84
trades whose twin had traded $100,000 or more, the rule mostly bought
Republicans, because polymarket.com priced them higher than Polymarket US
did: 24 Republican "Yes" purchases, of which 7 won, and 31 Democrat "No"
purchases, of which 10 won. The two crowds leaned different ways on the
midterms and the US one was nearer. That is one election, and would prove
nothing about the next. It is also the only evidence there is.

Splitting by the size of the polymarket.com market, as section 3 said would
be reported, does not rescue the rule: under $10,000 it returned −8.3%, and
at $10,000 or more −33.2% (z −2.8).

### What is left

The forward test F1 stays as fixed. It uses quotes that could really be
traded on both exchanges at the same moment, and it requires a
polymarket.com book no wider than 10¢, which removes the empty-book prices
that did the most damage here. The recorder collects what it needs at no
cost. But the reason for expecting it to pass has gone: the larger exchange
was not the better forecaster, and the two prices drift towards each other
rather than one towards the other. If F1 does pass its own bar it will be
reported as a surprise that needs explaining, not as a confirmation.

The gaps seen live in section 2 are real quotes. What this test says is
that taking them is not known to pay.
