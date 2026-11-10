"""What would larger positions have earned, and risked?

The paper account stakes 2% of its bankroll on a position and leaves about
two-thirds of its money idle. This repeats the account simulation at larger
stakes for three trade lists on the first round's panel, all three years:

  * the main account's rule as configured (95-98c, stand-alone);
  * the quiet-favourite rule Q of the second round (90-98c, traded range of 3c
    or less over 7 days);
  * both together, quiet contracts taken first.

Caps scale with the stake: one position per event, four positions per story,
at most 80% of the account invested. It chooses nothing: position size is the
account owner's decision, and the quiet rule has not been confirmed on new
data. The losses in these three years are the only losses the simulation
knows about.

    python scripts/run_position_size.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_quiet_favourites as rq  # noqa: E402

from kht.backtest.harvest import Capital, Rule, candidate_trades, run_portfolio  # noqa: E402
from kht.trading.universe import is_operational_tag  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
BANKROLL = 1_000.0


def main() -> None:
    meta, s = rq.load()
    single = ~meta.set_index("market_id")["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    ask, dte = s["ask"].to_numpy(), s["days_to_end"].to_numpy()
    dte_ok = (dte > 3) & (dte <= 60)
    rng7, seasoned7 = rq.trailing_range(s, 7)
    quiet = seasoned7 & (rng7 <= 0.03 + 1e-9)

    tag_lists = meta.set_index("market_id")["tags"].fillna("").str.split("|")
    counts = tag_lists.explode().value_counts()
    theme_set = {t for t in counts[(counts >= 2) & (counts <= max(2, 0.10 * len(meta)))].index if t and not is_operational_tag(t)}
    themes_of = tag_lists.map(lambda tags: tuple(sorted(set(tags) & theme_set)))

    def trades(rule: Rule, signal: np.ndarray) -> pd.DataFrame:
        t = candidate_trades(s, rule, signal=signal)
        t["themes"] = t["market_id"].map(themes_of)
        return t

    main_rule = trades(Rule(0.95, 0.98, 3, 60), (ask > 0.95) & (ask <= 0.98) & dte_ok & single)
    q_rule = trades(Rule(0.90, 0.98, 3, 60), (ask > 0.90) & (ask <= 0.98) & dte_ok & single & quiet)
    # together: a market bought by the quiet rule is not bought again; quiet trades go first on the day
    rest = main_rule[~main_rule["market_id"].isin(q_rule["market_id"])]
    both = (pd.concat([q_rule.assign(first=0), rest.assign(first=1)], ignore_index=True)
              .sort_values(["entry_period", "first", "market_id"]).drop(columns="first").reset_index(drop=True))
    lists = {"main rule (95-98c)": main_rule, "quiet rule Q (90-98c, not yet confirmed)": q_rule, "both, quiet first": both}
    for name, t in lists.items():
        print(f"{name}: {len(t):,} candidate trades, {int((t['won'] == 0).sum())} lost, average return {100 * t['ret'].mean():+.2f}%")

    rows = []
    for name, t in lists.items():
        for frac in (0.02, 0.03, 0.05, 0.075, 0.10):
            stake = BANKROLL * frac
            for story_cap, label in ((4 * stake, "four positions a story"), (None, "no cap on a story")):
                r = run_portfolio(t, Capital(bankroll=BANKROLL, stake=stake, max_event=stake, max_theme=story_cap, max_exposure_frac=0.8))
                tk, eq = r.trades, r.equity
                monthly = eq.assign(month=pd.to_datetime(eq["period"], unit="D").dt.to_period("M")).groupby("month")["equity"].last().pct_change()
                rows.append({"trades": name, "stake": f"{100 * frac:g}%", "story cap": label, "taken": r.stats["trades"],
                             "losers taken": int((tk["pnl"] < -0.5 * tk["stake"]).sum()), "per year %": 100 * r.stats["cagr"],
                             "total %": 100 * r.stats["total_return"], "worst drawdown %": 100 * r.stats["max_drawdown"],
                             "worst month %": 100 * float(monthly.min()), "losing months": int((monthly < 0).sum()),
                             "months": int(monthly.notna().sum()), "money in use %": 100 * r.stats["avg_utilisation"],
                             "largest single loss $": float(tk["pnl"].min())})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "ps_position_size.csv", index=False)
    for name in lists:
        print(f"\n{name}, $1,000 account, all three years:")
        print(res[res["trades"] == name].drop(columns="trades").round(1).to_string(index=False))


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for st in self.streams:
            st.write(text)

    def flush(self):
        for st in self.streams:
            st.flush()


if __name__ == "__main__":
    with (OUT / "position_size_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
