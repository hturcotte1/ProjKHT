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

1. Is the market in an allowed category, with a scheduled end between
   `dte_lo` and `dte_hi` days away?
2. Is this outcome's ask inside the price window, and is the spread sane?
3. Does the edge model say the outcome pays more often than its price, by at
   least `min_edge` per share **after the taker fee**?

Survivors are ranked by estimated return per day of capital tied up, and at
most `max_new_per_cycle` are bought, one position per market. Positions are
held to resolution unless an exit rule is configured.

All of that is configuration (`config/paper.json`), not code.

## What can stop an order

Every order passes `RiskManager.check` first, in backtest, paper and live modes
alike. A buy is refused if any of these would be exceeded:

| Limit | Default | Why |
|---|---:|---|
| Per order | $25 | No single fat-finger |
| Per market | $25 | One position, one stake |
| Per event | $25 | Legs of one event are the same bet |
| Per theme (narrow topic tag shared by several markets) | $75 | Different events about one story resolve together |
| Total exposure | 60% of bankroll | Always keep cash |
| Price window | 3¢–97¢ | Never trade the extreme tails |
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
kht geoblock                    # may this machine place orders?
```

### On a schedule, without a server

`.github/workflows/paper-trader.yml` runs one paper cycle on GitHub's servers
and commits `state/paper/` back to the repository, so the paper account keeps
going after any one session ends. `state/paper/STATUS.md` is the page to read.
To stop it: repository → Actions → *paper-trader* → ⋯ → *Disable workflow*.

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

## Reproducing the research

```bash
pip install -e ".[research,dev]"
```

```bash
python scripts/download_research_data.py meta
```

```bash
python scripts/download_trades.py non_sports --shard 0/3
```

```bash
python scripts/run_confirmatory.py
```

```bash
python scripts/fit_model.py
```

```bash
pytest
```

The raw data (about 2 GB of trade tapes) is not in the repository; the scripts
re-download it from Polymarket's public APIs. Result tables are in
`reports/research/`.
