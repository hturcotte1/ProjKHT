"""T5: does the edge keep growing as markets get thinner? (docs/04_second_round.md, section 13)

Fixed before any of these markets was downloaded. Resolved news markets
(outside sports and crypto, a life of two days or more) that traded 5,000 to
20,000 shares, used once they have traded 5,000. The first round's rules
exactly as before, and the thin account's band:

    R1d          ask above 95c and at most 99c, legs included
    main rule    95-98c, stand-alone
    thin band    90-98c, stand-alone

each bought at the next taker-buy print within 3 days and held, with today's
fee, 3 to 60 days to the scheduled end, one trade per market.

Bar: R1d positive with |t| >= 3 (clustered by event). Prediction, not a bar:
a return at least as large as in the 20,000-100,000 markets. Reported with
it: how many dollars traded in range, because below some size there is
nothing to buy.

Four more tests were fixed in docs/05_third_round.md, section 3, while the
tapes were still downloading and before any had been opened:

    T5-Y   the leader: T5's own trades that bought the "Yes" side of a leg.
           Bar: positive with |t| >= 3 and fewer losses than the price
           implies, exact binomial p < 0.01.
    T5-L   long-dated "No": stand-alone, 90-98c, more than 60 and at most 180
           days to a scheduled end on or before 27 October 2026.
           Bar: positive with |t| >= 3 (150 trades or more).
    T5-N   which side: the thin band split by side. Prediction: "No" returns
           more than "Yes". Decision: drop the "Yes" side only if the sign
           holds here and the gap pooled with the two earlier universes has
           |t| >= 3.
    T5-TM  resting bids, exactly as TM in round two.
           Bar: positive with |t| >= 3 and above the ask version, |t| >= 2.
    T5-H   the house: stand-alone, "No" at 50-90c, 3-60 days.
           Bar: return per trade positive with |t| >= 3.

    python scripts/run_thinner.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_quiet_favourites as rq  # noqa: E402
import run_quiet_replication as rr  # noqa: E402
import run_thin_markets as tm  # noqa: E402

from kht.backtest.harvest import Rule, candidate_trades, prepare  # noqa: E402
from kht.data.download import load_meta  # noqa: E402
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes  # noqa: E402
from kht.research.sports import build_trades_table  # noqa: E402
from kht.research.stats import mean_cluster  # noqa: E402
from scipy import stats as sps  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
MIN_CUM = 5_000
SCHEDULED_BY = pd.Timestamp("2026-10-27").timestamp()     # T5-L: only markets whose scheduled end is behind us
BIG_PANEL = ROOT / "data" / "cache" / "panel_non_sports.parquet"
THIN_PANEL = ROOT / "data" / "cache" / "panel_thin.parquet"
# the same rules on the 20,000-100,000 markets, from qt_quiet_replication.csv and t_thin_trades.csv
THIN = {"R1d: 95-99c, legs included": (1.69, 9.01, 3135), "main rule: 95-98c, stand-alone": (1.96, 5.96, 1393),
        "thin band: 90-98c, stand-alone": (2.40, 5.47, 1744)}


def thinner_meta() -> pd.DataFrame:
    meta = load_meta("closed_thinner")
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    meta = meta[(meta["category"] != "sports") & (meta["category"] != "crypto") & (life >= 2) & resolved].copy()
    meta["closed_ts"] = meta["closed_ts"].fillna(meta["end_ts"])
    return meta[meta["closed_ts"].notna()]


def main() -> None:
    meta = thinner_meta()
    have = {p.stem for p in (ROOT / "data" / "trades").glob("*.parquet")}
    print(f"news markets that traded 5,000 to 20,000 shares: {len(meta):,}; tapes on disk: {int(meta['condition_id'].isin(have).sum()):,}")
    tr = build_trades_table(meta)
    s = prepare(add_taker_buy_pnl(by_side(period_quotes(tr, min_cum=MIN_CUM), meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    print(f"panel: {len(s):,} outcome-days in {s['market_id'].nunique():,} markets, {s['cluster'].nunique():,} events, "
          f"{pd.to_datetime(s.ts.min(), unit='s').date()} to {pd.to_datetime(s.ts.max(), unit='s').date()}")
    single = ~meta.set_index("market_id")["neg_risk"].reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    ask, dte = s["ask"].to_numpy(), s["days_to_end"].to_numpy()
    ok = (dte > 3) & (dte <= 60)

    rules = [("R1d: 95-99c, legs included", 0.95, 0.99, np.ones(len(s), bool)),
             ("main rule: 95-98c, stand-alone", 0.95, 0.98, single),
             ("thin band: 90-98c, stand-alone", 0.90, 0.98, single),
             ("90-95c, stand-alone", 0.90, 0.95, single),
             ("control: long shots 3-10c", 0.03, 0.10, np.ones(len(s), bool))]
    rows = []
    kept = {}
    for name, lo, hi, mask in rules:
        t = candidate_trades(s, Rule(lo, hi, 3, 60), signal=(ask > lo) & (ask <= hi) & ok & mask)
        t = t.join(tm.band_flow(tr, t, lo, hi, MIN_CUM), on="market_id")
        fee_rate = t["entry_fee"] / (t["entry_px"] * (1 - t["entry_px"]))
        t["cost_vwap"] = t["vwap"] + fee_rate * t["vwap"] * (1 - t["vwap"])
        t["ret_vwap"] = (t["proceeds"] - t["cost_vwap"]) / t["cost_vwap"]
        kept[name] = t
        a = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
        b = mean_cluster(t["ret_vwap"].to_numpy(), t["cluster"].to_numpy())
        q = t["usd_window"].quantile([0.10, 0.50, 0.90])
        rows.append({"rule": name, "trades": len(t), "events": int(t["cluster"].nunique()), "lost": int((t["won"] == 0).sum()),
                     "lost %": 100 * float((t["won"] == 0).mean()), "return a trade %": 100 * a.mean, "t_event": a.t,
                     "at the 3-day average %": 100 * b.mean, "t ": b.t, "in the 20-100k markets %": THIN.get(name, (np.nan,))[0],
                     "in-range $: 10th pct": q[0.10], "median": q[0.50], "90th pct": q[0.90],
                     "under $100 in range %": 100 * float((t["usd_window"] < 100).mean())})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "t5_thinner.csv", index=False)
    print("\n", res.round(2).to_string(index=False))
    r1d = kept["R1d: 95-99c, legs included"]
    r = mean_cluster(r1d["ret"].to_numpy(), r1d["cluster"].to_numpy())
    print("=" * 110)
    print(f"T5: R1d on markets with 5,000 to 20,000 shares: {len(r1d):,} trades in {r1d['cluster'].nunique():,} events, "
          f"{int((r1d['won'] == 0).sum())} lost; return per trade {100 * r.mean:+.2f}% (t = {r.t:.2f})")
    print(f"  bar (positive with |t| >= 3)  ->  {'PASSED' if r.mean > 0 and abs(r.t) >= 3 else 'NOT PASSED'}")
    print(f"  prediction (at least the +1.69% of the 20,000-100,000 markets)  ->  {'held' if 100 * r.mean >= 1.69 else 'did not hold'}")
    print("=" * 110)
    for name in ("main rule: 95-98c, stand-alone", "thin band: 90-98c, stand-alone"):
        t = kept[name]
        t["year"] = pd.to_datetime(t["entry_period"], unit="D").dt.year
        print(f"\n{name} by year of entry:")
        print(t.groupby("year").agg(trades=("won", "size"), lost=("won", lambda w: int((w == 0).sum())),
                                    avg_ret_pct=("ret", lambda x: 100 * x.mean())).round(2).to_string())
    third_round(meta, s, kept)


def line(t: pd.DataFrame) -> dict:
    if len(t) < 2:
        return {"trades": len(t)}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy())
    return {"trades": len(t), "events": int(t["cluster"].nunique()), "lost": int((t["won"] == 0).sum()),
            "lost %": 100 * float((t["won"] == 0).mean()), "avg cost": float(t["cost"].mean()),
            "return a trade %": 100 * r.mean, "t_event": r.t, "median hold, days": float(t["hold"].median())}


def yes_no(meta: pd.DataFrame) -> pd.Series:
    """Markets whose two outcomes are named Yes and No, by market id."""
    m = meta.set_index("market_id")
    return (m["outcome0"].str.strip().str.lower() == "yes") & (m["outcome1"].str.strip().str.lower() == "no")


def side_split(panel: pd.DataFrame, meta: pd.DataFrame, tag: str) -> pd.DataFrame:
    """The thin band's stand-alone trades in Yes/No markets of one universe, for the pooled T5-N gap."""
    yn = yes_no(meta).reindex(panel["market_id"]).fillna(False).to_numpy(dtype=bool)
    single = ~panel["neg_risk"].fillna(False).to_numpy(dtype=bool)
    ask, dte = panel["ask"].to_numpy(), panel["days_to_end"].to_numpy()
    t = candidate_trades(panel, Rule(0.90, 0.98, 3, 60), signal=(ask > 0.90) & (ask <= 0.98) & (dte > 3) & (dte <= 60) & single & yn)
    t["cluster"] = tag + t["cluster"].astype(str)          # event ids must not collide across universes
    t["universe"] = tag
    return t


def earlier_panel(path: Path, meta: pd.DataFrame, min_cum: float) -> pd.DataFrame:
    """The by-side panel of a universe read in an earlier round: from the cache if it is there, else rebuilt from the tapes."""
    if path.exists():
        p = pd.read_parquet(path)
    else:
        p = add_taker_buy_pnl(by_side(period_quotes(build_trades_table(meta), min_cum=min_cum), meta))
        path.parent.mkdir(parents=True, exist_ok=True)
        p.to_parquet(path, index=False)
    p = prepare(p)
    p = p[p["won"].notna()].reset_index(drop=True)
    p["series"] = p.groupby(["market_id", "side"], sort=False).ngroup()
    return p


def third_round(meta: pd.DataFrame, s: pd.DataFrame, kept: dict[str, pd.DataFrame]) -> None:
    """The four tests fixed in docs/05_third_round.md, section 3."""
    m = meta.set_index("market_id")
    yn_of = yes_no(meta)
    leg_of = m["neg_risk"].fillna(False).astype(bool)
    yn = yn_of.reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    single = ~leg_of.reindex(s["market_id"]).fillna(False).to_numpy(dtype=bool)
    ask, dte, side = s["ask"].to_numpy(), s["days_to_end"].to_numpy(), s["side"].to_numpy()
    rows = []
    print("\n" + "#" * 110 + "\nThird round (docs/05_third_round.md, section 3)\n" + "#" * 110)

    # ---- T5-Y and the other three kinds of trade inside R1d
    r1d = kept["R1d: 95-99c, legs included"].copy()
    r1d = r1d[yn_of.reindex(r1d["market_id"]).fillna(False).to_numpy(dtype=bool)]
    r1d["leg"] = leg_of.reindex(r1d["market_id"]).fillna(False).to_numpy(dtype=bool)
    kinds = {"stand-alone, No": r1d[~r1d["leg"] & (r1d["side"] == 1)], "stand-alone, Yes": r1d[~r1d["leg"] & (r1d["side"] == 0)],
             "leg, Yes (the leader)": r1d[r1d["leg"] & (r1d["side"] == 0)], "leg, No (an also-ran)": r1d[r1d["leg"] & (r1d["side"] == 1)]}
    for name, t in kinds.items():
        rows.append({"test": "inside R1d (95-99c, 3-60 days)", "group": name, **line(t)})
    lead = kinds["leg, Yes (the leader)"]
    if len(lead) >= 2:
        r = mean_cluster(lead["ret"].to_numpy(), lead["cluster"].to_numpy())
        k, n, be = int((lead["won"] == 0).sum()), len(lead), float(1 - lead["cost"].mean())
        p = float(sps.binom.cdf(k, n, be))
        ok = r.mean > 0 and abs(r.t) >= 3 and p < 0.01
        print(f"T5-Y, the leader: {n:,} trades in {lead['cluster'].nunique():,} events, {k} lost; return per trade {100 * r.mean:+.2f}% (t = {r.t:.2f})")
        print(f"  the price paid implies {100 * be:.2f}% lose; chance of {k} or fewer in {n:,} if that were true: {p:.5f}")
        print(f"  bar (positive with |t| >= 3, and that chance below 0.01)  ->  {'PASSED' if ok else 'NOT PASSED'}")
    else:
        print("T5-Y, the leader: no trades")

    # ---- T5-L: long-dated "No"
    sched = s["end_ts"].to_numpy() <= SCHEDULED_BY
    far = (dte > 60) & (dte <= 180)
    band = (ask > 0.90) & (ask <= 0.98)
    long_no = candidate_trades(s, Rule(0.90, 0.98, 60, 180), signal=band & far & single & yn & sched & (side == 1))
    long_yes = candidate_trades(s, Rule(0.90, 0.98, 60, 180), signal=band & far & single & yn & sched & (side == 0))
    for name, t in (("No", long_no), ("Yes", long_yes)):
        row = line(t)
        if len(t) >= 2:
            row["per 30 days held %"] = 100 * float(t["ret"].sum()) / max(float(t["hold"].clip(lower=1).sum()), 1.0) * 30
        rows.append({"test": "long-dated (90-98c, 60-180 days, stand-alone)", "group": name, **row})
    if len(long_no) >= 2:
        r = mean_cluster(long_no["ret"].to_numpy(), long_no["cluster"].to_numpy())
        verdict = "CANNOT SETTLE IT (fewer than 150 trades)" if len(long_no) < 150 else ("PASSED" if r.mean > 0 and abs(r.t) >= 3 else "NOT PASSED")
        print(f"\nT5-L, long-dated No: {len(long_no):,} trades in {long_no['cluster'].nunique():,} events, {int((long_no['won'] == 0).sum())} lost; "
              f"return per trade {100 * r.mean:+.2f}% (t = {r.t:.2f}), median hold {long_no['hold'].median():.0f} days")
        print(f"  bar (positive with |t| >= 3, on 150 trades or more)  ->  {verdict}")
    else:
        print("\nT5-L, long-dated No: no trades")

    # ---- T5-N: which side, here and pooled with the two universes already read
    here = side_split(s, meta, "t5:")
    for name, t in (("No", here[here["side"] == 1]), ("Yes", here[here["side"] == 0])):
        rows.append({"test": "thin band (90-98c, 3-60 days, stand-alone)", "group": name, **line(t)})
    print("\nT5-N, which side (thin band, stand-alone, Yes/No markets):")
    sign_ok = False
    if (here["side"] == 0).sum() >= 2 and (here["side"] == 1).sum() >= 2:
        d, t_d = rq.gap(here[here["side"] == 1], here[here["side"] == 0])
        sign_ok = d > 0
        print(f"  in these markets: No minus Yes {100 * d:+.2f} points (t = {t_d:.2f}); predicted sign {'held' if sign_ok else 'did not hold'}")
    big_meta, thin_meta = tm.big_meta(), rr.thin_meta()
    allt = pd.concat([here, side_split(earlier_panel(BIG_PANEL, big_meta, 100_000), big_meta, "big:"),
                      side_split(earlier_panel(THIN_PANEL, thin_meta, 20_000), thin_meta, "thin:")], ignore_index=True)
    d, t_d = rq.gap(allt[allt["side"] == 1], allt[allt["side"] == 0])
    print(f"  pooled over the three universes ({int((allt['side'] == 1).sum()):,} No and {int((allt['side'] == 0).sum()):,} Yes trades): "
          f"No minus Yes {100 * d:+.2f} points (t = {t_d:.2f})")
    print(f"  decision rule (sign holds here and pooled |t| >= 3)  ->  {'DROP THE YES SIDE' if sign_ok and d > 0 and abs(t_d) >= 3 else 'LEAVE THE ACCOUNTS ALONE'}")

    # ---- T5-TM: resting bids on the thin account's signals
    rng14, seasoned14 = rq.trailing_range(s, 14)
    calm = ~(seasoned14 & (rng14 > 0.15))
    sig = (ask > 0.90) & (ask <= 0.98) & (dte > 3) & (dte <= 60) & single & calm
    taker = candidate_trades(s, Rule(0.90, 0.98, 3, 60, entry="taker"), signal=sig)
    maker = candidate_trades(s, Rule(0.90, 0.98, 3, 60, entry="maker"), signal=sig)
    rows.append({"test": "thin account's signals (90-98c, calm)", "group": "at the ask", **line(taker)})
    rows.append({"test": "thin account's signals (90-98c, calm)", "group": "resting bid", **line(maker)})
    if len(maker) >= 2 and len(taker) >= 2:
        r = mean_cluster(maker["ret"].to_numpy(), maker["cluster"].to_numpy())
        d, t_d = rq.gap(maker, taker)
        ok = r.mean > 0 and abs(r.t) >= 3 and d > 0 and abs(t_d) >= 2
        print(f"\nT5-TM, resting bids: {len(maker):,} filled of {len(taker):,} bought at the ask ({100 * len(maker) / len(taker):.0f}%); "
              f"return per trade {100 * r.mean:+.2f}% (t = {r.t:.2f}); bid minus ask {100 * d:+.2f} points (t = {t_d:.2f})")
        print(f"  bar (positive with |t| >= 3; above the ask version with |t| >= 2)  ->  {'PASSED' if ok else 'NOT PASSED'}")

    # ---- T5-H: "No" as the favourite, below the near-certain band
    short = (dte > 3) & (dte <= 60) & single & yn
    house = candidate_trades(s, Rule(0.50, 0.90, 3, 60), signal=(ask > 0.50) & (ask <= 0.90) & short & (side == 1))
    rows.append({"test": "the house (No at 50-90c, 3-60 days, stand-alone)", "group": "all markets", **line(house)})
    if len(house) >= 2:
        r = mean_cluster(house["ret"].to_numpy(), house["cluster"].to_numpy())
        c = mean_cluster((house["proceeds"] - house["cost"]).to_numpy(), house["cluster"].to_numpy())
        print(f"\nT5-H, the house: {len(house):,} trades in {house['cluster'].nunique():,} events, {100 * house['won'].mean():.1f}% won at an average cost of "
              f"{100 * house['cost'].mean():.1f}c; {100 * c.mean:+.2f}c a share (t = {c.t:.2f}); return per trade {100 * r.mean:+.2f}% (t = {r.t:.2f})")
        print(f"  bar (return per trade positive with |t| >= 3)  ->  {'PASSED' if r.mean > 0 and abs(r.t) >= 3 else 'NOT PASSED'}")
        print(f"  prediction (at least the thin markets' +6.7c a share)  ->  {'held' if 100 * c.mean >= 6.7 else 'did not hold'}")
        behind = house[m["end_ts"].reindex(house["market_id"]).to_numpy() <= SCHEDULED_BY]
        rows.append({"test": "the house (No at 50-90c, 3-60 days, stand-alone)", "group": "scheduled end passed", **line(behind)})
        for name, g in (("3-20 days left", house[house["dte_at_signal"] <= 20]), ("20-60 days left", house[house["dte_at_signal"] > 20]),
                        ("paid 50-60c", house[house["entry_px"] <= 0.60]), ("paid 60-70c", house[(house["entry_px"] > 0.60) & (house["entry_px"] <= 0.70)]),
                        ("paid 70-80c", house[(house["entry_px"] > 0.70) & (house["entry_px"] <= 0.80)]), ("paid 80-90c", house[house["entry_px"] > 0.80])):
            rows.append({"test": "the house (No at 50-90c, 3-60 days, stand-alone)", "group": name, **line(g)})
        for c_, g in house.groupby("category"):
            rows.append({"test": "the house, by category", "group": c_, **line(g)})
        house = house.assign(half=pd.to_datetime(house["entry_period"], unit="D").dt.year.astype(str)
                             + np.where(pd.to_datetime(house["entry_period"], unit="D").dt.month <= 6, " H1", " H2"))
        for h, g in house.groupby("half"):
            rows.append({"test": "the house, by half-year of entry", "group": h, **line(g)})
    mirror = candidate_trades(s, Rule(0.10, 0.50, 3, 60), signal=(ask > 0.10) & (ask <= 0.50) & short & (side == 0))
    rows.append({"test": "the other side of the house (Yes at 10-50c)", "group": "all markets", **line(mirror)})

    # ---- reported without a bar: every price, each side
    grid = []
    for lo, hi in ((0.03, 0.10), (0.10, 0.20), (0.20, 0.35), (0.35, 0.50), (0.50, 0.65), (0.65, 0.80), (0.80, 0.90), (0.90, 0.95), (0.95, 0.98)):
        for sd, sn in ((1, "No"), (0, "Yes")):
            g = candidate_trades(s, Rule(lo, hi, 3, 60), signal=(ask > lo) & (ask <= hi) & short & (side == sd))
            if len(g) < 20:
                continue
            c = mean_cluster((g["proceeds"] - g["cost"]).to_numpy(), g["cluster"].to_numpy())
            grid.append({"paid": f"{100 * lo:.0f}-{100 * hi:.0f}c", "side": sn, "trades": len(g), "won %": 100 * float(g["won"].mean()),
                         "avg cost": float(g["cost"].mean()), "cents a share": 100 * c.mean, "t": c.t})
    grid = pd.DataFrame(grid)
    grid.to_csv(OUT / "t5_side_by_price.csv", index=False)
    print("\nEvery price, each side (stand-alone Yes/No markets, 3-60 days; no bar):\n", grid.round(2).to_string(index=False))

    res = pd.DataFrame(rows)
    res.to_csv(OUT / "t5_third_round.csv", index=False)
    print("\n", res.round(2).to_string(index=False))
    # reported without a bar: categories inside R1d
    cats = pd.DataFrame([{"category": c, **line(g)} for c, g in kept["R1d: 95-99c, legs included"].groupby("category")])
    print("\nR1d by category (no bar):\n", cats.round(2).to_string(index=False))


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
    with (OUT / "thinner_output.txt").open("w") as fh:
        sys.stdout = Tee(sys.__stdout__, fh)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__
