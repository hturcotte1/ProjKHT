# 02 — Research findings

*Written 2026-11-10 after the tests fixed in `01_thinking_session.md` were
run. Every number here comes from a table in `reports/research/`; the script
that produced each one is named alongside it.*

## The short version

1. **The original idea, taken literally, does not make money.** Buying a
   contract because the crowd's price is expected to move, and selling it a
   few days later, lost about 6–7% per trade in every form tested. Prices on
   Polymarket move almost unpredictably from day to day, and a round trip
   costs about 6% of the stake at mid-range prices (2.5% where there is no
   fee). Sports prices before a game do not drift the way the Seahawks
   example imagines. Following wallets with a good record does not help
   either: their edge is half a cent a share and it is in the price within a
   minute.
2. **The crowd does have a standing blind spot.** In non-sports markets,
   cheap contracts are badly overpriced: one bought for under 10¢ loses about
   60% of the stake on average. The mirror image is that near-certain
   contracts are slightly too cheap.
3. **The rule I committed to in advance failed its test; one of its
   pre-registered variants passed.** Buying 90–97¢ contracts and holding them:
   +0.88% per trade on unseen data, t = 1.7 — not enough. Buying 95–99¢
   contracts: +0.96% per trade, t = 3.6 over 2,822 trades. The longshot
   control lost 37% per trade, as predicted.
4. **What the paper account trades** is that variant, narrowed to where the
   evidence is: 95–98¢ contracts in stand-alone yes/no markets, bought a day
   after they are first seen in that range, held to resolution. About 98 in
   100 such trades gain 3–4%; about 2 in 100 lose everything staked.
5. **It is a small edge, and it does not scale far.** Run as a $1,000 account
   at $20 a position, the backtest made roughly 7–9% a year with a third of
   the money in use. Judged by what actually traded at those prices, and
   assuming a tenth of it could be bought, a larger account would make about
   6–7% a year up to $50,000–100,000 and no more than about $20,000 a year at
   any size (section 7). It is real enough to keep testing and too thin to be
   excited about.
6. **Sports: nothing.** Both sports rules failed. Pre-game sports prices on
   Polymarket are well calibrated.

## 1. The data

All from Polymarket's public APIs; no account was needed.

| | |
|---|---|
| Resolved markets with at least 100,000 shares traded | 114,972 |
| Trade-by-trade tapes, non-sports and non-crypto markets | 16,335 markets, 59.3 million trades, Nov 2023 – Nov 2026 |
| Trade-by-trade tapes, sports game-winner markets | 32,410 games, 21.2 million pre-game trades |
| Quoted price histories (12-hour bars; 3-hour bars from July 2026) | 69,053 markets |

Two decisions about how to use it mattered more than any model.

**Which markets count.** A market is used only from the moment it has already
traded 100,000 shares. That is something a trader could have known at the
time. Section 2 shows what happens without this rule.

**What price counts.** Polymarket keeps no history of order books, but every
trade on the tape records which side was the taker. The last taker *buy* of an
outcome printed at about its ask, the last taker *sell* at about its bid. So
the backtests buy at a price somebody demonstrably paid, one day after the
signal, and pay today's fee for the market's category
(`src/kht/research/quotes.py`, `src/kht/backtest/harvest.py`).

## 2. The sample that lied

My first pass selected markets by their *total* volume and used quoted
mid-prices. It produced two confident findings.

| First pass (`reports/research/first_pass_biased/`) | Result | |
|---|---|---|
| Sports favourites are overpriced | calibration slope 0.83 | t = −6.1 |
| Yesterday's move partly reverses | slope −0.03 to −0.08 | t = −5 to −8 |

Both were wrong, for different reasons.

Total volume includes trading *during* the game, and a game with a comeback or
an upset trades far more. Selecting on it quietly over-samples upsets. In the
first games I checked, the slope was 0.52 where little had traded before
kick-off and 1.17 where a lot had. With the no-hindsight rule the sports slope
is 0.97 (t = −0.8, 4,950 games): no bias at all.

The reversal mostly lives in quoted mids of thin markets, where a quote being
pulled and replaced looks like a move and a reversal. On prices people traded
at, it shrinks to a few percent of the move, and as an actual trade it loses
money (section 3).

Two further errors were caught the same way, before they could reach a
conclusion: forward returns that dropped markets resolving inside the
look-ahead window, and a backtester that preferred one side of a market over
the other regardless of which signalled first, which skipped losing trades in
markets that later flipped. Both now have regression tests.

## 3. Can a shift in perception be traded?

### 3.1 Do prices trend or revert?

Slope of the next change on the past change, daily prices rebuilt from the
tape, 16,213 markets (`x_a1_momentum_daily.csv`):

| Past ↓ / next → | 1 day | 3 days | 7 days |
|---|---:|---:|---:|
| 1 day | −0.013 (t −1.6) | −0.029 (t −2.0) | −0.042 (t −2.4) |
| 3 days | −0.014 (t −2.2) | −0.036 (t −2.7) | −0.048 (t −2.9) |
| 7 days | −0.014 (t −3.2) | −0.031 (t −3.2) | −0.030 (t −2.0) |

There is a faint tendency to give a little back: after a 10¢ move, about
0.1–0.5¢ over the following week. It is weaker in the later half of the sample
(no |t| above 1.6). On 3-hour quoted prices since July 2026 there is nothing at
any horizon (all |t| below 1.7, `x_a2b_momentum_3h.csv`). After large one-day
moves the give-back is larger in cents but never significant: 0.4¢ the next
day after a move of 15¢ or more (t −1.5). There is no weekday pattern.

### 3.2 As actual trades

Buy at the ask the day after the move, sell at the bid a few days later, fees
both ways (`x_a3_roundtrip_trades.csv`):

![Round-trip trades](../reports/figures/roundtrip_perception_trades.png)

| Signal | Trades | Average return | t |
|---|---:|---:|---:|
| Fell 10¢ or more, hold 1 day | 5,674 | −6.7% | −5.6 |
| Rose 10¢ or more, hold 1 day | 5,798 | −7.0% | −6.5 |
| Fell 20¢ or more, hold 3 days | 1,718 | −6.7% | −2.1 |
| Rose 20¢ or more, hold 3 days | 1,723 | −8.0% | −4.4 |
| No signal at all, hold 3 days | 12,364 | −6.5% | −16.1 |

Every signal does about as badly as no signal. The loss *is* the cost of the
round trip. In geopolitics markets, which carry no fee, the cost falls to 2.5%
and buying after a 20¢ drop roughly breaks even (−0.4%, 443 trades).

That left one obvious follow-up: the same trades entered with a resting bid
instead of paying the spread. The bid is left at the signal day's closing bid
and counts as filled only if a later sale prints through it, the fill rule of
R1m; the exit is unchanged. Same grid, nothing tuned, exploratory
(`x_a3c_roundtrip_resting_bid.csv`):

| Signal | Bought at the ask | With a resting bid | t |
|---|---:|---:|---:|
| Fell 10¢ or more, hold 1 day | −6.7% | −4.0% | −2.5 |
| Rose 10¢ or more, hold 1 day | −7.0% | −3.9% | −3.1 |
| Fell 20¢ or more, hold 3 days | −6.7% | −4.3% | −1.1 |
| Rose 20¢ or more, hold 3 days | −8.0% | −4.6% | −2.1 |
| No signal at all, hold 3 days | −6.5% | −4.3% | −6.1 |
| Fee-free markets: fell 20¢ or more, hold 3 days | −1.7% | −0.4% | −0.0 |
| Fee-free markets: no signal, hold 3 days | −2.5% | −0.2% | −0.1 |

A resting bid saves about two points and changes nothing else. Every signal
still does as badly as no signal; the fee-free cells sit at zero beside their
own no-signal benchmark; and where a cell is positive in one half of the
sample it is negative in the other. A bid that fills only when the price keeps
falling is not a cheap way to buy a dip.

### 3.3 Sports before the game

15,112 games in the no-hindsight sample (`x_b*.csv`, `s1_rules.csv`).

| Question | Answer |
|---|---|
| Does the favourite get bid up as the game approaches? | No. In leagues with reliable start times it drifts *down* by 0.1–0.2¢ over the last 12 hours (t −3 to −5). Late money leans slightly to the underdog; the spread is 1¢. |
| Does an early move continue? | Barely: 5–6% of the move from three days out to one day out carries on (t 1.7–2.0). |
| Do results go further than the closing price in the direction of the move? | No (all \|t\| below 1.6). The close has absorbed the move. |
| Does the public's share of small tickets predict the move or the result? | The move by at most 0.4¢ from one extreme to the other (t 2.4), and not at all in leagues with reliable start times. The result, no. |
| Do large orders? | No (all \|t\| below 2). |
| **S1**: buy 75–95¢ favourites six hours out | −1.7% per trade, t = −1.2, 1,083 trades. Not confirmed. |
| **S2**: buy the side that rose 3¢ or more | +0.04%, t = 0.0, 2,003 trades. Not confirmed. Fading it loses 4.7%. |

Sports is where the most professional money is, and it shows.

### 3.4 Following wallets that were right before

Every tape row names the wallet that took the trade, so the cleanest form of
the thesis can be tested directly: if some wallets are reliably better
informed, their buying is a shift in perception you can see happening. The
plan and the bar were written into `run_wallet_skill.py` and committed before
it was run.

Each quarter from late 2024, wallets with at least 50 past trades in at least
10 resolved markets were ranked on how far their purchases had beaten a
calibration line fitted to the same past (so that simply buying favourites
does not count as skill), and cut into fifths. The test is what they did in
the *following* quarter: 1.84 million trades, at prices from 5¢ to 95¢, from
up to 38,900 ranked wallets, with a follower buying the same outcome at the
next print at least a minute later and paying today's fee
(`w_wallet_skill_fifths.csv`).

| Past-skill fifth | Wallet's own edge per share | t | Price a minute later | Follower, all markets | Follower, fee-free markets |
|---|---:|---:|---:|---:|---:|
| Bottom | +0.04¢ | 0.2 | +0.17¢ | −0.57¢ (t −3.5) | −0.06¢ (t −0.2) |
| 2 | −0.03¢ | −0.2 | +0.14¢ | −0.57¢ (t −4.2) | −0.36¢ (t −1.5) |
| 3 | +0.03¢ | 0.2 | +0.14¢ | −0.52¢ (t −3.6) | −0.25¢ (t −1.0) |
| 4 | +0.30¢ | 2.6 | +0.19¢ | −0.31¢ (t −2.7) | −0.06¢ (t −0.4) |
| Top | +0.51¢ | 4.4 | +0.40¢ | −0.30¢ (t −2.5) | +0.14¢ (t 0.9) |

By the measure fixed in advance, the follower's return per trade, the top
fifth lost 4.0% (t −3.0) and beat the bottom fifth by 1.2 points (t 1.75),
against a bar of a positive return and a gap, each with |t| ≥ 3. **Not a
lead.** That return is a ratio, which the cheap contracts in the sample
dominate, so the table gives the same trades in cents per share and splits
them by fee; those columns were added after the planned ones had been read
and are labelled as unplanned in the output.

What it shows is the thesis in miniature. Skill is real and it persists: the
top fifth go on beating their own purchase price by half a cent a share. And
the price moves 0.4¢ their way by the very next print, two to three times
what it moves after anyone else's trade. Four fifths of the edge has gone
before a follower can act, and the fee takes the rest. Informed buying does
shift the price. The shift is over within a minute.

### Verdict on the thesis as stated

Short-term changes in the crowd's price are close to unpredictable from
anything in the price or the order flow, and where a pattern exists it is ten
to fifty times smaller than the cost of acting on it. "Buy at 70 because it
will be 80 on Tuesday" needs information the market does not already have,
and the wallets that have it are in and priced within a minute.

## 4. What the crowd gets predictably wrong

What a contract went on to earn, by the price paid for it, on the holdout
(`c1_calibration_by_price.csv`):

![Calibration](../reports/figures/calibration_holdout.png)

| Price paid | Won | Profit per share after fees | t |
|---|---:|---:|---:|
| 3–5¢ | 1.6% | −2.5¢ (−64%) | −7.3 |
| 5–10¢ | 3.0% | −4.2¢ (−61%) | −9.8 |
| 10–20¢ | 9.6% | −5.0¢ (−37%) | −4.9 |
| 40–60¢ | about as priced | −1.7 to −2.9¢ | n.s. |
| 90–95¢ | 96.4% | +3.1¢ | 6.5 |
| 95–97¢ | 98.1% | +1.8¢ | 5.2 |
| 97–99¢ | 99.0% | +0.8¢ | 3.9 |

*(One row per market per day, so long-lived markets weigh more; the rule tests
below count each market once.)*

This is the favourite–longshot bias: people overpay for a small chance of a
big win, and nobody is paid enough to push a dull 96¢ contract up to the 98¢
it is worth while their money sits locked up. The calibration slope is 1.19 on
the holdout (t = 3.5 against 1) and 1.31 on the newer sample (t = 3.8), in line
with the published estimates quoted in the thinking-session document.

It is **not** a preference for "Yes" over "No": at the same price the two do
equally well or badly (`x_a4_yes_no.csv`). And it is **not** present in sports.

## 5. The pre-registered test

Rules, variants and controls were fixed in `01_thinking_session.md` (section
8, with commit timestamps) after seeing only markets that closed from June
2026. The holdout is every market scheduled to end before May 2026: 11,372
markets, untouched until the test (`c2_rules.csv`).

| Rule | Trades | Events | Won | Return per trade | t | Verdict |
|---|---:|---:|---:|---:|---:|---|
| **R1** buy 90–97¢, 3–60 days out, hold | 2,319 | 1,415 | 94.8% | +0.88% | 1.70 | **Not confirmed** |
| R1a same, 7–60 days | 1,799 | 1,193 | 94.8% | +0.97% | 1.64 | No |
| R1b same, sell 3 days before the end | 1,799 | 1,193 | 86.9% | +0.34% | 0.70 | No |
| R1c 80–97¢ | 2,876 | 1,645 | 91.1% | +1.20% | 1.90 | No |
| **R1d 95–99¢** | 2,822 | 1,652 | 98.2% | **+0.96%** | **3.62** | **Confirmed** |
| R2 R1, "No" side of stand-alone markets | 1,122 | 887 | 95.3% | +1.57% | 2.19 | No |
| R3 R2, "by/before" questions | 693 | 543 | 94.8% | +1.38% | 1.41 | No |
| R1m R1 with a resting bid | 2,186 | 1,340 | 94.2% | +1.54% | 2.68 | No (close) |
| Control: longshots 3–10¢ | 2,378 | 1,448 | 4.5% | −37.0% | −5.77 | Negative, as predicted |
| Control: coin flips 40–60¢ | 764 | 588 | 45.8% | −7.5% | −2.13 | Negative |

The bar was |t| ≥ 3 with standard errors clustered by event. Ten rules were
tried in all (these eight and the two sports rules in section 3), and a t of
3.62 survives a correction for that (p ≈ 0.0003 × 10 = 0.003). The primary
rule did not clear the bar and I am not going to pretend it did: the edge is
not spread across 90–97¢ as I guessed, it sits at the top.

On the newer sample that shaped the rules, R1d returned +1.28% (t = 2.74,
988 trades) and R1 +1.45% (t = 1.74).

**One departure from the plan as written.** The pre-registration describes the
holdout as "markets that closed before 2026-06-08". The test script, committed
six minutes later and forty minutes before the holdout was opened, splits on
the *scheduled* end date instead (before May 2026), because a split on the
realised close date conditions on the outcome: a "by December" market that
closes in May is one where the thing happened. Every verdict is the same under
the wording as written, with a thinner margin for the rule that passed: R1d
+0.84%, t = 3.10 (3,041 trades); R1 +0.85%, t = 1.70; long-shot control
−33.5%, t = −5.1 (`c5_holdout_definitions.csv`). No R1d holdout trade, and at
most two trades of any other rule, come from a market in the slice examined
beforehand.

## 6. Checks on the rule that passed

All on the holdout (`c3_r1d_*`, `c4_r1d_*`).

| Check | Result |
|---|---|
| By year | 2024 +1.5%, 2025 +0.8%, 2026 +0.9%. Positive each year. |
| By price | 95–96¢ +2.4% (t 3.5); 96–97¢ +1.1%; 97–98¢ +1.0%; **98–99.5¢ −0.1%** |
| Without the 50 largest events | +0.96%, t = 3.2 |
| One trade per event only | +1.09%, t = 3.3 |
| Bootstrap over events | 95% interval +0.43% to +1.48%; 99% interval +0.23% to +1.61% |
| By category | geopolitics +1.6% (t 3.2), politics +0.6%, economics +1.3%, culture +1.0%, finance +0.3% |
| Stand-alone market vs leg of a multi-outcome event | **+1.36% (t 3.9)** vs +0.50% (t 1.2) |
| Losses | 52 of 2,822 trades lost everything (1.84%); never more than 2 in one event or 4 in one week |
| Markets left out for lack of a result | 6 of 16,555 closed markets (2021 price-range markets and one superseded duplicate). Asked directly on 10 November 2026, Polymarket lists one market of this size scheduled to end before May 2026 as still open, a five-minute crypto market outside the universe, so nothing unresolved is hiding in the holdout |

**One check cut the other way.** The backtest buys at the first trade print on
the days *after* the signal, and only if the price is still in range. Buying
at the signal day's own last price instead, for every signal, returns +0.63%
(t = 2.2). The 72 signals that never offered an in-range price afterwards lost
11% on average: they were contracts already falling out of the range. The
one-day wait is doing real work, so the live rule has the same wait built in
(a contract must also have been in range 18 hours earlier, checked against
Polymarket's own price history). Where that cannot be reproduced, expect
closer to +0.6% than +1%.

## 7. What the paper accounts trade

Two changes were made to R1d **after** the holdout was opened. They follow the
breakdowns above and hold on both samples, but they are choices made with the
answer in view and carry less weight than the pre-registered result.

- **95–98¢ instead of 95–99¢.** The top cent returned nothing after fees.
- **Stand-alone markets only.** In legs of multi-outcome events other traders
  can lock in arbitrage across the legs, and the edge is half the size.

The exact rules as configured, both samples (`d_deployed_rules.csv`):

| | Holdout | | Newer sample | |
|---|---:|---:|---:|---:|
| | return / trade | t | return / trade | t |
| **Main account**: 95–98¢, stand-alone, buy at the ask | +1.52% (1,263 trades) | 3.68 | +1.91% (573) | 3.23 |
| …same band, multi-outcome legs (not traded) | +1.01% | 1.97 | +1.27% | 1.38 |
| …same rule with a resting bid | +1.99% | 4.09 | +2.48% | 3.72 |
| **Experimental account**: 90–98¢, stand-alone, resting bid | +2.02% (1,404) | 3.13 | +2.89% (633) | 3.38 |

A resting bid earns the spread instead of paying it and pays no fee, which on
an edge this thin is most of the difference. It fell just short of the bar as
pre-registered (R1m, t = 2.68), so it gets its own paper account rather than a
place in the main one.

Not counted anywhere: Polymarket's maker rebate (a quarter of the taker fees
collected in most categories, nothing in fee-free geopolitics), its liquidity
rewards, and its taker rebate tiers. At 96¢ the fee is about 0.15¢ a share, so
a share of it is worth a few hundredths of a percent, and the first taker tier
needs roughly $40,000 a month of fee-paying volume at these prices.

### As an account

![Main rule as an account](../reports/figures/main_rule_equity.png)

$1,000, $20 a position, one position per event, $80 per theme, at most 80%
invested (`d_deployed_accounts.csv`):

| | Trades taken | Total | Per year | Worst drawdown | Money in use |
|---|---:|---:|---:|---:|---:|
| Main rule, holdout (2.5 years) | 534 | +18.4% | 7.0% | −3.8% | 30% |
| Main rule, all three years | 699 | +29.6% | 9.1% | −3.8% | 32% |
| Experimental rule, holdout | 555 | +11.5% | 4.2% | −6.4% | 32% |

Read these as a range, not a forecast. The pre-registered R1d run the same way
made between 2.7% and 8.1% a year depending only on which caps were applied,
because the account takes a third of the signals and which third matters. The
steps in the chart are month-ends, when many "by the 30th" markets resolve at
once. The right-hand part of the chart also omits positions in markets that
have not resolved yet.

**In dollars:** each win is about 70¢ on a $20 position, each loss is $20.
A year is roughly 220–240 trades, of which about four lose (the simulated
account had nine losers in three years). Expect something like +$60 to +$90 on
$1,000 in an average year, and a losing year whenever losses bunch.

**How the losses arrived.** In three years the pre-registered rule lost 69
trades in 65 separate events, never more than two in one event. Its worst week
held four losing events, in unrelated markets, and its worst thirty days eight.
That is no more bunching than chance produces. Drawing the same number of loss
days at random, in proportion to how many events were held each day, gives a
worst week of four and a worst thirty days of ten at the median (p = 0.91 and
0.92; spread across calendar months, p = 0.29; `check_loss_bunching.py`,
`c6_*.csv`). Scattered is not the same as painless: the average trade lost
money in 12 of the 36 calendar months in which any trade ended, four in a row
at worst, which is what a 1.8% loss rate looks like when a month holds
anything from a handful to a few hundred trades.

Deadlines are not where the risk is. The ten busiest exit days hold 30% of all
trades and three of the 69 losers. A contract that survives to its deadline
nearly always pays; the losses come when the event happens first. What three
years cannot show is one shock that flips many near-certain contracts at once.
The per-story cap in the trading system is there for that case, and the
history gives no way to size it.

**Buying late.** The backtest buys a contract the first time it qualifies. An
account that is switched on today, or comes back after days without a cycle,
finds contracts that have been sitting in the band for days or weeks and buys
those. The paper account's first purchases are of that kind, and so is most of
the forward-test log so far. On the same data, buying late did no worse.
Buying the first time a contract qualifies made +1.64% a trade (1,836 trades,
both samples). Buying whatever qualified on a switch-on date, tried on 154
dates a week apart, made +1.72% (2,046 trades in 1,129 markets, t = 4.7). On
the holdout alone the two are +1.52% and +1.22%, a gap well inside the noise
(`check_late_entry.py`, `c7_*.csv`; exploratory). Contracts that had already
been in the band for twenty days or more lost less often, 3 of 435 against 33
of 1,836. The pre-registered rule points the same way on the holdout and only
weakly on the newer sample, so this is a lead to watch in the forward-test log
and not a result.

One day's purchases are a small sample, though. Of the 76 switch-on dates on
which ten or more contracts were bought, 56 had no losing trade and made about
3% a trade. On 19 the day's purchases lost money overall, because one loser
among twenty cancels the rest. The paper account's first positions are one
such day.

### How much money it could take

The backtest buys $20 at a time, which says nothing about a larger account.
Polymarket publishes no historical order books, so the nearest thing to "how
much was for sale" is how much takers actually bought. For each of the main
rule's 1,836 trades (both samples) I added up the dollars takers paid at
in-range prices on the entry day and the two days after it, limited a position
to a share of that flow, and priced it at the volume-weighted average of those
prints instead of the first one (`run_capacity.py`, `k_capacity_*.csv`). This
is exploratory, and it rests on an assumption history cannot check: that
taking a tenth of what others bought would not have moved the price.

**Flow per market is small and very uneven.** The median market saw $5,500
bought in range over the three days; a tenth of them saw under $230 and a
tenth over $79,000. Eighteen markets, 1% of them, hold 36% of all the dollars.

**The price is a little worse at size.** The average fill moves from 96.5¢ to
96.9¢, and on the holdout the result slips just under the bar:

| Entry priced at | Holdout | t | All three years | t |
|---|---:|---:|---:|---:|
| The first print, as in the backtest | +1.52% | 3.68 | +1.64% | 4.84 |
| The three-day average | +1.20% | 2.91 | +1.29% | 3.84 |

The edge is not confined to thin markets: the quarter with the most flow
returned +1.96% (t 3.3) at the three-day average, the other three quarters
about +1.0–1.2% each.

**As accounts.** 2% of the bankroll per position, one position per event, 8%
per theme, at most 80% invested, a position at most a tenth of the in-range
flow, all three years:

| Bankroll | Average position | Positions cut by flow | Per year | Profit per year | Worst drawdown |
|---:|---:|---:|---:|---:|---:|
| $1,000 | $19 | 9% | 6.7% | $71 | −4.5% |
| $10,000 | $153 | 40% | 6.2% | $660 | −4.7% |
| $50,000 | $503 | 72% | 7.0% | $3,700 | −2.0% |
| $100,000 | $788 | 81% | 6.3% | $6,700 | −1.7% |
| $250,000 | $1,255 | 90% | 4.1% | $10,600 | −1.8% |

At a twentieth of the flow instead of a tenth, the return fades sooner (4.6% at
$100,000, 2.9% at $250,000); at a quarter it holds to $250,000 (6.3%). The
$1,000 row is lower than the 9.1% above mainly because of the worse entry price.

**The ceiling is about $20,000 a year, and only with small positions.** Every
trade taken at a tenth of its flow, no account limits at all, with a ceiling on
the size of a position:

| Largest position | Bought per year | Return on it | Profit per year |
|---:|---:|---:|---:|
| $500 | $0.2M | +1.44% | $3,000 |
| $2,000 | $0.5M | +1.51% | $8,200 |
| $5,000 | $0.9M | +1.54% | $13,700 |
| $10,000 | $1.2M | +1.48% | $18,000 |
| $25,000 | $1.7M | +1.32% | $22,400 |
| $100,000 | $2.3M | +0.03% | $600 |
| No ceiling | $2.8M | −1.27% | −$35,100 |

The last two rows are the lesson. The dollars sit in a handful of very large
markets, and two of the twenty largest lost: "US x Iran permanent peace deal
by June 15, 2026?" ($2.5 million bought in range, the second largest of all)
and "Khamenei out as Supreme Leader of Iran by February 28?" ($0.7 million). A
position that follows the flow puts most of its money where one outcome
erases years of small wins. The rule scales only as many small positions.

So, if a tenth of the flow can be had: roughly $4,000–7,000 a year on
$50,000–100,000, about $10,000 on $250,000, and no more than about $20,000 a
year however much money is brought to it. Thirty-three losing trades in three
years cannot pin those figures down; the shape (flat, then fading, and
negative if concentrated) is the reliable part.
One liberty is taken: a position is sized from flow over the days *after* the
entry, which a real account could only match by buying a share of each day's
trading as it happens.

## 8. The model

`config/model.json` holds a calibration line fitted on 4,886 resolved trades,
`P(pays) = sigmoid(−0.27 + 1.19 × logit(ask))`, plus a small shift per segment
(category × stand-alone or multi-outcome), shrunk hard toward zero. A 96¢ ask
becomes an estimated 97.1%.

Refitted each quarter on resolved trades only and scored on the next quarter,
trades in its top quarter of predicted edge returned +1.25% against +0.17% in
the bottom quarter, but no step is significant (`m_walkforward_by_predicted_edge.csv`).
So it is used only to rank candidates when there are more than the account can
take, and to drop the few segments with no estimated edge. It is not evidence
of anything.

## 9. What could still be wrong

- **It has been true for three years, not thirty.** The effect is positive in
  each year but 2025 and 2026 are weaker than 2024.
- **Two parameters were chosen after the holdout was opened** (section 7).
- **Tail risk is the whole risk.** 98% of trades make 3%; 2% lose 100%. A
  backtest with 52 losses cannot say much about a week with ten. The theme and
  event caps exist for this, and the first live cycle showed why: it bought
  four positions tagged "Iran" before I widened the definition of a theme.
- **Fees are today's, behaviour is yesterday's.** Much of the history was
  traded when these markets had no fee. Fees are charged in the backtest, but
  other traders have also adapted to them.
- **Capital sits idle.** Two-thirds of the account is unused in the backtest.
  Larger positions would use more of it and concentrate the tail.
- **The estimate at size is weaker than the estimate at $20.** Priced the way
  a larger account would have to buy, the holdout return is +1.20% with
  t = 2.9, just under the bar, and the capacity figures assume a tenth of the
  flow could have been taken without moving the price (section 7).
- **"Days to the end" comes from Polymarket's own end-date field, and that
  field is noisy.** For about one in seven questions with a written deadline
  ("by June 30") it is more than a week away from the date in the question.
  The backtest and the live system read the same field, so they agree with
  each other, and nothing suggests the field is rewritten when a market
  closes (98% of dated markets that closed on schedule match their written
  date). I cannot check that it never changed while a market was open.
- **Resolution risk is not modelled** beyond counting split resolutions as
  half-payouts: disputes, delays and rule changes are assumed to look like the
  past.
- **Paper fills are not real fills.** The paper broker is strict, but it has
  never been reconciled against a real order.

## 10. What happens next

The paper accounts are set to run about every three hours and log every signal
they see, in the traded band and on either side of it, whether or not there is
money to take it (`kht shadow`). The first cycle alone logged 246 signals, 97
of them the kind the account trades, most of which resolve within two months,
so the log will say more by January than the paper account can in a year.
Nearly all of those first signals were contracts already sitting in their
band when the log began, which the backtest would have bought earlier. That
did not change the result in the history (see "Buying late" above), but it
means the log's first months are a test of the rule on a standing stock of
contracts, and only later a repeat of the backtest.

It will still not say much, and it is worth knowing why before reading it. A
signal in the traded band has to win 96.6% of the time to break even, and won
98.1% in the backtest. Those are one and a half points apart, and 200 signals
measure a win rate only to within about two points either way. Telling the
two apart takes roughly 1,000 resolved signals, which at the rate they arrive
is a year or so. An edge this thin cannot be confirmed quickly by anyone.

| After | If the traded band shows | Then |
|---|---|---|
| ~200 resolved signals (about January) | fewer than 95% winning | Something has changed. Stop. |
| ~200 resolved signals | 95% or more | Not a failure, and not yet a confirmation. Keep logging. |
| ~1,000 resolved signals (a year or so) | fewer than 97% winning | No edge worth the tail risk. Stop. |
| ~1,000 resolved signals | 97.5% or more | Consistent with the backtest, and something that would happen only about one time in fifteen if there were no edge at all. |
| Any time | the experimental account's fills are scarce or its losers bunch | Resting bids are being picked off. Drop it. |
| Any time | 4 or more losses in a week | Stop and read them before anything else. |

A small live test does not need to wait for the thousandth signal: its
purpose would be to check that real fills match paper fills, which a few
dozen trades can show, not to prove the edge.

**What was not tested.** Anything during a game, where prices move on the
score and the edge goes to whoever sees it first. Crypto price markets, left
out from the start because they carry the platform's highest fee and resolve
on an outside price that programs watch continuously. Outside signals such as
sportsbook lines. And reacting to informed wallets within seconds rather than
a minute. All four need a faster engine than this one and compete with people
who do nothing else.
