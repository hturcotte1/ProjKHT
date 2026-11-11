# Configuration

| File | What it is |
|---|---|
| `paper.json` | **The main paper account.** The one rule that passed its pre-registered test, slightly trimmed: in stand-alone yes/no markets that have traded 100,000 shares, buy a "No" whose ask is above 95¢ and at most 98¢, with 3–60 scheduled days left, that was also in that band 18 hours earlier; lift the ask; hold to resolution. |
| `paper_maker.json` | **An experiment, not a validated strategy.** The wider 90–98¢ band entered with a resting bid instead of lifting the ask. In the historical test this was better than the taker version but fell just short of the bar (t = 2.7 on the holdout), so it gets a paper account of its own to earn or lose its place on new data. |
| `paper_thin.json` | **Weakly supported.** The main rule in markets that have traded 20,000 to 100,000 shares so far. Measured without hindsight it earns about what it does in big markets (+1.1% a trade, t = 3.4), and less at the prices a larger order would pay. |
| `paper_long.json` | **Exploratory.** "No" at 90–98¢ with 60 to 180 days to run, in markets with 20,000 shares or more, entered with a resting bid for three days and then at the ask. It earned 4–5% a trade in the two larger universes (t = 6 and 10), which were explored, not tested; in the thinnest markets, where it was tested, it fell short (t = 2.7). |
| `us_quoter.json` | **Polymarket US, orders before games.** The settings of `kht us-quote` (`docs/10_us_quoter.md`): 100 contracts a side, up to 20 games, at most $1,200 at risk, stop at $150 lost in a day. On paper unless live trading is switched on in the environment. |
| `model.json` | The fitted calibration line and per-segment shifts, written by `scripts/fit_model.py`. Used to rank candidates and to drop segments with no estimated edge. |

Since the third round every account buys the "No" side only
(`no_side_only`): at the same near-certain price "No" earned 3.6 points a
trade more than "Yes" across three universes (t = 4.4,
`docs/05_third_round.md`). The "Yes" side is still logged.

`strategy` keys are documented on `StrategyConfig` in
`src/kht/trading/strategy.py`; `risk` keys on `RiskLimits` in
`src/kht/trading/risk.py`.

Changing `"mode"` to `"live"` is not enough to trade real money; see
`docs/03_system.md`.
