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
