# 04 — Second round: looking for something better than a thin edge

*Started 2026-11-10 at 18:00 UTC. Sections 1 to 4 were written and committed
before any of the tests in section 4 was run; the commit time is the evidence.
Results are added from section 5 on.*

## 1. Where the first round left things

One rule passed: buy near-certain contracts and hold them. It is real on three
years of data and thin: about +1.5% a trade, 7–9% a year on a small account,
two-thirds of the money idle, and a year or more before new data can confirm
it. The original idea, trading the shift in the crowd's price, failed in every
form.

This round asks a different question of the same finding. The edge exists
because the crowd overpays for long shots and nobody is paid to correct it.
**Where is that mistake largest, and what does the crowd fail to look at when
it makes it?** Three things would make the strategy better than it is:

1. a larger gain per trade, by finding the contracts where the mistake is
   biggest;
2. more separate bets, so that more of the money works;
3. a faster verdict from new data.

## 2. Ideas considered

Each has to name the mistake, the reason it survives, and a test.

| # | Idea | The mistake it would exploit | Status |
|---|---|---|---|
| 1 | **Quiet favourites.** Among near-certain contracts, buy the ones that have not moved for two weeks | The crowd prices a favourite the same whether its market is in the news or forgotten, but the risk that something happens is not the same | **Test now** (track A) |
| 2 | **An outside yardstick for price markets.** "Will Bitcoin reach $X by Friday" has a fair value that can be worked out from Bitcoin's price and how much it moves. Buy where Polymarket's price is furthest from it | Lottery buyers on Polymarket pay more for far-off price targets than the same bet costs in the options market, where professionals set the price | **Test now** (track C) |
| 3 | **The confirmed rule in places it has never been tried.** Crypto price markets were left out of the first round entirely: 8,510 resolved markets | Same as the first round; a rule that is real should repeat where it has not been fitted | **Test now** (track C) |
| 4 | **Get out when the yardstick says the bet has turned.** A price drifts towards a target before it reaches it, so a losing "No" can be sold part-way | None: this is risk control, which lets positions be larger | After 2 |
| 5 | **Size positions by the evidence** instead of a flat $20 | None: two-thirds of the account is idle | Analysis, section 4 |
| 6 | Slow spread of news between related markets (a move in "by November" before "by December") | Thin sister markets update late | Later; costs are doubled and the first round found that news is in the price within a minute |
| 7 | Pairs of deadlines for the same event, traded against each other | The crowd's sense of "when" is worse than its sense of "whether" | Later; two spreads to pay |
| 8 | Quote both sides and collect Polymarket's liquidity rewards while waiting | None: a payment for providing prices | Needs live order books; cannot be tested on history |
| 9 | Weather markets against forecast models | The crowd anchors on yesterday's forecast | Later; small universe |
| 10 | Other venues' prices as the yardstick for non-price markets | One crowd is better informed than the other | Later; matching questions across venues is slow work |
| 11 | Read the fine print: trade where the headline and the resolution rule disagree | People trade the headline | Cannot be tested on history without hindsight |
| 12 | Bet against first-time wallets | Newcomers herd | Dropped: the first round found the least skilled wallets do not lose beyond costs |
| 13 | Buy at 99¢ after the result is known and wait for the payout | Impatience | Dropped: the first round found nothing in the top cent |

Why 1 and 2 first. Both follow from evidence already in hand and both say
something specific about what the crowd overlooks.

*Quiet favourites.* Two numbers in the first-round findings disagree. Counting
every day a contract spends at 90–95¢, such contracts earned +3.1¢ a share
(t = 6.5). Counting each market once, on the first day it gets there, the same
band earned +0.9% a trade and failed its test. The difference is the contracts
that stay: a market that sits at 93¢ for a month is counted thirty times in
the first number and once in the second. The late-entry check pointed the same
way (contracts that had been in the band twenty days lost 3 times in 435,
against 33 in 1,836). A market goes quiet when the story behind it has gone
quiet, and stories that have gone quiet tend to stay that way, but a 93¢ price
with a month to run still has to pay somebody for locking up their money, so
it stays at 93¢.

*An outside yardstick.* For most markets there is no way to know what a fair
price is. For a market on the price of Bitcoin there is: the distance to the
target, the time left and how much Bitcoin moves give a probability, and the
options market publishes its own estimate of how much Bitcoin will move. If
the crowd overpays for long shots everywhere, it should overpay most visibly
here, and here the size of each mistake can be measured before the bet is
made instead of assumed from an average.

## 3. Rules of evidence for this round

The same as before, tightened where the first round showed a weakness.

- A result counts only at |t| ≥ 3, with standard errors clustered so that bets
  that win or lose together count once. The first round tried ten rules and
  one wallet-following test; this round adds three (A1, C1, C2). The running
  count is reported with every result.
- Prices are prices somebody paid: entries at the next taker-buy print after
  the signal, today's fee charged, markets used only once they have already
  traded 100,000 shares.
- The first round's two samples have both been opened. A test on them is
  called what it is: a prediction made before looking, on data that has been
  examined for other questions. Only an untouched universe or new data is
  called a confirmation.
- Crypto price markets are untouched. They are split by scheduled end date
  into a discovery set (before 1 June 2026) and a holdout (from 1 June 2026).
  Nothing is computed on the holdout until the rules for it are committed.

## 4. Tests fixed in advance

### Track A: quiet favourites

**Data.** The first round's panel: non-sports, non-crypto resolved markets
with a life of two days or more, daily prices rebuilt from the trade tape,
used only once a market has traded 100,000 shares.

**Definition.** For an outcome at the end of day D, its *two-week range* is
the highest minus the lowest price at which it traded on days D−13 to D
(trades in the other outcome count at one minus their price). The outcome is
**quiet** if that range is 3¢ or less and the market had already been in the
panel on day D−13.

> **A1.** In stand-alone markets (not a leg of a multi-outcome event): when an
> outcome's ask is above 90¢ and at most 95¢, the scheduled end is more than 3
> and at most 60 days away, and the outcome is quiet, buy it at the first
> taker-buy print on a later day, within 3 days, if that print is above 90¢
> and at most 95.5¢. Pay today's taker fee. Hold to resolution. One trade per
> market, on the first day it qualifies.

**Control.** The same band, horizon and entry on the first day an outcome is
in the band and *not* quiet.

**Bar.** A1 earns a positive average return per trade with |t| ≥ 3, clustered
by event, over all resolved markets in the panel; and A1 beats its control
with |t| ≥ 2 on the difference. If either fails, the trading system is not
changed.

The 90–95¢ band is chosen because it is where buying on arrival failed and
where this cut has never been made. It is not untouched data in the strict
sense: the day-counted figure that prompted the idea came from it.

Reported alongside, not used to choose anything: the same rule at 95–98¢ (A2,
already partly seen); in legs of multi-outcome events (A3); entered with a
resting bid under the first round's fill rule (A4); ranges of 2¢ and 5¢;
windows of 7 and 28 days; each of the first round's two samples; each year.

### Track C: crypto price markets

**Data.** Every resolved crypto market with 100,000 shares or more and a life
of two days or more whose question is about a price on a date ("above",
"below", "between") or a price being touched within a period ("reach", "hit",
"dip to"). Five-minute, hourly and daily "up or down" markets are left out.
8,510 markets. Trade tapes are downloaded for all of them; the holdout's
tapes are not read until its rules are committed.

**Clustering.** By the calendar week of the scheduled end, all coins
together, because one move in Bitcoin settles every target that week.

> **C1 (replication).** The main paper account's rule exactly as configured:
> ask above 95¢ and at most 98¢, not a leg of a multi-outcome event, scheduled
> end more than 3 and at most 60 days away, bought at the first taker-buy
> print on a later day within 3 days if still in range, hold to resolution,
> with the crypto fee rate of 0.07. Also the pre-registered R1d (95–99¢, legs
> included).

**Bar for C1.** Positive with |t| ≥ 3 on the discovery set, and positive on
the holdout when it is opened. If C1 fails on discovery, crypto price markets
are closed as a place for the plain rule and only C2 goes on.

> **C2 (the yardstick).** For each outcome and day, work out a model
> probability from the coin's price at that moment, the target, the time left
> and a forecast of how much the coin moves. Buy where the model's fair value
> exceeds the ask plus the fee by a margin, hold to resolution.

What is fixed now: the inputs (hourly prices from a public exchange feed; the
options market's volatility index where one exists, otherwise trailing
realised volatility; nothing dated after the signal), the entry (next
taker-buy print within 3 days, as everywhere), holding to resolution, the
clustering, and the bar. What is chosen on the discovery set and committed
before the holdout is opened: the form of the model, any recalibration of it,
the margin, and the price and time limits.

**Bar for C2.** On the holdout: positive with |t| ≥ 3, and a higher return per
trade than C1's band rule on the same holdout. A model that cannot beat a
price band is not worth its complexity.

### Analysis without a test: position size

For the rule that is already confirmed, the account simulation is repeated at
position sizes from 2% to 10% of the bankroll, with and without the per-story
cap, to show what larger positions would have earned and what they would have
risked. This chooses nothing; position size is the account owner's decision.

## 5. Track A: what happened, and what is fixed next

*Written at 18:10 UTC on 10 November, after track A was run on the first
round's panel and before any tape of a sports or crypto market had been read.*

**A1 as written.** 45 trades in 41 events, none lost, +5.88% a trade; the
control (the same band, not quiet) made +1.75% on 1,485 trades with 82 losers;
the gap is 4.1 points (t = 6.2). That meets the bar as I wrote it, and the bar
was badly written: with no losing trade the t-statistic measures only how much
the prices paid varied, so a t of 36 means nothing. The honest test of 45
trades with no loser is a count. If quiet favourites lost as often as the
others in the band (5.5%), 41 separate events would all win about one time in
ten. **A1 on its own is not established.**

**What the wider cuts show** (listed in advance as "reported alongside", so
they are evidence but not the test):

| Cut | Markets | Lost | Return a trade |
|---|---:|---:|---:|
| 90–95¢, range of 3¢ or less over **7** days, bought at the next print | 171 trades | 0 | +6.2% |
| 90–95¢, the same, every such signal bought at that day's own price, first day per market | 196 | 1 | +5.7% (t 10.4) |
| 90–95¢, everything else in the band, same way | 1,560 | 90 (5.8%) | +1.5% (t 2.3) |
| 95–98¢, range of 3¢ or less over 14 days, same way | 415 | 3 (0.7%) | +2.2% (t 5.1) |
| 95–98¢, everything else in the band, same way | 1,818 | 37 (2.0%) | +1.5% (t 4.1) |

One loser in 196 markets, against a rate of 5.8% for the rest of the band,
would happen by chance less than once in a thousand tries even if only half
of those markets were truly separate bets. Counting every day a contract
spends in the band, the loss rate rises steadily with how much the price has
moved in the last two weeks, in both bands; in the 95–98¢ band the contracts
that moved more than 15¢ in two weeks earn nothing (+0.7%, t 0.9). Most of the
first round's edge sits in contracts that have gone quiet.

The second row matters because of a flaw the first round found in its own
method: a backtest that waits for a later print never buys a contract whose
price collapses in between. Buying at the signal day's own price removes that
help, and the result stands.

This is still a pattern found by looking, in data that has been looked at
before. It becomes a finding only if it repeats where nothing has been
looked at.

### The rule to be replicated, fixed now

An outcome is **quiet** if the highest and lowest prices it traded at over
the last 7 days are 3¢ or less apart, and its market was already in the panel
7 days ago.

> **Q.** When an outcome's ask is above 90¢ and at most 98¢, its scheduled end
> is more than 3 and at most 60 days away, and it is quiet, buy it at the first
> taker-buy print on a later day, within 3 days, if that print is above 90¢
> and at most 98.5¢. Pay today's fee for the category. Hold to resolution. One
> trade per market, on the first day it qualifies.

The control is the same band, horizon and entry on the first day an outcome
is in the band and not quiet.

### Where it is replicated

Two universes whose tapes have never been read.

**QS: sports markets that are not single games.** Season-long, tournament and
similar questions: resolved, 100,000 shares or more, a life of 14 days or
more, no game start time. 3,182 markets, most of them legs of "who will win"
events, so legs and stand-alone markets are both traded and reported
separately. Sports fee rate 0.05. Clustered by event.

**QC: crypto price markets.** As defined for track C, excluding legs of
multi-outcome events. Fee rate 0.07, clustered by the week of the scheduled
end. Run on the discovery set now and on the holdout when it is opened. Daily
"above" markets live only a week and cannot meet the 7-day condition, so this
is in practice a test on the monthly and longer markets.

**Bar, for each universe.** Q earns a positive return per trade with |t| ≥ 3;
it beats its control with |t| ≥ 2 on the difference; and, because a
t-statistic fails when almost nothing loses, the number of separate clusters
with a losing Q trade is below what the control's loss rate would produce,
with a one-sided exact binomial p under 0.01.

Also reported, fixed now: the same rule with the scheduled end more than 60
and at most 365 days away (**Q-long**), in both universes. The first round's
panel suggests the effect continues there with a lower loss rate and a longer
wait.

If Q fails in both universes it is not traded with real money on the strength
of the first round's panel alone. A paper account can still test it forward.

## 6. Track C: crypto price markets

*Discovery set only: 6,429 markets scheduled to end before 1 June 2026. The
holdout (1,738 markets) has not been read.*

**C1, the confirmed rule where it had never been tried: not repeated.** 511
trades, 10 lost, +1.30% a trade, but t = 1.07 (`run_crypto_price.py`,
`cp_rules_discovery.csv`). The return is the size it was in the first round.
What differs is how the losses arrive: all ten fell in five weeks, because one
move in Bitcoin settles every target that week. Thirty-eight weeks with five
bad ones cannot tell +1.3% from zero. The long-shot control lost 56% a trade
(t = −3.1), so the crowd overpays for long shots here too; the favourites'
side of it is too small to see through the bunching.

**QC, quiet favourites in crypto: nothing to judge.** 47 trades, none lost.
Most of these markets live a week and cannot meet a 7-day condition.

**C2, the outside yardstick: it does not find mispriced contracts.**
(`run_crypto_yardstick.py`, `cy_*.csv`.) The model is a driftless lognormal
walk fed with the coin's last hourly price and the options market's
volatility index.

- *It is a fair yardstick.* Across the middle of the range, things happened
  about as often as the model said.
- *When it disagrees with the price somebody paid, the price is right.* Over
  2.04 million taker prints with 3 to 60 days to run, profit per share against
  the model's edge has a slope of +0.08 (t = 0.19). A slope of 1 would mean
  the model's edge is real; 0 means it is noise. Nothing at 1–3 days or in the
  last day either.
- *My first pass said the opposite, and was wrong.* Using each day's last
  quoted price beside the coin's price at the end of that day gave a slope of
  +1.35 (t = 4.5), which would have been the best result of the project. The
  quote can be hours older than the coin price next to it, so the model was
  being credited with knowing where the coin went afterwards. The table is
  kept in the output under the word ARTEFACT.
- *Distance does not make a tail safe.* Near-certain "No" contracts on price
  barriers at least three expected moves away: 249 trades, 4 lost, +0.55% a
  trade (t = 0.3). The four were Bitcoin, Ether, Solana and XRP "dip" markets
  in the same week of January 2026, each bought at 98¢. One crash week erased
  most of two years of 2% gains. The lognormal walk calls that move a
  once-in-decades event; in crypto it is not.
- *Upside targets looked overpriced and downside targets underpriced*: "No" on
  "reach" markets 2.5 moves away lost 0 of 200, "No" on "dip" markets 5 of
  199. That cannot be told apart from the direction prices went. Bitcoin fell
  by a fifth in each of the two quarters that hold most of these trades, and
  quarter by quarter the losers are on whichever side the coin moved
  (`cy_by_quarter.csv`).

**Verdict.** Crypto price markets are closed for this strategy. Selling their
tails is selling crash insurance, the premium is about what the first round
found elsewhere, and the claims arrive together. No C2 rule came out of the
discovery set, so nothing is committed for the holdout and it stays unread,
which keeps it available for a future idea. The bar for C2 was written for a
rule; there is no rule to hold to it.

What the track was worth: an untouched universe in which the favourite side of
the bias did not repeat cleanly, which is a reason for caution about the first
round's result everywhere that losses can bunch; and a second example, after
the first round's biased sample, of a strong result made out of nothing by a
timing mismatch.

## 7. The replication of the quiet rule in sports: failed

*`run_quiet_replication.py sports_other`, `qs_*.csv`. 3,182 season-long and tournament
markets, none of them read before.*

| | Trades | Events | Lost | Return a trade | t |
|---|---:|---:|---:|---:|---:|
| **Q**, quiet, 3–60 days | 265 | 89 | 11 (4.2%) | −0.27% | −0.2 |
| Control, not quiet | 658 | 227 | 29 (4.4%) | +0.35% | 0.4 |
| **Q-long**, quiet, 60–365 days | 385 | 78 | 17 (4.4%) | −0.56% | −0.7 |
| Control, not quiet | 449 | 115 | 20 (4.5%) | +0.17% | 0.2 |

Every part of the bar failed. Quiet favourites lost exactly as often as the
others, and neither group earned anything: at an average cost of 95–96¢, a
loss rate of 4.2–4.4% is a fair price. The first round's own rule does nothing
here either (95–99¢, 752 trades, +0.38%, t = 0.8).

Two things follow.

**There is no favourite–longshot edge in sports, in games or in season-long
markets.** The first round found that for games; this extends it. Whatever
the crowd gets wrong in news markets, it does not get wrong where outcomes
are settled on a field and professionals price them.

**"Quiet" is not a general property of prices that makes a favourite safe.**
A team's title odds sit still between matches and then move on a result. The
idea behind the quiet rule was that a still price means a story has gone
dormant, and in a competition with a fixture list it means nothing of the
kind. I registered sports as a replication because it was the untouched data
I had, and the honest reading is that the rule failed the test I set, in a
place where the reasoning behind it does not apply. That is weaker than
failing where it should work and it is not a pass.

So after two universes the quiet rule stands like this: a large effect on the
first round's news markets, found by looking; nothing to judge in crypto;
and a clear failure in sports. By the rule I wrote before testing, it is not
to be traded with real money on that evidence.

## 8. Where the quiet rule should be tested instead

*Written at 18:33 UTC on 10 November, before any of the data below was
downloaded.*

The right replication is in markets of the same kind as the ones the effect
was found in, that have never been in the data. There is such a set. Every
market in both rounds so far had traded at least 100,000 shares. Polymarket
has many resolved news markets that never got that far.

**QT: thinner news markets.** Resolved Polymarket markets outside sports and
crypto, with a life of two days or more, that traded at least 20,000 and
fewer than 100,000 shares. A market is used only once it has traded 20,000
shares. Everything else is rule Q exactly as fixed in section 5: ask above 90¢
and at most 98¢, scheduled end 3 to 60 days away, traded range of 3¢ or less
over the last 7 days in a market already in the panel 7 days ago, bought at
the next taker-buy print within 3 days if still in range, today's fee, held,
one per market. Stand-alone markets and legs are both traded and reported
separately. The control is the same band on the first day not quiet. Clustered
by event.

**Bar.** The same three parts as before: Q positive with |t| ≥ 3; above its
control with |t| ≥ 2; and fewer events with a losing Q trade than the
control's loss rate would produce (one-sided exact p under 0.01).

Reported alongside: the first round's main rule (95–98¢, stand-alone) on the
same markets, as a replication of the first round in thinner markets; Q
within the 90–95¢ band alone, where the effect was largest; and the main rule
split by whether the outcome's traded range over the last 14 days was above
15¢, because on the first round's panel the contracts that had moved that much
earned nothing (added at 18:36 UTC, while the list of thinner markets was
still downloading and before any of their tapes existed).

If QT passes, the quiet rule has repeated once in the right kind of market
and failed once in the wrong kind, and it earns a paper account and a place
in the forward test. If it fails, it is dropped.

**A second, smoother test on the same markets, added at 18:45 UTC while their
tapes were still downloading and before any had been read.** A rule with a
cut-off at 3¢ throws away most of the data, and a cut-off chosen after looking
tends to look sharper than it is. So I also fitted the plainest possible model
on the first round's panel: one row a week for every favourite priced 88–99¢
with 3 to 180 days to run (14,896 rows, 3,705 markets, 2.5% of them lost), and
a logistic regression of losing on the price paid and on how far the price had
ranged over the last 7 days:

> logit P(loses) = 0.311 − 1.046 × logit(price) + 0.295 × log(range + 0.005)

The range term has t = 3.1 (clustered by event) and is the only thing that
improved the fit out of sample; a 28-day range, days to the end, whether the
market is a leg, its category, its recent dollar volume and its price change
over the week all added nothing or made it worse. The model says a favourite
that has ranged 15¢ in a week is about twice as likely to lose as one at the
same price that has ranged 1¢: a real difference and a much smaller one than
"one loser in 196" suggests. That gap is itself a warning that the 3¢ cut-off
flatters the effect.

> **QT-smooth.** On the thinner markets, the same weekly rows and the same
> regression. The bar is a positive coefficient on the range with t ≥ 2,
> clustered by event.

Reported with it: how often favourites lost in each third of the frozen
model's predicted loss, among those priced 90–98.5¢ with 3 to 60 days to run.
If QT-smooth passes, the frozen model replaces the first round's calibration
line for ranking candidates, whatever happens to the 3¢ rule.
