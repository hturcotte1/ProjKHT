# 01 — Thinking session: trading perception instead of outcomes

*Written 2026-11-10, before any hypothesis was tested on data. Section 6 is a
pre-registration: the tests were fixed here first so that the results in
`02_research_findings.md` cannot be quietly re-shaped to look better.*

## 1. The thesis, stated precisely

A Polymarket price is the marginal trader's probability for an outcome — the
crowd's *perception*. The thesis is that the **change** in that perception over
the next hours or days is easier to forecast than the outcome itself:

> buy at 70¢ because we expect the crowd to be at 80¢ on Tuesday, sell at 80¢,
> and never care who wins.

Keynes described this game in 1936 as a beauty contest in which the skill is
"anticipating what average opinion expects the average opinion to be".

## 2. The benchmark we have to beat: prices should be unpredictable

If the crowd updated rationally, today's price would already equal the expected
value of every future price (a martingale). There would be nothing to forecast.
So "predict perception" only works where the crowd **departs from rational
updating in a systematic way**, or where something mechanical pushes prices
(order flow, fees, locked-up capital).

That gives a discipline for the whole project. Every idea below has to name:

1. the specific human tendency or mechanical force that makes the price path
   predictable,
2. why it has not been competed away (fees, thin books, small size, tied-up
   capital, inattention), and
3. a test that could show it is false.

Ideas that cannot name all three are stories, not strategies.

## 3. Two facts that shape everything

### 3.1 Perception trading and outcome betting are the same skill, with a choice at the exit

Suppose we buy at 70¢ and the crowd later re-rates to 80¢. If 80¢ is a fair
price at that point, then *selling at 80¢* and *holding to resolution* have the
same expected profit (10¢). Holding pays no exit spread or fee but carries the
outcome's variance; selling locks the gain but pays to leave. Sports bettors
call the first number "closing line value": beat the closing line consistently
and you win long-run whether or not you ever sell.

So the system does not have to round-trip. Forecasting the price path is the
edge; whether to sell early or hold is a separate cost-versus-variance choice
made per trade.

### 3.2 Costs today are large relative to typical price moves

Checked against Polymarket's fee page on 2026-11-10:

| | |
|---|---|
| Taker fee per share | `rate × p × (1 − p)`; rate is 0.03–0.07 depending on the market (0.03 on the NFL moneyline we sampled, 0.05 on its props, 0.07 on crypto) |
| Maker fee | zero, plus a rebate of 15–25% of the taker fees collected |
| Fee-free | geopolitics / world-events markets |
| Worst case | at 50¢ a taker pays 0.75–1.75¢ per share each way, on top of the spread |

A taker round trip at mid prices therefore costs roughly 2–4¢ per share. Most
perception moves are smaller than that. Three consequences:

- small edges must be captured as a **maker** (resting limit orders) or by
  **holding to resolution**, not by crossing the spread twice;
- fees shrink toward the price extremes (`p(1−p)`), so the same edge is cheaper
  to harvest at 85¢ than at 50¢;
- fee-free geopolitics markets are structurally the cheapest place to round-trip.

## 4. What the literature already says

| Source | Finding | Relevance |
|---|---|---|
| Walker, Princeton thesis (2026): 188,509 resolved Polymarket markets | Prices are compressed toward 50¢ (recalibration slope 1.11): longshots overpriced, favourites underpriced, in every domain, worse far from resolution | A slow, predictable re-rating as resolution nears |
| Le, arXiv 2602.19520 (2026): 429k contracts, Kalshi + Polymarket | Political markets persistently underconfident (compressed to 50¢) on both venues; about half the raw variation is noise once errors are clustered by event | Same effect; warns that naive significance is overstated |
| Bürgi, Deng & Whelan (2025), Kalshi | Longshot bias is much stronger for takers than makers | Be the maker |
| Moskowitz, *Journal of Finance* (2021): 100k+ sports contracts | Open-to-close line moves show momentum that the game outcome then **reverses** (delayed overreaction); too small to beat bookmaker costs | Direct test of the thesis in sports: the crowd's pre-game drift is real but is an overshoot |
| Ottaviani & Sørensen, *AER* (2015) | With diverse beliefs and limited budgets, prices **underreact** to news: momentum first, reversal later | Theoretical reason to expect drift after news |
| Choi & Hui (2014), in-play soccer | Under-reaction to ordinary news, over-reaction to surprising news | Sign of the effect may flip with the size of the jump |
| Barber & Odean (2008); Da, Engelberg & Gao (2011) | Retail buys whatever grabs attention; attention spikes lift prices temporarily | Attention-driven overshoot and fade |
| Dubach, arXiv 2604.24366 (2026), Polymarket order book | Trade direction inferred from the public feed is wrong ~40% of the time; use taker-side fills | Our flow data must come from the trade tape, not the book feed |

Two things stand out. First, nobody in this list reports a tradable short-term
momentum or reversal effect on Polymarket itself — the price-path question is
open, which is what makes it worth testing. Second, the best-documented effect
(compression toward 50¢) is a statement about perception being *predictably
wrong and predictably corrected*, which is the thesis in slow motion.

## 5. The brainstorm: every route I could think of

### A. How crowds revise beliefs (psychology of updating)

- **A1. Under-reaction → momentum.** Anchoring on the old price, conservatism,
  news that diffuses slowly through a casual audience, and the disposition
  effect (holders sell winners early, which caps the rise). Prediction: a move
  over the last day continues over the next few.
- **A2. Over-reaction → reversal.** Salient, vivid news and attention-driven
  buying overshoot. Prediction: large fast jumps partly give back.
- **A3. It depends on the size of the surprise.** Small moves continue, extreme
  moves revert (Choi & Hui). Prediction: continuation is a hump-shaped function
  of jump size.

### B. Standing biases that leak out slowly

- **B1. Favourite–longshot bias.** People overweight small probabilities.
  Longshot prices bleed down; favourites grind up.
- **B2. Compression far from resolution.** Capital is locked until resolution,
  so nobody bothers to push a 90% favourite to its fair 93%. The gap closes as
  the event nears.
- **B3. "Something will happen" bias.** The dramatic outcome is more fun to buy
  than its boring complement.
- **B4. Loyalty and wishful thinking.** Popular teams and candidates are
  overbought, most of all when casual money shows up.

### C. When the crowd shows up (timing and flow)

- **C1. Pre-game public money.** Casual bettors arrive in the last day before a
  game and lean toward favourites and famous teams. (The Seahawks example.)
- **C2. Weekend and evening flow.** Recreational money trades at predictable
  times.
- **C3. Deadline decay.** "Will X happen by date D" must fall toward zero if
  nothing happens. Is the path of that decay priced correctly?
- **C4. Newly listed markets.** Early prices are set by few people.

### D. Who knows what, and when the crowd finds out

- **D1. Informed versus casual flow.** Follow wallets with a record of skill,
  fade the rest.
- **D2. Slow diffusion between related markets.**
- **D3. Outside lead indicators** of perception: sportsbook lines, polls, news
  and search volume.
- **D4. A language model reading the news** to forecast the crowd's reaction.

### E. Structural edges that are not about perception

Near-certain "bond" yield, multi-outcome arbitrage, liquidity rewards and maker
rebates. These are crowded and latency-sensitive and are not the thesis, but
maker rebates matter as an execution choice.

### How I narrowed it

| Filter | Why |
|---|---|
| Testable tonight on free public data with a large sample | No external paid feeds; rules out D3 and D4 for now |
| Does not need to be fastest | Our reaction time is minutes to hours; rules out in-game and sub-minute effects |
| Survives 2–4¢ of round-trip cost, or works as a maker / held to resolution | Section 3.2 |
| Has a behavioural reason and a reason it persists | Section 2 |
| Works at small size | A small account can trade thin markets that larger players ignore |

D1 (wallet-level flow) passes the filters but needs wallet-history data that is
expensive to assemble; it is the first extension if the price-path tests come
up short.

## 6. Pre-registered tests

Data: every resolved binary market with at least 100,000 shares traded and a
life of two days or more, with its full price history at 3-hour resolution;
plus finer bars for recent sports games. Price change is measured in cents per
share. Standard errors are clustered by event (markets in one event move
together) and, where relevant, by calendar day. With roughly a dozen
hypotheses, a result counts as a finding only at |t| ≥ 3, and only if it holds
in the later half of the sample when estimated on the earlier half.

| # | Hypothesis | Test | Supports the idea if |
|---|---|---|---|
| H1 | Momentum (A1) | Regress next-k-bar price change on the past-j-bar change, for j, k from 3h to 7d | Positive slope beyond one bar |
| H2 | Reversal after jumps (A2/A3) | Next-period change conditional on the size of the last move, in bins | Sign turns negative for the largest moves |
| H3 | Compression / longshot bias (B1/B2) | Mean price change to resolution by price bin; calibration slope by time to resolution | Low prices fall, high prices rise; slope > 1, larger far from resolution |
| H4 | "Something happens" bias (B3) | Unconditional drift of the Yes side in Yes/No markets | Negative mean drift |
| H5 | Pre-game drift (C1) | Change from T−24h to kickoff by favourite status; does the pre-game move predict the result? | Favourites rise into kickoff; move is not confirmed by outcomes (overshoot) or is (information) |
| H6 | Calendar effects (C2) | Mean change by weekday and hour | Stable pattern across both halves |
| H7 | Deadline decay (C3) | Path of "by date" markets versus a constant-hazard benchmark | Systematic deviation |
| H8 | New-market effects (C4) | Drift and compression in the first days of a market | Early prices more compressed |

Known traps, and how each test guards against them:

- **Bid–ask bounce** looks like reversal. Any reversal result must survive
  skipping one bar between signal and entry, and must be re-checked on trade
  prices with known taker side.
- **Trading at the mid** flatters every backtest. Backtests pay half the spread
  plus the taker fee each way unless the order is modelled as a resting maker
  order, in which case a fill is not assumed.
- **Selecting markets by final volume** peeks at the future. Results are
  re-run on a stricter volume cut; if they change sign, they are not findings.
- **Correlated markets** inflate significance. Cluster by event.
- **Trying many ideas** guarantees false positives. Threshold of |t| ≥ 3 plus
  an untouched later sample.

## 7. Direction

Build one statistical model of **expected price drift** — a forecast, for each
market, of where the crowd's price will be over the next hours to days — using
whichever of H1–H8 survive. Trade the forecasts that exceed costs, as a maker
where the edge is thin, and decide sell-versus-hold per trade as in 3.1.

If nothing survives costs, say so plainly, and fall back to the best-documented
slow effect (H3) with maker execution.

## 8. Second pre-registration (2026-11-10, 06:40 UTC)

*Added while the data was still downloading, after two things had been learned
from the newest slice only (non-sports markets that closed between 2026-06-08
and 2026-11-10; about 3,200 of 16,500 markets, because tapes download
newest-first). Nothing older had been looked at when this was written.*

### What changed

1. **The sample had to be redefined.** Markets had been chosen by *total*
   volume. Total volume is larger when something dramatic happens, so the
   sample over-represented upsets and made underdogs look underpriced
   (calibration slope 0.81). Restricting to markets that had *already* traded
   100,000 shares at the moment of each observation — a rule that uses no
   hindsight — reversed the sign (slope 1.14). Every result from here on uses
   the no-hindsight rule, which requires the trade tape, so the tape is now
   the primary data set and the price panel secondary.

2. **Prices come from the tape, not the mid.** Each tape row is a taker order
   with a known side, so the last taker buy marks the ask and the last taker
   sell marks the bid. Backtests now enter at a price a taker demonstrably
   paid, one bar after the signal.

3. **A candidate edge appeared in the newest slice**: contracts quoted at
   90–97¢ paid out more often than their price (about +3¢ after today's
   fees), and contracts under 10¢ lost most of their stake. The effect grew
   with time to resolution.

### The rule fixed here, to be judged on the older, unseen data

> **R1.** In non-sports, non-crypto markets that have already traded 100,000
> shares: when one side's ask is above 90¢ and at most 97¢ and the scheduled
> end is more than 3 and at most 60 days away, buy it at the next taker-buy
> print (if still in range and within 3 days), pay today's taker fee for the
> category, and hold to resolution. One position per market.

Variants fixed at the same time: (a) 7–60 days; (b) sell 3 days before the
scheduled end instead of holding; (c) 80–97¢; (d) 95–99¢.
Controls that should *lose* if the effect is real: the same rule on 3–10¢
contracts, and on 40–60¢ contracts.

**Holdout:** markets that closed before 2026-06-08. R1 counts as confirmed
only if its average return per trade there is positive with |t| ≥ 3
(clustered by event) and the longshot control is negative. The paper trader
is the second, forward-looking test.

### Known weaknesses to check, listed before looking

- Entry requires a taker-buy print on the next days. If informed traders buy
  favourites that are about to win, conditioning on that print flatters the
  result; compare against entering at the signal bar's ask.
- Markets still open today are missing (censoring). Limit the comparison to
  entries whose scheduled end has passed, and count overdue open markets.
- A 93¢ position that fails loses 93¢. Report the worst event, the worst day
  and results with the best events removed.
- Markets that resolved 50/50 must be included as a half-payout, not dropped.
