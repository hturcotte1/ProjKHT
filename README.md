# Project KHT

Trading how the crowd *perceives* an outcome on Polymarket, rather than the
outcome itself: research, a tested rule, and a trading system running on paper.

## Where this stands (11 November 2026)

**The one rule that passed its tests lives on polymarket.com, which a US
resident cannot use. On Polymarket US, the exchange the account will be on,
nothing is confirmed.** Polymarket US is a separate exchange with its own
markets, crowd, fees and data. A fourth round went looking for what carries
over. Its answers are below, under "The fourth round"; in one line each:

- the rule's kind of question barely exists on Polymarket US, and what
  history there is leans the same way without proving it;
- Polymarket US's price history cannot be trusted for a backtest, so its
  live order books are now recorded every cycle instead;
- three new things were tested on Polymarket US with the rules fixed
  first, and all three failed: a search over thousands of rules, buying
  whatever is cheaper there than on polymarket.com, and sports;
- one lead is open: the exchange pays a published reward for orders left
  resting in its markets, and before most sports games very little is
  resting where it counts. The risk is being traded against just before a
  price moves. On 29,647 past lower-tour tennis matches that cost 18¢ to
  21¢ for each hour that 100 contracts rested on each side, and the
  formula pays about 27¢ an hour: a real margin and a thin one. In doubles
  and darts the cost was the larger. A paper account now tests this on
  live order books with its rules fixed in advance
  (`docs/09_sports_rewards.md`), and the program that would place the
  orders is written and rehearsing on paper (`docs/10_us_quoter.md`).
  Whether the exchange pays what its formula says can only be learned
  with a real account, which is the owner's call;
- **and that lead has a date on it.** The exchange has filed amended rules
  with its regulator, in force from 18 November 2026, that let it cap a
  reward at a share of what the account itself trades. Where it sets such
  a cap, orders that rest without being traded against earn nothing, and
  the lead ends there (`docs/09_sports_rewards.md`, section 9). Whether
  and where it will set one is not yet published.

## What came out of it

**The idea as first stated does not survive costs.** "Buy at 70 because the
crowd will be at 80 by Tuesday" was tested as momentum, as reversal, as a
response to big moves, with resting orders instead of paying the spread, by
following wallets with a good record, and in sports as pre-game drift and as
public tickets versus large money. Day-to-day price changes turned out to be
close to unpredictable, and a round trip costs about 6% of the stake. Wallets
that were right before do stay slightly right, but the price has moved within
a minute of their trades. Every version lost money or did nothing.

**But the crowd has a standing blind spot, and it is tradable in a small
way.** People overpay for long shots: a contract bought under 10¢ loses about
60% of the stake on average. The other side of that is that near-certain
contracts are slightly too cheap, and nobody is paid enough to fix it while
their money sits locked up. The third round found the lean is more specific
than long shots: asked "will this happen?", the crowd pays too much for
"Yes", at every price, and the contract worth holding is the "No".

| Tested on markets never looked at beforehand | Trades | Won | Return per trade | t |
|---|---:|---:|---:|---:|
| The rule I committed to first: buy 90–97¢, hold | 2,319 | 94.8% | +0.88% | 1.7 — **failed** the bar of 3 |
| Its pre-registered variant: buy 95–99¢, hold | 2,822 | 98.2% | +0.96% | 3.6 — **passed** |
| Control: buy 3–10¢ long shots | 2,378 | 4.5% | −37% | −5.8 — as predicted |

**What the main paper account trades:** the "No" side of stand-alone yes/no
markets at 95–98¢, bought a day after first being seen in that range, held to
resolution. About 98 trades in 100 gain 3–4%; about 2 in 100 lose the whole
stake. As a $1,000 account at $20 a position the backtest made roughly 7–9% a
year with a third of the money in use. That is a real edge and a thin one.

**It does not scale far.** Judged by how much actually traded at those
prices, and assuming a tenth of it could be bought, a larger account would
make about 6–7% a year up to $50,000–100,000 (roughly $4,000–7,000 a year),
and no more than about $20,000 a year at any size. It only works as many
small positions: the biggest markets include the biggest losers.

**Sports: nothing.** Both sports rules failed; pre-game prices there are well
calibrated.

### The second round

A second round on the same day went looking for something better than a thin
edge. Its own new ideas failed, and the one result it was proud of was wrong.

| Tried | Result |
|---|---|
| Buy only favourites whose price has gone quiet for a week | Not passed. They lose a third to a half as often and cost more; half a point a trade, not significant |
| Price crypto markets from the coin's price and volatility, and buy where Polymarket disagrees | No. Where they disagree, Polymarket's price is right |
| The confirmed rule on crypto price markets | Not repeated: same return, but the losses all come in the same weeks |
| The confirmed rule on sports season-long markets | No edge at all |
| The confirmed rule on thinner news markets | **Reported as t = 9.0 and "larger than in big markets". Withdrawn in round three**: see below |
| Stop-losses | Lower the return at every level |

### The third round, and a correction

Round two chose its "thin" markets by how much they had traded *by the end*.
Nobody knows that when placing a trade, and it is not neutral: a market
where the surprise happens draws a burst of trading and leaves the thin
group, taking its losses with it. Round three caught this before reading its
own data, rebuilt every universe from what a market had traded *at the
time*, and reran everything.

| | As reported in round two | Measured without hindsight |
|---|---:|---:|
| The first round's test in big markets | +0.96% a trade, t = 3.6 | +0.97%, t = 3.6: **unchanged** |
| The rule in markets at 20,000–100,000 shares | +1.69%, t = 9.0 | +0.33%, t = 1.7 |
| Its 95–98¢ stand-alone form there | +1.96%, t = 6.0 | +1.10%, t = 3.4 |
| The wider 90–98¢ band there | +2.40%, t = 5.5 | +0.70%, t = 1.5 |
| Resting bids there | +3.57%, t = 5.6: "passed" | +1.42%, t = 2.3: not passed |
| The rule in markets at 5,000–20,000 shares | would have shown +1.58%, t = 8.1 | −0.26%, t = −1.3 |

The edge does not grow as markets get smaller. It shrinks, and below 20,000
shares it is gone. It belongs to the markets people are watching.

What round three found, on markets nobody had looked at and with the tests
fixed first:

| Tried | Result |
|---|---|
| **At the same near-certain price, buy "No" and not "Yes"** | **Passed.** "No" earned 4.9 points a trade more than "Yes" (t = 3.9); 3.6 points pooled over three sizes of market (t = 4.4) |
| "Yes" against "No" at every price from 3¢ to 98¢ | "Yes" lost money in 23 of 27 cells, at every price in the untouched markets. Asked "will this happen?", the crowd pays too much for "Yes" |
| "No" at 90–98¢ with 60–180 days to run instead of 3–60 | +5.4% a trade in big markets (t = 9.9) and +4.1% in thin ones (t = 6.4), where it was explored; +2.5% (t = 2.7) where it was tested. Not passed; now in a paper account |
| "No" at 50–90¢ | Positive in all three sizes of market, not significant where tested. Not passed |
| The leader of a multi-way event | 1 loss in 265 in big markets, ordinary elsewhere. Not passed |

Every account now buys the "No" side only. As accounts, the main rule and the
long-dated one each earn roughly 7–12% and 6–8% a year on $1,000 in the
backtests; they do not add up inside one account, because they compete for
the same events. The whole story is in
[`docs/05_third_round.md`](docs/05_third_round.md).

### The fourth round: Polymarket US

The owner's proposal was to backtest and paper trade thousands of strategies
and keep the best. Done carelessly that finds winners in pure noise, so the
judge was fixed first: a search half and an untouched half, a bar set by
rerunning everything in worlds where every price is right, and nothing
counted as found unless it clears what the luckiest worthless rule reaches.

| Tried | Result |
|---|---|
| 53,760 rules on three years of polymarket.com | 32 survive, against 0.1 expected from luck. All 32 are one idea, the one already known: "No" on a stand-alone question. 23 of them are the long-dated form |
| Those 32 rules on Polymarket US | **None confirmed.** It lists too few such questions: the best rule scores 2.06 against a bar of 2.61. The lean is the same: +2.1% a trade on 392 trades |
| The same search on Polymarket US alone | **Nothing.** A first run found 18 winners. They were prices at which nothing could be bought |
| What Polymarket US's price history is | Where one side of an order book is empty it shows the last trade as if it were a quote. Checked against more than 600 live books. A backtest on it buys from nobody |
| **Two exchanges, one question:** buy on Polymarket US whatever is cheaper there than on polymarket.com | **Failed**, on rules fixed beforehand: −19.8% on 505 purchases. The two exchanges are equally accurate, and for most shared questions polymarket.com is the smaller market |
| Sports on Polymarket US (most of that exchange): 3,360 rules on a year of games, fixed in writing first | **Nothing.** Not one rule passed even the first step, on 118,339 games. An hour before a game the middle of the order book is a fair price; a buyer loses the spread and the fee ([`docs/06_polymarket_us.md`](docs/06_polymarket_us.md), section 10) |
| **Being paid to leave orders.** Polymarket US pays rewards for resting orders and publishes the schedule | **A lead, not a result.** Outside sports some pools are paid to nobody today ([`docs/08_rewards.md`](docs/08_rewards.md)). In sports every game has its own pool. By the published formula 100 contracts resting on each side before a lower-tour tennis match would be paid about 27¢ an hour, and on 29,647 past matches being run over cost 18¢ to 21¢ an hour: the reward is about one and a half times the cost. Doubles and darts fail that check. A paper test on live order books is running, rules fixed first. **From 18 November 2026 the exchange's filed rules let it cap a reward at a share of the account's own trading, which would end this where it is applied:** [`docs/09_sports_rewards.md`](docs/09_sports_rewards.md), section 9 |

What exists now that did not: a recorder that writes down the real order
books of Polymarket US, with sizes, every cycle, and the polymarket.com
quote for the same question where there is one. It is the only evidence
about that exchange worth having, and it took three wrong write-ups to
learn that. The story is in
[`docs/06_polymarket_us.md`](docs/06_polymarket_us.md) and
[`docs/07_two_venues.md`](docs/07_two_venues.md).

## Where to read what

| If you want | Read |
|---|---|
| The reasoning before any data: every route considered, and the rules fixed in advance | [`docs/01_thinking_session.md`](docs/01_thinking_session.md) |
| What the data said, with numbers, figures and what could still be wrong | [`docs/02_research_findings.md`](docs/02_research_findings.md) |
| How the trading system works and how to operate it | [`docs/03_system.md`](docs/03_system.md) |
| The second round: what was tried next, fixed in advance, and what happened | [`docs/04_second_round.md`](docs/04_second_round.md) |
| The third round: which side of the bet carries the edge, and the correction of round two | [`docs/05_third_round.md`](docs/05_third_round.md) |
| The fourth round: Polymarket US, a wide search with a judge fixed first, and what its price feed really records | [`docs/06_polymarket_us.md`](docs/06_polymarket_us.md) |
| Two exchanges quoting the same question: the idea, the test, and why it failed | [`docs/07_two_venues.md`](docs/07_two_venues.md) |
| Rewards for resting orders on Polymarket US: what is public, what is unknown, and the small test that would settle it | [`docs/08_rewards.md`](docs/08_rewards.md) |
| Rewards in sports games: what the order books show, and the paper test of small resting orders, fixed in advance | [`docs/09_sports_rewards.md`](docs/09_sports_rewards.md) |
| What the paper orders before games did in the latest run | `state/us-rewards/STATUS.md` (from its first run) |
| The system that would rest those orders for real: what it does, its limits, and the steps before any real order | [`docs/10_us_quoter.md`](docs/10_us_quoter.md) |
| What Polymarket US's order books showed at the last cycle | [`state/us/STATUS.md`](state/us/STATUS.md) |
| What the paper accounts hold right now | [`state/paper/STATUS.md`](state/paper/STATUS.md), [`state/paper-maker/STATUS.md`](state/paper-maker/STATUS.md), [`state/paper-thin/STATUS.md`](state/paper-thin/STATUS.md), `state/paper-long/STATUS.md` (from its first cycle) |

## What is running

Four **paper** accounts (no real money, no orders sent) trade against live
Polymarket prices through GitHub Actions and commit their state to this
repository. They are set to trade about every three hours: the workflow asks
to be woken every 15 minutes and trades when three hours have passed.
GitHub's scheduler passed over it for the first thirteen hours, so the cycles
of 10 November 2026 were started by hand. Since 00:56 UTC on 11 November it
has been running them unattended, about every four hours: GitHub starts the
workflow far less often than it is asked to. `state/last_cycle_started` shows
when the last cycle ran, and
[`docs/03_system.md`](docs/03_system.md#on-a-schedule-without-a-server) lists
the ways to keep it going if the scheduler stops.

| Account | Rule | Status |
|---|---|---|
| Main, `state/paper/` | "No" at 95–98¢, stand-alone markets with 100,000 shares or more, buy at the ask | The rule that passed, on the side that carries it |
| Experimental, `state/paper-maker/` | "No" at 90–98¢, same markets, resting bid | Better in the backtest, fell just short of the bar; unproven |
| Thin markets, `state/paper-thin/` | "No" at 95–98¢, markets with 20,000 to 100,000 shares so far | Weakly supported (+1.1% a trade, t = 3.4). It traded 90–98¢ until round three showed that band rested on a flawed sample |
| Long-dated, `state/paper-long/` | "No" at 90–98¢ with 60 to 180 days to run, 20,000 shares or more; a resting bid for three days, then the ask | Exploratory: strong where explored, short of its bar where tested |

Each cycle also logs *every* signal it sees, traded or not, so the rule can be
scored on new data far faster than a small account allows.

All four trade polymarket.com prices. They are the forward test of the rule
itself, not of anything a US resident can do with it.

The same job also runs the **Polymarket US recorder** (`kht us-record`,
`state/us/`): no account, no trades, only the order books written down.

A second job, *us-rewards*, runs the **paper orders before games**
(`kht us-rewards`, `state/us-rewards/`). It follows every game in the
exchange's reward programmes on who wins through the six hours before its
start, reading each order book about every two minutes, and works out what
orders of a fixed size would have been paid by the published formula and
how often they would have been traded against. It is a simulation: no
account, no orders, no key. Each run lasts five hours and starts the next,
and it stops by itself on 18 November 2026. The rules it follows are fixed
in [`docs/09_sports_rewards.md`](docs/09_sports_rewards.md), section 5.

The same job runs a **rehearsal** beside it (`kht us-quote`,
`state/us-quoter/`): the program that would place such orders for real,
on paper, choosing 20 games at a time under its own limits
([`docs/10_us_quoter.md`](docs/10_us_quoter.md)). It sends nothing
anywhere. Its connection to the exchange has never been run.

```bash
python scripts/us_rewards_score.py --settle   # add the runs up and apply the judge
```

```bash
kht report            # the paper account
```

```bash
kht shadow            # every signal seen so far, scored against how it resolved
```

To stop the schedule: repository → Actions → *paper-trader* → ⋯ → *Disable
workflow*. The same for *us-rewards*, or add an empty file
`state/us-rewards/STOP`.

## Before any real money

Live trading is built but switched off, and has never touched a real account.
Three things are yours to settle first.

1. **Which Polymarket.** The live code targets polymarket.com's API through
   the official SDK, and the owner of this project lives in the United
   States, where only Polymarket US is open. Nothing has passed a test on
   Polymarket US (the fourth round, above), so there is nothing to trade
   there yet, and no adapter for placing orders on it has been written. The
   read-only client is `src/kht/api/polymarket_us.py`.
2. **Where it runs.** Polymarket only accepts orders from permitted locations
   and publishes a check for it. The cloud machine this was built on, and
   GitHub's runners, fail that check (United States). The code refuses to
   trade where the check fails, and should not be made to.
3. **Limits and keys.** Bankroll and caps live in the config file. Keys go in
   environment variables on the machine that trades: never in this
   repository, never in a chat.

Then: let the forward-test log rule out a clear failure, which it can do by
about January. Confirming an edge this thin takes around a thousand resolved
signals, a year or so
([findings, section 10](docs/02_research_findings.md#10-what-happens-next)).
And place one minimum-size order by hand, checked against the website, before
any loop is switched on. Details in [`docs/03_system.md`](docs/03_system.md).

## Layout

```
src/kht/api/        read-only clients for Polymarket's public data
src/kht/data/       bulk, resumable downloads
src/kht/research/   panel building, statistics, quotes rebuilt from the trade tape
src/kht/backtest/   backtester: real prints, fees, finite capital
src/kht/trading/    strategy, risk limits, brokers (paper and live), engine
scripts/            the research, in the order it was run
config/             strategy settings and the fitted model
reports/            result tables and figures
state/              the paper accounts
tests/              the test suite
```

```bash
pip install -e ".[research,dev,live]" && pytest
```
