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
            │ 1 scan      every open market that has traded enough     │
            │             shares for this account, plus any market we  │
            │             hold or have an order in (even if closed)    │
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
| Schedule gate | `trading/schedule.py` | Whether a scheduled run is due to trade or should end at once |
| Traded range | `trading/quiet.py` | How far an outcome's price has ranged over the last few days, read from the public trade feed |

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

All of that is configuration (`config/paper.json`), not code. Three more
settings came out of the second round of research
(`04_second_round.md`):

| Setting | What it does | Used by |
|---|---|---|
| `max_volume` | Skips markets that have traded this many shares or more, so an account can be kept to thin markets | The thin-market account (20,000 to 100,000 shares) |
| `busy_days`, `busy_range` | Skips an outcome whose traded price has ranged more than `busy_range` over the last `busy_days` days, in a market older than that | The thin-market account (14 days, 15¢) |
| `quiet_days`, `quiet_range` | Buys only outcomes whose traded price has stayed within `quiet_range` over the last `quiet_days` days | No account: the rule it serves did not pass its tests |

The range is the highest minus the lowest price at which the outcome traded,
with trades in the other outcome counted at one minus their price: the
measure the backtest used, read from the same public trade feed. Each check
is one request, so a cycle is allowed 120 of them and remembers the answers
(three hours for an outcome that passed, twelve for one that did not).

### The forward-test log

Each cycle also writes every signal it sees to `shadow.csv`, once per market
per price band: the traded band, and the bands just below and above it that
did not pass the historical test. A signal is logged when it meets the same
18-hour confirmation as a real trade, whether or not the account has money or
room under its caps to take it. `kht shadow` scores the log against how the
markets resolved, in four groups: the rule as traded (stand-alone markets in
the traded band), legs of multi-outcome events in that band, and the bands
below and above. Only signals whose scheduled end has passed are scored.
Counting early resolutions as they happen would bias the result downward: a
"by December" market that closes in November is one where the thing happened. This is how the rule gets tested on genuinely new data at a
useful speed: the account can hold a few dozen positions, the log sees
hundreds.

Beside each logged signal the engine records how far the outcome's price had
ranged over the seven days before it was logged (`shadow_quiet.csv`). The feed
is read as of the signal's own time, so a signal measured late gets the same
answer as one measured at once, and signals logged before this existed are
caught up a hundred or so a cycle. `kht shadow` then reports four more
groups: quiet and not quiet (a range of 3¢ or less, or more), in the traded
band and below it. The second round found that quiet favourites lose less
often and cost more; these groups are how new data gets to say whether there
is anything left over.

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

A story stays capped for as long as the account holds anything in it: each
position remembers the themes it was bought under and any it has come under
since, so the cap does not lapse if the story later spreads past a tenth of
all markets or its markets start to close. This matters now: on 10 November
the tag `iran` was on 8.6% of the markets scanned, just inside the line.

Two **kill switches** are evaluated every cycle from equity marked at the bid:
a daily loss limit and a maximum drawdown from the high-water mark. Once
tripped, buying stops and resting buy orders are cancelled; selling stays
allowed. It stays tripped until a person resets it — a new day does not clear
it. A day starts from the higher of the equity now and the equity the previous
cycle ended on, so a loss that lands between two cycles on either side of
midnight counts against the new day, and after several days without a cycle
the daily limit covers everything lost since the last one. An empty side of
the order book is not read as a price: a position
with no usable quote is carried at cost until one returns, so a cleared book
cannot trip the switch, while a real collapse (the other outcome bid high)
still does.

## Paper trading, and why its results mean something

The paper broker sends nothing to the exchange but is deliberately strict:

- A **taker** order fills against the real order book at that moment, level by
  level, never beyond its limit, and pays the market's real fee rate. Whatever
  is not filled is cancelled, not assumed.
- A **resting** order fills only when a real trade later prints through its
  price on the public tape, or at its price after the shares that were already
  queued ahead of it have traded. Every trade since the previous cycle is
  replayed, however long ago that was, up to 30,000 a market. Beyond that the
  oldest are out of reach, and `STATUS.md` then says that fills may be
  missing: a resting bid is hit when the price falls, so a missed fill would
  make the account look better than it was.
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

**Still to do before a live loop is left alone.** These need a real account,
so they could not be done here:

1. Place one minimum-size order by hand through `LiveBroker` and check the
   fill, the balance and the position on the website.
2. Wire in a check, every cycle, that the ledger agrees with what the exchange
   reports for cash and positions, and halt on any difference. The helper for
   cash exists (`cash_on_exchange`); the check itself does not.
3. Decide what happens to orders the state file does not know about. `sync`
   only asks the exchange about orders this system placed.

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
GitHub's servers and commits the state back to the repository, so the accounts
keep going after any one session ends. A cycle takes one to four minutes.

It is meant to run about every three hours. The workflow asks GitHub to wake
it every 15 minutes, and each run first checks `state/last_cycle_started`. If
a cycle started less than 170 minutes ago, the run ends after a few seconds
without trading (`src/kht/trading/schedule.py`). GitHub starts scheduled jobs
late and drops some, and this way a dropped slot costs minutes rather than
hours. The file records attempts, not successes, so a cycle that keeps failing
is retried every three hours, not every 15 minutes. A run started by hand
(Actions → *paper-trader* → *Run workflow*) always trades, unless its "skip if
a cycle started less than three hours ago" box is ticked.

**GitHub's scheduler has not started this workflow once.** By 14:40 UTC on 10
November 2026, seven hours after the schedule was added, it had passed over
every slot: eighteen for this workflow and fifteen for a second workflow that
has nothing but a schedule. GitHub reported no incident, and runs started
through the manual trigger worked every time, which is how all four cycles so
far were run. Other new repositories have reported the same in 2026.

Two explanations fit, and the second workflow (`scheduler-check.yml`) is there
to tell them apart:

- *New repositories wait.* GitHub may not have begun scheduling here yet. If
  so, both workflows start on their own and nothing needs doing.
- *The schedule belongs to someone without access.* GitHub runs a schedule on
  behalf of whoever last committed its `cron` line. Commits from the Claude
  sessions that built this project carry an address that GitHub maps to an
  account with no access to this repository. At 13:40 UTC the paper trader's
  `cron` line was therefore committed again as the repository owner, through
  GitHub's API, and the check workflow's was left as it was. If the paper
  trader starts and the check never does, this was the cause, and the `cron`
  line must not be edited from a Claude session again without being
  committed again the same way. In the first hour neither had started.

Until the scheduler starts, something else has to start the workflow. All of
these pass through the same three-hour check, so they can overlap safely:

1. **By hand.** Actions → *paper-trader* → *Run workflow*.
2. **Switching the workflow off and on.** Actions → *paper-trader* → ⋯ →
   *Disable workflow*, then *Enable workflow*. Only the repository owner can
   do this. It makes GitHub register the schedule afresh and is worth trying
   once.
3. **A scheduler of your own**, calling GitHub every three hours from a
   machine that is always on or from a hosted cron service. It needs a
   fine-grained personal access token limited to this repository, with
   *Actions: read and write* and nothing else, kept in that machine's
   environment and never in the repository:

   ```bash
   curl -fsS -X POST \
     -H "Authorization: Bearer $KHT_DISPATCH_TOKEN" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/hturcotte1/ProjKHT/actions/workflows/paper-trader.yml/dispatches \
     -d '{"ref":"claude/polymarket-perception-trading-nnq8h8","inputs":{"respect_interval":"true"}}'
   ```

4. **A Claude scheduled task** that starts the workflow every three hours.
   There is nothing to set up beyond asking for it. Each start is a short
   Claude session and counts against the account's usage.
5. **The engine on a machine of your own.** Disable the workflow, clone the
   repository and run the loop there, one process for each account:

   ```bash
   kht run --interval 10800 --report state/paper/STATUS.md
   ```

   ```bash
   kht run --interval 10800 --config config/paper_maker.json --state state/paper-maker --report state/paper-maker/STATUS.md
   ```

   GitHub is then not involved. Live trading would have to run this way in
   any case, because GitHub's runners fail Polymarket's location check.

| Account | Config | State | What it is |
|---|---|---|---|
| Main | `config/paper.json` | `state/paper/` | The rule that passed its test: 95–98¢, markets with 100,000 shares or more |
| Experimental | `config/paper_maker.json` | `state/paper-maker/` | Resting-bid entry on a wider band; unproven |
| Thin markets | `config/paper_thin.json` | `state/paper-thin/` | 90–98¢ in markets with 20,000 to 100,000 shares, where the second round found the same edge repeating and larger. Started 10 November 2026 |

The thin-market account is the one to watch first. History can show that
contracts in those markets were underpriced and cannot show whether a $20
order fills at the price a backtest assumed. Its fills are against the real
order book, so a few weeks of them answer that.

`STATUS.md` in each state directory is the page to read. To stop the schedule:
repository → Actions → *paper-trader* → ⋯ → *Disable workflow*.

Three things to know about running it this way:

- If nothing starts the workflow, the accounts stop, and nothing says so.
  The time in `state/last_cycle_started` and the date at the top of
  `STATUS.md` show when the last cycle ran, and `STATUS.md` gives the longest
  gap between two cycles so far. A missed cycle or a missed day does no harm
  to the positions, which are held for weeks, and the loss limits and the
  replay of resting orders are built to cope with a gap of any length. What a
  long gap costs is the signals that came and went in between, which the
  forward-test log never sees.
- GitHub only runs schedules from the repository's default branch, and it
  pauses them in a public repository after 60 days without activity. Each
  cycle's state commit counts as activity. If the schedule is paused, the
  Actions tab says so and has a button to re-enable it.
- The repository is public, so the rule, the research and the paper accounts'
  positions can be read by anyone. Making it private changes nothing in the
  code, but every run is then billed as at least a minute of the account's
  free Actions allowance, including the runs that find no cycle due. Change
  the schedule line to `17 */3 * * *` first: eight runs a day instead of
  ninety-six.

## Files the system writes

All under the state directory (default `state/paper/`):

| File | Contents |
|---|---|
| `state.json` | Cash, positions, orders, risk state, the config and model in force |
| `STATUS.md` | The readable account page |
| `equity.csv` | One row per cycle: equity, cash, exposure |
| `fills.csv` | Every fill |
| `settlements.csv` | Every resolved position and its profit |
| `decisions.jsonl` | Every order placed, every order a limit blocked with the reason, each cycle's count of candidates the limits screened out before they were proposed, and any market whose trades could not be read back to the previous cycle (`tape_incomplete`) |
| `shadow.csv` | The forward-test log: every signal seen, traded or not |
| `shadow_quiet.csv` | For each logged signal, the traded range of its price over the seven days before it was logged |
| `quiet.csv` | Each range check made for a trading decision (only in accounts with a range filter) |

One file sits beside the account directories: `state/last_cycle_started`, the
time the scheduled workflow last began a cycle.

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
python scripts/check_loss_bunching.py       # did the rule's losses bunch in time more than chance?
```

```bash
python scripts/check_late_entry.py          # does buying a contract late do as well as buying it first?
```

The second round (`04_second_round.md`), in the order it was run:

```bash
python scripts/run_quiet_favourites.py                    # track A on the first round's panel
```

```bash
python scripts/download_trades.py crypto_price --shard 0/3   # and 1/3, 2/3
python scripts/download_crypto_prices.py
python scripts/run_crypto_price.py                        # the first round's rule on crypto, discovery set
python scripts/run_crypto_yardstick.py                    # an outside fair value for crypto price markets
```

```bash
python scripts/download_trades.py sports_other --shard 0/3   # and 1/3, 2/3
python scripts/run_quiet_replication.py sports_other
```

```bash
python scripts/download_research_data.py meta --thin      # markets with 20,000 to 100,000 shares
python scripts/download_trades.py non_sports_thin --shard 0/3   # and 1/3, 2/3
python scripts/run_quiet_replication.py non_sports_thin   # the quiet rule and the first round's rules on thinner markets
python scripts/run_thin_markets.py                        # what those markets can take, and accounts that add them
```

```bash
python scripts/run_position_size.py && python scripts/check_stops_and_paths.py
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
python scripts/run_wallet_skill.py          # does past wallet skill persist, and can it be followed
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
