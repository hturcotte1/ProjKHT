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
