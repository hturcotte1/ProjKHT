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
| `qt_` | `run_quiet_replication.py non_sports_thin` | Second round: the quiet rule and the first round's rules on 25,283 thinner news markets (20,000 to 100,000 shares), never read before | **The evidence**: the quiet rule does not pass; the first round's rules repeat (t 6.0 and 9.0) |
| `tm_` | `run_thin_maker.py` | TM, fixed in advance: resting bids against paying the ask in the thinner markets; plus bidding first and paying the ask later (exploratory) | **The evidence** for the bid (passed); the combination is exploratory |
| `t_` | `run_thin_markets.py` | How many dollars traded in range in the thinner markets, and accounts that add them to the main rule | Exploratory; rests on an assumption about market impact |
| `q_stops`, `q_price_path` | `check_stops_and_paths.py` | Stop-losses (they lower the return) and the price path of quiet favourites towards the deadline | Exploratory |
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
