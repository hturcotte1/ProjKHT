# Result tables and figures

Everything in `research/` is written by a script in `scripts/` and can be
regenerated. The prefix says where a table came from and how much weight it
carries.

| Prefix | Script | What it is | Weight |
|---|---|---|---|
| `c1_` … `c4_` | `run_confirmatory.py` | The pre-registered rules on the holdout and the newer sample; robustness, account simulation and tail for R1 and R1d | **The evidence** |
| `c5_` | `check_holdout_definition.py` | Every pre-registered rule under the holdout as run (scheduled end) and as first written (close date) | A check on the evidence |
| `s1_`, `s2_` | `run_confirmatory_sports.py` | The pre-registered sports rules | **The evidence** (negative) |
| `x_a…` | `run_exploratory.py --part A` | Momentum, reversal, round-trip trades, Yes vs No, resting-bid entry, breakdowns (non-sports) | Exploratory |
| `x_b…` | `run_exploratory.py --part B` | Sports: drift, momentum, tickets versus money | Exploratory |
| `d_` | `run_deployed_rules.py` | The exact rules the two paper accounts run | Not independent: tuned after the holdout was opened |
| `m_` | `fit_model.py` | Model segments and the walk-forward check | Model is for ranking only |
| `k_` | `run_capacity.py` | How much traded at in-range prices in each market the main rule bought, and what larger accounts would have made if limited to a share of it | Exploratory; rests on an assumption about market impact |
| `first_pass_biased/` | `run_research.py` | The first pass on a sample chosen by total volume | **Known to be biased**; kept because the comparison is a finding |

`*_output.txt` files are the full console output of each run.
`c2_trades_<rule>.csv` list every trade of every pre-registered rule, so any
number in the write-up can be recomputed by hand.

`figures/` holds the charts used in `docs/02_research_findings.md`, drawn by
`scripts/make_figures.py`.
