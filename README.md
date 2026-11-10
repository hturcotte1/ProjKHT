# Project KHT

Trading how the crowd *perceives* an outcome on Polymarket, rather than the
outcome itself: research, a tested rule, and a trading system running on paper.

## What came out of it

**The idea as first stated does not survive costs.** "Buy at 70 because the
crowd will be at 80 by Tuesday" was tested as momentum, as reversal, as a
response to big moves, and in sports as pre-game drift and as public tickets
versus large money. Day-to-day price changes turned out to be close to
unpredictable, and a round trip costs about 6% of the stake. Every version
lost money or did nothing.

**But the crowd has a standing blind spot, and it is tradable in a small
way.** People overpay for long shots: a contract bought under 10¢ loses about
60% of the stake on average. The other side of that is that near-certain
contracts are slightly too cheap, and nobody is paid enough to fix it while
their money sits locked up.

| Tested on markets never looked at beforehand | Trades | Won | Return per trade | t |
|---|---:|---:|---:|---:|
| The rule I committed to first: buy 90–97¢, hold | 2,319 | 94.8% | +0.88% | 1.7 — **failed** the bar of 3 |
| Its pre-registered variant: buy 95–99¢, hold | 2,822 | 98.2% | +0.96% | 3.6 — **passed** |
| Control: buy 3–10¢ long shots | 2,378 | 4.5% | −37% | −5.8 — as predicted |

**What the paper account trades:** 95–98¢ contracts in stand-alone yes/no
markets, bought a day after first being seen in that range, held to
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

## Where to read what

| If you want | Read |
|---|---|
| The reasoning before any data: every route considered, and the rules fixed in advance | [`docs/01_thinking_session.md`](docs/01_thinking_session.md) |
| What the data said, with numbers, figures and what could still be wrong | [`docs/02_research_findings.md`](docs/02_research_findings.md) |
| How the trading system works and how to operate it | [`docs/03_system.md`](docs/03_system.md) |
| What the paper accounts hold right now | [`state/paper/STATUS.md`](state/paper/STATUS.md), [`state/paper-maker/STATUS.md`](state/paper-maker/STATUS.md) |

## What is running

Two **paper** accounts (no real money, no orders sent) trade against live
Polymarket prices every three hours through GitHub Actions and commit their
state to this repository.

| Account | Rule | Status |
|---|---|---|
| Main, `state/paper/` | 95–98¢, stand-alone markets, buy at the ask | The rule that passed |
| Experimental, `state/paper-maker/` | 90–98¢, stand-alone markets, resting bid | Better in the backtest, fell just short of the bar; unproven |

Each cycle also logs *every* signal it sees, traded or not, so the rule can be
scored on new data far faster than a small account allows.

```bash
kht report            # the paper account
```

```bash
kht shadow            # every signal seen so far, scored against how it resolved
```

To stop the schedule: repository → Actions → *paper-trader* → ⋯ → *Disable
workflow*.

## Before any real money

Live trading is built but switched off, and has never touched a real account.
Three things are yours to settle first.

1. **Which Polymarket.** The live code targets polymarket.com's API through
   the official SDK. Polymarket US is a separate exchange with its own
   accounts, markets, fees and API (it publishes a Python SDK, so an adapter
   is possible). None of this research used its data, and about half of the
   rule's trades were in geopolitics markets, which I could not confirm it
   lists. If the account is there, the rule has to be re-tested there first.
2. **Where it runs.** Polymarket only accepts orders from permitted locations
   and publishes a check for it. The cloud machine this was built on, and
   GitHub's runners, fail that check (United States). The code refuses to
   trade where the check fails, and should not be made to.
3. **Limits and keys.** Bankroll and caps live in the config file. Keys go in
   environment variables on the machine that trades: never in this
   repository, never in a chat.

Then: wait for the forward-test log to say something
([findings, section 10](docs/02_research_findings.md#10-what-happens-next)),
and place one minimum-size order by hand, checked against the website, before
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
