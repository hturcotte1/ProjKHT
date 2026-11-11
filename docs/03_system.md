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
| Polymarket US recorder | `api/polymarket_us.py`, `trading/us_recorder.py`, `trading/twins.py` | Not part of any account: writes down the order books of Polymarket US, and the polymarket.com quote for the same question. See "The Polymarket US recorder" below |
| Paper orders before games | `trading/us_rewards.py` | Not part of any account: a simulation of small resting orders on Polymarket US, paid by the exchange's published reward formula. See "Paper orders before games on Polymarket US" below |
| Orders before games, for real or on paper | `trading/us_quoter.py`, `trading/us_live.py` | The system that would rest those orders with a real account: choice of games, limits, orders that may only rest and that expire by themselves. On paper by default; the live connection has never been run. `docs/10_us_quoter.md` |

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

All of that is configuration (`config/paper.json`), not code. More settings
came out of the second and third rounds of research (`04_second_round.md`,
`05_third_round.md`):

| Setting | What it does | Used by |
|---|---|---|
| `max_volume` | Skips markets that have traded this many shares or more, so an account can be kept to thin markets | The thin-market account (20,000 to 100,000 shares) |
| `busy_days`, `busy_range` | Skips an outcome whose traded price has ranged more than `busy_range` over the last `busy_days` days, in a market older than that | The thin-market account (14 days, 15¢) |
| `quiet_days`, `quiet_range` | Buys only outcomes whose traded price has stayed within `quiet_range` over the last `quiet_days` days | No account: the rule it serves did not pass its tests |
| `maker_fallback_hours` | With `entry: maker`, pays the ask once this account's bids in a market have gone unfilled this long, counted from the first bid | The long-dated account (72 hours) |
| `no_side_only` | Buys only the outcome named "No" of a Yes/No question; the other side is still logged | Every account, by decision of the third round's test T5-N |
| `dte_lo`, `dte_hi` | Scheduled days to the end between which a contract qualifies | 3 to 60 everywhere except the long-dated account (60 to 180) |
| `wide_watch_lo` | Also logs stand-alone signals priced from here up to `watch_lo`, on both sides, as band "wide"; never traded | The main and thin accounts (50¢): the forward test of "No" against "Yes" at mid prices |

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
markets resolved, in groups: stand-alone markets in the traded band, the
same split into the "No" side (what the accounts buy) and the "Yes" side
(logged only), legs of multi-outcome events in that band, and the bands
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

**GitHub's scheduler took thirteen hours to begin here, and runs this
workflow about every four hours.** What happened, in UTC:

- *10 November 2026, about 07:40.* The schedule was added. For the next
  thirteen hours GitHub passed over every slot, on a day it reported no
  incident. Runs started through the manual trigger worked every time, and
  the seven cycles of that day were started that way.
- *20:39.* The first scheduled run. It came between cycles and did not trade.
- *11 November, 00:56.* The first cycle nobody started: a scheduled run found
  a cycle due, traded all four accounts and committed their state.

Two explanations had fitted the silence: that GitHub does not begin
scheduling a new repository at once, or that a schedule belongs to whoever
committed its `cron` line and the commits from the Claude sessions that built
this project map to a GitHub account with no access here. To tell them apart
the paper trader's `cron` line was committed again as the repository owner
through GitHub's API, and a second workflow with nothing but a schedule was
left as a Claude session had committed it. Both began within an hour of each
other (20:39 and 21:23), so the first explanation was the right one, and
who commits the workflow file does not matter. The second workflow has been
deleted.

The scheduler is not doing what the `cron` line asks. In its first five hours
it started this workflow twice out of some twenty quarter-hour slots, and the
check workflow twice out of five hourly ones, each about four hours apart and
up to 54 minutes late. With the 170-minute check that means a cycle roughly
every four hours for now, which is enough for accounts that hold positions
for weeks. `state/last_cycle_started` shows when the last one began.

If the scheduler stops, or a cycle every four hours is too slow, something
else can start the workflow. All of these pass through the same three-hour
check, so they can overlap safely with the schedule and with each other:

1. **By hand.** Actions → *paper-trader* → *Run workflow*.
2. **Switching the workflow off and on.** Actions → *paper-trader* → ⋯ →
   *Disable workflow*, then *Enable workflow*. Only the repository owner can
   do this. It makes GitHub register the schedule afresh, and is the first
   thing to try if scheduled runs stop.
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
| Main | `config/paper.json` | `state/paper/` | The rule that passed its test, on the side that carries it: "No" at 95–98¢, markets with 100,000 shares or more |
| Experimental | `config/paper_maker.json` | `state/paper-maker/` | Resting-bid entry on a wider band; unproven |
| Thin markets | `config/paper_thin.json` | `state/paper-thin/` | "No" at 95–98¢ in markets with 20,000 to 100,000 shares so far. Weakly supported: +1.1% a trade (t = 3.4) measured without hindsight. Started 10 November 2026 on a 90–98¢ band that the third round withdrew; what it bought then is held to resolution |
| Long-dated | `config/paper_long.json` | `state/paper-long/` | "No" at 90–98¢ with 60 to 180 days to run, 20,000 shares or more, entered with a resting bid for up to three days and then at the ask. Exploratory: +4–5% a trade where it was explored (t = 6 to 10), +2.5% (t = 2.7) where it was tested. Started 10 November 2026 |

The forward log is the thing to watch. It scores the "No" and the "Yes" side
of every signal apart, which is the one claim that passed a test in the third
round, and it is the only clean test the long-dated account will get. A
bid-first thin-market account existed for a few hours on 10 November and was
withdrawn before its first cycle, when the result behind it turned out to
rest on a sample chosen with hindsight.

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

## The Polymarket US recorder

Polymarket US is the exchange open to US residents. It is separate from
polymarket.com in every way that matters: its own markets, order books, fees
and API. It publishes no trades, and its price history shows the last trade
wherever one side of an order book is empty, so nothing can be backtested on
it honestly (`docs/06_polymarket_us.md`, section 7). What can be done is to
write down its order books as they are.

```bash
kht us-record --state state/us
```

One run reads every open market outside sports and crypto that shows a
quote (about 2,600 order books, five minutes), pairs each with the same
question on polymarket.com where the titles and answers match exactly, and
reads that order book too. It uses public endpoints only, places no orders
and needs no key. The scheduled workflow runs it after the paper accounts;
if it fails, the accounts' state is still committed.

| File under `state/us/` | Contents |
|---|---|
| `snapshots/YYYY-MM-DD/HHMMSS.csv.gz` | One row per market: the three best prices and sizes on each side, the last trade, contracts traded, open interest, and the polymarket.com bid and ask of its twin |
| `markets.csv` | What each market is. Rows are added, never rewritten |
| `twins.csv` | Its twin on polymarket.com, if it has one. Rows are added, never rewritten |
| `rewards.csv` | One line per reward programme per run: how many of its books would have been paid that second (`docs/08_rewards.md`) |
| `log.csv` | One line per run |
| `STATUS.md` | The latest run in words |

The snapshots grow by about half a megabyte a day. They are the data for the
forward tests fixed in `docs/06_polymarket_us.md`, section 8, and
`docs/07_two_venues.md`, section 3. To score them:

```bash
python scripts/us_forward.py --settle
```

## Paper orders before games on Polymarket US

Polymarket US pays a published reward to orders left resting in its
markets, and each sports game has its own pool
(`docs/09_sports_rewards.md`). This is a paper account that rests small
orders before games and is paid by the published formula. It is a
simulation: it reads the public reward schedule and the public order books,
places no orders and needs no key.

```bash
kht us-rewards --state state/us-rewards --minutes 300
```

One run follows every game in a "day-of" reward programme on who wins,
from six hours before its start until ten minutes before, reading its order
book about every two minutes. For each reading it works out where the
paper orders would rest, what share of each side's score they would hold,
and whether the trading since the last reading would have gone through
them. The rules are in `docs/09_sports_rewards.md`, section 5, and in
`src/kht/trading/us_rewards.py`; they are fixed for the length of the test.

It runs in its own workflow, `.github/workflows/us-rewards.yml`. A run
lasts five hours, commits what it recorded and starts the next one. It
stops by itself on 18 November 2026, or at once if a file
`state/us-rewards/STOP` exists.

| File under `state/us-rewards/` | Contents |
|---|---|
| `runs/<run>/games.csv.gz` | One row per game per US date: seconds watched and quoted, and for each order size the share of the score it held, in share-seconds |
| `runs/<run>/hits.csv` | One row each time a resting order would have been traded against: the side, the price, how much traded |
| `settlements.csv` | How finished games settled (written by the scoring script) |
| `log.csv` | One line per run |
| `STATUS.md` | The latest run in words |

To add the runs up and apply the judge:

```bash
python scripts/us_rewards_score.py --settle
```

The system that would place such orders for real is `kht us-quote`
(`src/kht/trading/us_quoter.py`, `src/kht/trading/us_live.py`). It runs on
paper by default and has never been run against the exchange. What it
does, its limits and the steps before any real order are in
`docs/10_us_quoter.md`.

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

The third round (`05_third_round.md`). The first three lines fetch what the
earlier rounds left out; every universe is then built by
`scripts/at_the_time.py` from what a market had traded at the time:

```bash
python scripts/download_research_data.py meta --thinner   # markets that ended at 5,000 to 20,000 shares
python scripts/download_trades.py non_sports_thinner --shard 0/3 --max-pages 100   # and 1/3, 2/3
python scripts/download_trades.py short_lived && python scripts/download_trades.py short_lived_thin && python scripts/download_trades.py short_lived_thinner
```

```bash
python scripts/at_the_time.py big thin thinner   # the cached pieces every script below reads
python scripts/run_corrections.py                # the earlier rounds without the two hindsight filters
python scripts/run_sides.py                      # which side of the bet, on the two larger universes
python scripts/run_thinner.py                    # the six tests fixed in advance, on the smallest
python scripts/run_third_accounts.py             # the strategy as accounts
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
