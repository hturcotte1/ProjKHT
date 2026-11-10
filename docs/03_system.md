# 03 — How the trading system works

This describes the machinery: what runs, in what order, what stops it, and how
to operate it. The reasons for the trading rule itself are in
`02_research_findings.md`.

## One cycle

The system does not run continuously. It wakes up, does one **cycle**, writes
everything down and exits. Nothing is kept in memory between cycles, so it can
be run by any scheduler and survives restarts.

```
            ┌─────────────────────────────────────────────────────────┐
            │ 1 scan      every open market that has traded ≥100k      │
            │             shares, plus any market we hold or have an   │
            │             order in (even if it has since closed)       │
            │ 2 fills     did anything trade into our resting orders?  │
            │ 3 settle    pay out positions in resolved markets        │
            │ 4 mark      value positions at the bid; check kill switch│
            │ 5 decide    strategy lists the orders it wants           │
            │ 6 limits    each order must pass every risk limit        │
            │ 7 execute   broker places what survived                  │
            │ 8 record    state.json, fills, equity, decisions, STATUS │
            └─────────────────────────────────────────────────────────┘
```

Code: `src/kht/trading/engine.py` (`Engine.run_cycle`).

## The parts

| Part | File | What it is responsible for |
|---|---|---|
| Market data | `api/polymarket.py`, `trading/universe.py` | Read-only clients for Polymarket's public APIs; the list of tradable markets |
| Strategy | `trading/strategy.py` | Which contracts to buy and when to sell. A pure function of the market snapshot and the account |
| Edge model | `config/model.json` | The calibration numbers the strategy uses; produced by `scripts/fit_model.py` |
| Risk limits | `trading/risk.py` | Hard caps and the kill switch. Sits between the strategy and the broker |
| Brokers | `trading/broker.py` (paper), `trading/live.py` (real orders) | Turning an approved order into fills |
| Fill rules | `trading/fills.py` | How orders fill; shared by the backtester and the paper broker |
| Ledger | `trading/portfolio.py` | Cash, positions, realised profit |
| Record | `trading/engine.py` (`StateStore`), `trading/report.py` | State on disk and the readable status page |

## What the strategy does

For every scanned market and each of its two outcomes it asks:

1. Is it a stand-alone yes/no market (not one leg of a multi-outcome event),
   in an allowed category, with a scheduled end between `dte_lo` and `dte_hi`
   days away?
2. Is this outcome's ask inside the price window (95–98¢ for the main
   account), and is the spread sane?
3. Does the edge model put the estimated profit per share, **after the taker
   fee**, at `min_edge` or more?
4. Was the contract already in the price window `confirm_hours` (18) hours
   ago? This is checked against Polymarket's own price history. The rule was
   tested as "seen in range one day, bought the next if still in range", and
   the wait matters: it screens out contracts that are falling through the
   range.

Survivors are ranked by estimated return per day of capital tied up, and at
most `max_new_per_cycle` are bought, one position per market. Positions are
held to resolution.

All of that is configuration (`config/paper.json`), not code.

### The forward-test log

Each cycle also writes every signal it sees to `shadow.csv`, once per market
per price band: the traded band, and the bands just below and above it that
did not pass the historical test. A signal is logged when it meets the same
18-hour confirmation as a real trade, whether or not the account has money or
room under its caps to take it. `kht shadow` scores the log against how the
markets resolved. This is how the rule gets tested on genuinely new data at a
useful speed: the account can hold a few dozen positions, the log sees
hundreds.

## What can stop an order

Every order passes `RiskManager.check` first, in backtest, paper and live modes
alike. A buy is refused if any of these would be exceeded:

| Limit | Default | Why |
|---|---:|---|
| Per order | $25 | No single fat-finger |
| Per market | $25 | One position, one stake |
| Per event | $25 | Legs of one event are the same bet |
| Per theme (a topic tag shared by 2 or more markets but under 10% of all of them) | $80 | Different events about one story resolve together |
| Total exposure | 80% of bankroll | Always keep cash |
| Price window | 3¢–98.5¢ | Never trade the extreme tails |
| Open orders | 60 | Bounded bookkeeping |
| Taker edge | must exceed the fee | A taker order that cannot pay its own fee is refused |

Two **kill switches** are evaluated every cycle from equity marked at the bid:
a daily loss limit and a maximum drawdown from the high-water mark. Once
tripped, buying stops and resting buy orders are cancelled; selling stays
allowed. It stays tripped until a person resets it — a new day does not clear
it.

## Paper trading, and why its results mean something

The paper broker sends nothing to the exchange but is deliberately strict:

- A **taker** order fills against the real order book at that moment, level by
  level, never beyond its limit, and pays the market's real fee rate. Whatever
  is not filled is cancelled, not assumed.
- A **resting** order fills only when a real trade later prints through its
  price on the public tape, or at its price after the shares that were already
  queued ahead of it have traded.
- Positions are valued at the **bid**, so the account shows the spread as a
  loss the moment it buys.

The backtester uses the same fill rules (`fills.py`), which is what makes
backtest, paper and live results comparable.

## Live trading

`trading/live.py` places real orders through Polymarket's official Python SDK
(`polymarket-client`). It is **off** and has **never been run against a real
account**. To switch it on, all of these must be true:

1. the config says `"mode": "live"`;
2. the environment has `KHT_ENABLE_LIVE=yes-trade-real-money`;
3. `POLYMARKET_PRIVATE_KEY` and `POLYMARKET_WALLET_ADDRESS` are set in the
   environment — never in the repository or a config file;
4. Polymarket's own geoblock check says the machine may place orders;
5. the account is not in closed-only mode.

Point 4 is a compliance rule. Polymarket lists the United States among the
places where the international platform accepts only closing orders, and its
check reports the cloud machines used to build this project, and GitHub's
runners, as blocked. The code refuses to start there and must not be made to.

Paper and live accounts cannot share a state directory; the engine refuses.

**Polymarket US is a different exchange.** It has its own accounts, markets,
fee schedule and API (documented at docs.polymarket.us, with an official
Python SDK), and `trading/live.py` does not talk to it. Everything in the
research was measured on the international platform's data: 896 of the main
rule's 1,836 backtest trades were in geopolitics markets, which I could not
confirm the US exchange lists. An account there needs its own adapter and,
before that, its own test of the rule on that exchange's markets.

## Running it

```bash
pip install -e .                # the engine (needs only `requests`)
```

```bash
kht candidates                  # what it would buy right now; places nothing
```

```bash
kht cycle --report state/paper/STATUS.md
```

```bash
kht run --interval 1800         # loop: one cycle every 30 minutes
```

```bash
kht report                      # print the account status
```

```bash
kht shadow                      # score every logged signal against how it resolved
```

```bash
kht geoblock                    # may this machine place orders?
```

### On a schedule, without a server

`.github/workflows/paper-trader.yml` runs one cycle for each paper account on
GitHub's servers every three hours and commits the state back to the repository,
so the accounts keep going after any one session ends. A run takes one to
three minutes.

| Account | Config | State | What it is |
|---|---|---|---|
| Main | `config/paper.json` | `state/paper/` | The rule that passed its test |
| Experimental | `config/paper_maker.json` | `state/paper-maker/` | Resting-bid entry on a wider band; unproven |

`STATUS.md` in each state directory is the page to read. To stop the schedule:
repository → Actions → *paper-trader* → ⋯ → *Disable workflow*.

## Files the system writes

All under the state directory (default `state/paper/`):

| File | Contents |
|---|---|
| `state.json` | Cash, positions, orders, risk state, the config and model in force |
| `STATUS.md` | The readable account page |
| `equity.csv` | One row per cycle: equity, cash, exposure |
| `fills.csv` | Every fill |
| `settlements.csv` | Every resolved position and its profit |
| `decisions.jsonl` | Every order placed and every order a limit blocked, with the reason |
| `shadow.csv` | The forward-test log: every signal seen, traded or not |

## Reproducing the research

```bash
pip install -e ".[research,dev]"
```

```bash
python scripts/download_research_data.py meta
```

```bash
python scripts/download_research_data.py prices     # quoted price histories; about 75 minutes
```

```bash
python scripts/download_trades.py non_sports --shard 0/3
```

```bash
python scripts/download_trades.py sports_ml --shard 0/3
```

```bash
python scripts/run_confirmatory.py          # the pre-registered test (non-sports)
```

```bash
python scripts/check_holdout_definition.py  # the same verdicts under the other holdout definition
```

```bash
python scripts/run_confirmatory_sports.py   # the pre-registered test (sports)
```

```bash
python scripts/run_exploratory.py           # everything that was not pre-registered
```

```bash
python scripts/run_exploratory_resting.py   # the round-trip trades with a resting bid
```

```bash
python scripts/run_deployed_rules.py        # the exact rules the paper accounts run
```

```bash
python scripts/run_capacity.py              # how much money the main rule could absorb
```

```bash
python scripts/fit_model.py && python scripts/make_figures.py
```

```bash
pytest
```

The raw data (about 3.5 GB of trade tapes; the downloads took about two hours)
is not in the repository; the scripts re-fetch it from Polymarket's public
APIs. Run each `--shard i/3` in its own terminal. Result tables are in
`reports/research/`.
