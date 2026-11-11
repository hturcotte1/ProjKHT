# Result tables and figures

Everything in `research/` is written by a script in `scripts/` and can be
regenerated. The prefix says where a table came from and how much weight it
carries.

| Prefix | Script | What it is | Weight |
|---|---|---|---|
| `c1_` … `c4_` | `run_confirmatory.py` | The pre-registered rules on the holdout and the newer sample; robustness, account simulation and tail for R1 and R1d | **The evidence** |
| `c5_` | `check_holdout_definition.py` | Every pre-registered rule under the holdout as run (scheduled end) and as first written (close date) | A check on the evidence |
| `c6_` | `check_loss_bunching.py` | How the losing trades of the rule that passed were spread over events, weeks and months, against what chance would produce | Exploratory description of the evidence |
| `c7_` | `check_late_entry.py` | The same rules entered late: days or weeks after a contract first qualified, and on "switch-on" dates a week apart | Exploratory check on how the paper accounts and the forward-test log start |
| `q_` | `run_quiet_favourites.py` | Second round, track A: favourites that have not moved for one or two weeks against those that have. Rule and bar fixed in `docs/04_second_round.md` | A prediction made before looking, on data examined before for other questions |
| `qs_` | `run_quiet_replication.py` | Second round: the quiet rule Q on sports markets that are not single games, never read before | A replication on untouched data (**failed**) |
| `qt_` | `run_quiet_replication.py non_sports_thin` | Second round: the quiet rule and the first round's rules on 25,283 thinner news markets (20,000 to 100,000 shares), never read before | **Known to be biased**: the thin markets were chosen by final volume (see `cor_`). Kept because the comparison is the lesson |
| `tm_` | `run_thin_maker.py` | TM, fixed in advance: resting bids against paying the ask in the thinner markets; plus bidding first and paying the ask later (exploratory) | **Known to be biased**: the thin markets were chosen by final volume (see `cor_`). Kept because the comparison is the lesson |
| `t_` | `run_thin_markets.py` | How many dollars traded in range in the thinner markets, and accounts that add them to the main rule | **Known to be biased**: the thin markets were chosen by final volume (see `cor_`). Kept because the comparison is the lesson |
| `q_stops`, `q_price_path` | `check_stops_and_paths.py` | Stop-losses (they lower the return) and the price path of quiet favourites towards the deadline | Exploratory |
| `cor_` | `run_corrections.py` | Third round: the first round's rules and round two's thin-market rules, resting bids and accounts rerun without the two filters that needed hindsight (final volume; a life of two days) | **The corrected evidence** for everything `qt_`, `tm_` and `t_` claimed; the first round is unchanged |
| `s3_` | `run_sides.py` | Third round: the rule split by what was bought (stand-alone No or Yes, leader, also-ran), long-dated No, each side at every price, on the two larger universes built at the time | Exploratory; it chose the tests in `t5_` |
| `t5_` | `run_thinner.py` | Third round: six tests fixed in advance, on markets while they had traded 5,000 to 20,000 shares. Files ending `_as_fixed` are the same tests on the universe as first written, chosen with hindsight | **The evidence**: one decision rule met (No against Yes), five bars missed. `_as_fixed` is a measure of the flaw, not a result |
| `a3_` | `run_third_accounts.py` | Third round: the strategy as accounts (No only; the long-dated sleeve; both), each market at its earliest entry | Exploratory |
| `f_intl_`, `factory_intl_output` | `factory.py run-intl` | Fourth round, stage 1: 53,760 rules on polymarket.com, searched on markets ending before 2026 and judged on those ending after, with the bar set by placebo worlds | **The evidence** that the search finds one idea and only one |
| `f_us_`, `factory_us_*` | `factory.py confirm-us`, `run-us` | Fourth round, stages 2 and 2b: the survivors on Polymarket US, and the same search on Polymarket US alone. Files ending `_first_mapping`, `_with_end_prices` and `_ends_removed` are earlier versions of the US table, each superseded | **The evidence** (nothing confirmed). The superseded files are kept as the record of three errors in reading the price feed |
| `tv_`, `two_venues_output` | `two_venues.py` | Fourth round: Polymarket US against polymarket.com on the same questions, tests fixed in `docs/07_two_venues.md` before they ran | **The evidence** (failed) |
| `sp_`, `sports_us_output` | `sports_us.py` | Fourth round: moneylines on Polymarket US, 3,360 rules, the judge of `docs/06`, section 9 | **The evidence** |
| `usf_`, `us_forward_output` | `us_forward.py` | The forward tests on Polymarket US, scored from the recorder's snapshots: F1 (two exchanges), F2 (stand-alone "No"), the reward programmes over time. Rules fixed in `docs/06` section 8 and `docs/07` section 3 before any snapshot existed | **Forward evidence**; grows with every cycle |
| `usr_` | `us_rewards_score.py` | Paper orders before games on Polymarket US: reward by the published formula, simulated fills, and the judge of `docs/09`, section 5. Rules fixed before the first run | **Forward evidence** from a simulation; grows with every run |
| `ps_` | `run_position_size.py` | The account simulation at larger position sizes, for the main rule, the quiet rule and both | Analysis; chooses nothing |
| `cp_` | `run_crypto_price.py` | Second round, track C: the confirmed rule and the quiet rule on crypto price markets, discovery set | A replication on untouched data (not repeated) |
| `cy_` | `run_crypto_yardstick.py` | Second round, track C: an outside fair value for crypto price markets from the coin's price and volatility; includes one table marked as an artefact | Exploratory on the discovery set (negative) |
| `s1_`, `s2_` | `run_confirmatory_sports.py` | The pre-registered sports rules | **The evidence** (negative) |
| `x_a…` | `run_exploratory.py --part A` | Momentum, reversal, round-trip trades, Yes vs No, resting-bid entry, breakdowns (non-sports) | Exploratory |
| `x_a3c_` | `run_exploratory_resting.py` | The round-trip trades entered with a resting bid instead of at the ask | Exploratory |
| `x_b…` | `run_exploratory.py --part B` | Sports: drift, momentum, tickets versus money | Exploratory |
| `w_` | `run_wallet_skill.py` | Does a wallet's past skill persist, and can it be followed? Plan fixed in the script before it ran; one table is marked as unplanned | Exploratory (negative) |
| `d_` | `run_deployed_rules.py` | The exact rules the two paper accounts run | Not independent: tuned after the holdout was opened |
| `m_` | `fit_model.py` | Model segments and the walk-forward check | Model is for ranking only |
| `k_` | `run_capacity.py` | How much traded at in-range prices in each market the main rule bought, and what larger accounts would have made if limited to a share of it | Exploratory; rests on an assumption about market impact |
| `first_pass_biased/` | `run_research.py` | The first pass on a sample chosen by total volume | **Known to be biased**; kept because the comparison is a finding |

`*_output.txt` files are the full console output of each run.
`c2_trades_<rule>.csv` list every trade of every pre-registered rule, so any
number in the write-up can be recomputed by hand.

`figures/` holds the charts used in `docs/02_research_findings.md`, drawn by
`scripts/make_figures.py`.
