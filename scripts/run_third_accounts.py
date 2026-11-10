"""Accounts for the strategy as it stands after the third round (docs/05_third_round.md).

On the corrected universes (scripts/at_the_time.py), with positions limited
to a tenth of what takers bought in range and priced at the three-day
average, as in every account simulation since the first round:

    today        the main paper account: big markets, 95-98c, 3-60 days, either side
    no only      the same, "No" side only (the decision T5-N made)
    + long       plus "No" at 90-98c with 60 to 180 days to run, in markets with
                 20,000 shares or more at the time
    + thin       plus 95-98c "No" in markets with 20,000 to 100,000 shares

The long-dated trades use every market, not only those whose scheduled end
has passed: the account lives through time and cannot use that filter, and
leaving it out leans against the result (recent markets are in the sample
only if they closed early, which for a "No" mostly means it lost).

Exploratory: the long-dated sleeve did not pass its test in the thinnest
markets (T5-L, t = 2.7) and rests on exploration in the two larger universes.

    python scripts/run_third_accounts.py
"""

from __future__ import annotations

import gc
import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import at_the_time as att  # noqa: E402
import run_thin_markets as tm  # noqa: E402

from kht.backtest.harvest import Rule, candidate_trades, prepare  # noqa: E402
from kht.research.stats import mean_cluster  # noqa: E402
from kht.trading.universe import is_operational_tag  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 200)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"


def lists_for(label: str, lo_cum: int, hi_cum: int, only: tuple[str, ...] | None) -> dict[str, pd.DataFrame]:
    meta, tr, p = att.panel(lo_cum, hi_cum, only)
    s = prepare(p)
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    del p
    m = meta.set_index("market_id")
    yn = ((m["outcome0"].str.strip().str.lower() == "yes") & (m["outcome1"].str.strip().str.lower() == "no")).reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    single = ~s["neg_risk"].fillna(False).to_numpy(dtype=bool)
    ask, dte, side = s["ask"].to_numpy(), s["days_to_end"].to_numpy(), s["side"].to_numpy()
    short, far, no = (dte > 3) & (dte <= 60) & single, (dte > 60) & (dte <= 180) & single, yn & (side == 1)
    tag_lists = m["tags"].fillna("").str.split("|")
    counts = tag_lists.explode().value_counts()
    theme_set = {x for x in counts[(counts >= 2) & (counts <= max(2, 0.10 * len(meta)))].index if x and not is_operational_tag(x)}
    themes_of = tag_lists.map(lambda tags: tuple(sorted(set(tags) & theme_set)))
    lists = {}
    for name, lo, hi, d0, d1, mask in (("tight, either side", 0.95, 0.98, 3, 60, short), ("tight, No", 0.95, 0.98, 3, 60, short & no),
                                       ("long No", 0.90, 0.98, 60, 180, far & no), ("long No, 95-98c", 0.95, 0.98, 60, 180, far & no)):
        t = candidate_trades(s, Rule(lo, hi, d0, d1), signal=(ask > lo) & (ask <= hi) & mask)
        t = t.join(tm.band_flow(tr, t, lo, hi, lo_cum), on="market_id")
        fee_rate = t["entry_fee"] / (t["entry_px"] * (1 - t["entry_px"]))
        t["cost_vwap"] = t["vwap"] + fee_rate * t["vwap"] * (1 - t["vwap"])
        t["ret_vwap"] = (t["proceeds"] - t["cost_vwap"]) / t["cost_vwap"]
        t["themes"] = t["market_id"].map(themes_of)
        t["universe"] = label
        lists[f"{label} {name}"] = t
    del tr, s
    gc.collect()
    return lists


def main() -> None:
    lists = lists_for("big", 100_000, att.TOP, ("big",))
    lists.update(lists_for("thin", 20_000, 100_000, None))
    desc = pd.DataFrame([tm.describe(k, v) for k, v in lists.items()])
    desc.to_csv(OUT / "a3_trades.csv", index=False)
    print("the trade lists (first print as in every backtest; 3-day average as a larger order would pay)\n")
    print(desc.round(2).to_string(index=False))

    combos = {
        "today: big, 95-98c, either side": ["big tight, either side"],
        "no only: big, 95-98c, No": ["big tight, No"],
        "no only + long No in big markets": ["big tight, No", "big long No"],
        "no only + long No, 20,000 shares or more": ["big tight, No", "big long No", "thin long No"],
        "no only + long No (20,000 or more) + thin 95-98c No": ["big tight, No", "thin tight, No", "big long No", "thin long No"],
        "long No alone, 20,000 shares or more": ["big long No", "thin long No"],
    }
    rows, curves = [], {}
    for name, keys in combos.items():
        for bankroll in (1_000, 5_000, 25_000):
            for frac in (0.02, 0.03, 0.04, 0.05):
                row, eq = att.account([lists[k] for k in keys], bankroll, frac)
                rows.append({"account": name, **row})
                if bankroll == 1_000 and frac == 0.03:
                    curves[name] = eq.set_index("period")["equity"]
    acc = pd.DataFrame(rows)
    acc.to_csv(OUT / "a3_accounts.csv", index=False)
    pd.DataFrame(curves).to_csv(OUT / "a3_equity_1000_3pct.csv")
    print(f"\naccounts: positions at most {tm.PARTICIPATION:.0%} of the in-range flow, priced at the 3-day average, one position per event, "
          "four per story, at most 80% invested\n")
    print(acc.round(1).to_string(index=False))

    # by calendar year, for the account the paper trader now runs as two accounts
    name = "no only + long No, 20,000 shares or more"
    eq = curves[name]
    year = pd.to_datetime(eq.index, unit="D").year
    by_year = eq.groupby(year).agg(["first", "last"])
    by_year["return %"] = 100 * (by_year["last"] / by_year["first"] - 1)
    print(f"\n{name}, $1,000 at 3% a position, by calendar year:\n", by_year.round(1).to_string())

    # how the long-dated list is spread: losses by quarter of entry
    long_all = pd.concat([lists["big long No"], lists["thin long No"]], ignore_index=True).drop_duplicates("market_id")
    q = pd.to_datetime(long_all["entry_period"], unit="D").dt.to_period("Q")
    spread = long_all.groupby(q).agg(trades=("won", "size"), lost=("won", lambda w: int((w == 0).sum())), ret=("ret", lambda x: 100 * x.mean()))
    print("\nlong-dated No (20,000 shares or more), by quarter of entry:\n", spread.round(2).to_string())
    r = mean_cluster(long_all["ret"].to_numpy(), long_all["cluster"].to_numpy())
    print(f"all: {len(long_all):,} trades, {int((long_all['won'] == 0).sum())} lost, {100 * r.mean:+.2f}% a trade (t = {r.t:.2f}), median hold {long_all['hold'].median():.0f} days")


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
    with (OUT / "third_accounts_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
