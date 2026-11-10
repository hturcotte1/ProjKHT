# Configuration

| File | What it is |
|---|---|
| `paper.json` | **The main paper account.** The one rule that passed its pre-registered test, slightly trimmed: in stand-alone yes/no markets, buy a contract whose ask is above 95¢ and at most 98¢, with 3–60 scheduled days left, that was also in that band 18 hours earlier; lift the ask; hold to resolution. |
| `paper_maker.json` | **An experiment, not a validated strategy.** The wider 90–98¢ band entered with a resting bid instead of lifting the ask. In the historical test this was better than the taker version but fell just short of the bar (t = 2.7 on the holdout), so it gets a paper account of its own to earn or lose its place on new data. |
| `model.json` | The fitted calibration line and per-segment shifts, written by `scripts/fit_model.py`. Used to rank candidates and to drop segments with no estimated edge. |

`strategy` keys are documented on `StrategyConfig` in
`src/kht/trading/strategy.py`; `risk` keys on `RiskLimits` in
`src/kht/trading/risk.py`.

Changing `"mode"` to `"live"` is not enough to trade real money; see
`docs/03_system.md`.
