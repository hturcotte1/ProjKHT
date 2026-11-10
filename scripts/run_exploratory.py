"""Exploratory analyses, run after the confirmatory tests.

Everything here is hypothesis-generating: many cuts of the same data, no
pre-registration. The write-up labels these results as such.

    A  non-sports markets (daily panel rebuilt from the tape)
       A1 momentum / reversal of the daily mid          (thesis test, H1)
       A2 response to large one-day moves               (thesis test, H2)
       A3 the same ideas as actual round-trip trades with costs
       A4 Yes versus No                                 (H4)
       A5 resting-order (maker) entry for R1
       A6 where R1's edge concentrates
    B  sports game-winner markets (pre-game tape)
       B1 does the favourite drift into the start?      (H5)
       B2 does the early move continue, and is it right?
       B3 tickets versus money: does public flow predict the move or the result?

Usage: python scripts/run_exploratory.py [--out reports/research] [--part A|B] [--dry-run]
"""

from __future__ import annotations

import argparse
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from kht.backtest.harvest import Rule, candidate_trades, prepare
from kht.data.download import load_meta
from kht.research import hypotheses as H
from kht.research.dataset import make_dataset
from kht.research.quotes import add_taker_buy_pnl, by_side, period_quotes, tape_mids
from kht.research.sports import build_pregame_trades, build_trades_table, game_features
from kht.research.stats import mean_cluster, ols_cluster

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_rows", 300)

RELIABLE_START = {"nfl", "nba", "mlb", "nhl", "cfb", "ncaa-basketball", "wnba", "soccer", "ufc"}


def section(title: str) -> None:
    print("\n" + "=" * 110 + f"\n{title}\n" + "=" * 110, flush=True)


def rstats(t: pd.DataFrame, label: str) -> dict:
    if len(t) < 20:
        return {"rule": label, "trades": len(t)}
    r = mean_cluster(t["ret"].to_numpy(), t["cluster"].to_numpy(), t["entry_period"].to_numpy())
    return {"rule": label, "trades": len(t), "events": int(t["cluster"].nunique()),
            "win%": 100 * float((t["pnl_ps"] > 0).mean()), "avg_entry": float(t["entry_px"].mean()),
            "avg_pnl_c": 100 * float(t["pnl_ps"].mean()), "avg_ret%": 100 * r.mean, "t": r.t,
            "med_hold_d": float(t["hold"].median())}


def non_sports(meta: pd.DataFrame) -> pd.DataFrame:
    life = (meta["closed_ts"].fillna(meta["end_ts"]) - meta["start_ts"]) / 86_400
    resolved = meta["winner"].notna() | (meta["final0"] == 0.5)
    return meta[(~meta["category"].isin(["sports", "crypto"])) & (life >= 2) & resolved].copy()


# =========================================================================== A
def part_a(out: Path, dry: bool) -> None:
    meta = non_sports(load_meta("closed"))
    if dry:
        meta = meta[meta["closed_ts"] >= pd.Timestamp("2026-06-08", tz="UTC").timestamp()]
    tr = build_trades_table(meta)
    q = period_quotes(tr)
    # when each market first satisfied the no-hindsight rule (used for the 3-hour panel below)
    cross_ts = tr.loc[tr["cum_before"] >= 100_000].groupby("market_id")["ts"].min()
    del tr
    print(f"non-sports: {q['market_id'].nunique():,} markets, {len(q):,} market-days")

    section("A1. Momentum / reversal of the daily mid (tape-derived, no-hindsight universe)")
    d, _ = make_dataset(tape_mids(q), meta, "1d")
    r = H.h1_momentum(d)
    r.to_csv(out / "x_a1_momentum_daily.csv", index=False)
    order = list(d.attrs["horizons"])
    a = r[r.group == "all"]
    print("slope of next change on past change (entry one bar after the signal)\n",
          a.pivot(index="past", columns="next", values="beta").loc[order, order].round(4))
    print("t-statistics\n", a.pivot(index="past", columns="next", values="t").loc[order, order].round(2))
    print("past 1d -> next 1d by category\n",
          r[(r.past == "1d") & (r.next == "1d")][["group", "beta", "t", "n", "clusters"]].round(4).to_string(index=False))
    half = d["ts"] <= d["ts"].median()
    for label, part in (("earlier half", d[half]), ("later half", d[~half])):
        part.attrs = d.attrs
        rh = H.h1_momentum(part, by_category=False)
        print(f"{label}: t\n", rh.pivot(index="past", columns="next", values="t").loc[order, order].round(2))

    section("A2. After a one-day move of a given size: continuation (+) or give-back (-), in cents")
    j = H.h2_jump_response(d, "1d", ["1d", "3d", "7d"])
    j.to_csv(out / "x_a2_jump_response.csv", index=False)
    lv = [str(c) for c in pd.IntervalIndex.from_breaks(H.JUMP_BINS)]
    print((100 * j.pivot(index="abs_move", columns="next", values="cont")).reindex(lv).round(3))
    print("t\n", j.pivot(index="abs_move", columns="next", values="t").reindex(lv).round(2))
    print("n\n", j.pivot(index="abs_move", columns="next", values="n").reindex(lv))

    section("A2b. Finer grain: quoted 3-hour mids (July-November 2026 only), same universe rule")
    try:
        from kht.data.download import load_price_panel

        px = load_price_panel("3h")
        px = px[px["market_id"].isin(cross_ts.index)]
        px = px[px["ts"] >= px["market_id"].map(cross_ts)]
        d3, _ = make_dataset(px, meta, "3h")
        r3 = H.h1_momentum(d3, by_category=False)
        r3.to_csv(out / "x_a2b_momentum_3h.csv", index=False)
        o3 = list(d3.attrs["horizons"])
        print(f"{d3['market_id'].nunique():,} markets, {len(d3):,} three-hour bars")
        print("slope\n", r3.pivot(index="past", columns="next", values="beta").loc[o3, o3].round(4))
        print("t\n", r3.pivot(index="past", columns="next", values="t").loc[o3, o3].round(2))
        j3 = H.h2_jump_response(d3, "3h", ["3h", "12h", "1d", "3d"])
        j3.to_csv(out / "x_a2b_jump_response_3h.csv", index=False)
        print("after a 3-hour move: continuation in cents\n",
              (100 * j3.pivot(index="abs_move", columns="next", values="cont")).reindex(lv).round(3))
        print("t\n", j3.pivot(index="abs_move", columns="next", values="t").reindex(lv).round(2))
    except FileNotFoundError as exc:
        print("skipped:", exc)

    section("A2c. Day-of-week pattern in the favoured side's daily change (cents)")
    cal = H.h6_calendar(d, "1d")
    cal = cal[cal["dim"] == "weekday"]
    cal.to_csv(out / "x_a2c_weekday.csv", index=False)
    print(cal.assign(mean_h1=100 * cal["mean_h1"], mean_h2=100 * cal["mean_h2"]).round(3).to_string(index=False))

    section("A3. The same ideas as real round trips: buy at the ask, sell at the bid, fees both ways")
    s = prepare(add_taker_buy_pnl(by_side(q, meta)))
    s = s[s["won"].notna()].reset_index(drop=True)
    s["series"] = s.groupby(["market_id", "side"], sort=False).ngroup()
    mid = np.where(s["ask"].notna() & s["bid"].notna() & ((s["ask"] - s["bid"]).between(-0.005, 0.10)),
                   0.5 * (s["ask"] + s["bid"]), s["last"])
    s["mid"] = mid
    g = s.groupby("series", sort=False)
    prev_mid, prev_period = g["mid"].shift(1), g["period"].shift(1)
    chg = (s["mid"] - prev_mid).where((s["period"] - prev_period) <= 2)
    s["chg_1d"] = chg
    rows = []
    band = dict(ask_lo=0.10, ask_hi=0.90)
    for thr in (0.05, 0.10, 0.20):
        for hold in (1, 3, 7):
            drop = (s["chg_1d"] <= -thr).to_numpy()
            rise = (s["chg_1d"] >= thr).to_numpy()
            t = candidate_trades(s, Rule(**band, hold_periods=hold, reentry=True), signal=drop)
            rows.append(rstats(t, f"buy what fell >= {int(100 * thr)}c, hold {hold}d"))
            t = candidate_trades(s, Rule(**band, hold_periods=hold, reentry=True), signal=rise)
            rows.append(rstats(t, f"buy what rose >= {int(100 * thr)}c, hold {hold}d"))
    base = candidate_trades(s, Rule(**band, hold_periods=3, reentry=True),
                            signal=(s["chg_1d"].abs() < 0.01).to_numpy() & (s["period"].to_numpy() % 7 == 0))
    rows.append(rstats(base, "benchmark: no move, hold 3d (cost of a round trip)"))
    a3 = pd.DataFrame(rows)
    a3.to_csv(out / "x_a3_roundtrip_trades.csv", index=False)
    print(a3.round(2).to_string(index=False))

    # the same trades where a round trip is cheapest: geopolitics markets carry no fee
    geo = (s["category"] == "geopolitics").to_numpy()
    rows = []
    for thr in (0.10, 0.20):
        for hold in (1, 3):
            for label, sig in (("fell", s["chg_1d"] <= -thr), ("rose", s["chg_1d"] >= thr)):
                t = candidate_trades(s, Rule(**band, hold_periods=hold, reentry=True), signal=sig.to_numpy() & geo)
                rows.append(rstats(t, f"fee-free only: buy what {label} >= {int(100 * thr)}c, hold {hold}d"))
    t = candidate_trades(s, Rule(**band, hold_periods=3, reentry=True),
                         signal=(s["chg_1d"].abs() < 0.01).to_numpy() & (s["period"].to_numpy() % 7 == 0) & geo)
    rows.append(rstats(t, "fee-free only: benchmark, no move, hold 3d"))
    a3b = pd.DataFrame(rows)
    a3b.to_csv(out / "x_a3b_roundtrip_fee_free.csv", index=False)
    print("\n", a3b.round(2).to_string(index=False))

    section("A4. Yes versus No at the same price (buy at the ask, hold to resolution, net of fees)")
    yn = s.merge(meta[["market_id", "outcome0"]], on="market_id", how="left")
    yn = yn[(yn["outcome0"] == "Yes") & yn["ask"].notna() & (yn["days_to_close"] > 0)]
    yn["which"] = np.where(yn["side"] == 0, "Yes", "No")
    rows = []
    for (lvl, which), gg in yn.groupby([pd.cut(yn["ask"], [0, 0.1, 0.3, 0.5, 0.7, 0.9, 0.97, 1.0]), "which"], observed=True):
        if len(gg) < 300:
            continue
        rr = mean_cluster(gg["net_ps"].to_numpy(), gg["cluster"].to_numpy(), gg["day"].to_numpy())
        rows.append({"ask": str(lvl), "side": which, "n": len(gg), "events": int(gg["cluster"].nunique()),
                     "win%": 100 * gg["won"].mean(), "avg_ask": gg["ask"].mean(), "net_c": 100 * rr.mean, "t": rr.t})
    a4 = pd.DataFrame(rows)
    a4.to_csv(out / "x_a4_yes_no.csv", index=False)
    print(a4.round(2).to_string(index=False))

    section("A5. R1 with a resting bid instead of lifting the ask")
    rows = []
    for label, rule in (("R1 taker (as pre-registered)", Rule(0.90, 0.97, 3, 60)),
                        ("R1 maker: bid at the signal bar's bid, 3 days", Rule(0.90, 0.97, 3, 60, entry="maker")),
                        ("R1 maker, 7 days", Rule(0.90, 0.97, 3, 60, entry="maker", max_wait=7)),
                        ("R1c taker 80-97c", Rule(0.80, 0.97, 3, 60)),
                        ("R1c maker 80-97c, 3 days", Rule(0.80, 0.97, 3, 60, entry="maker"))):
        rows.append(rstats(candidate_trades(s, rule), label))
    a5 = pd.DataFrame(rows)
    a5.to_csv(out / "x_a5_maker_entry.csv", index=False)
    print(a5.round(2).to_string(index=False))

    section("A6. Where R1's edge concentrates (all data; exploratory)")
    r1 = candidate_trades(s, Rule(0.90, 0.97, 3, 60))
    info = meta.set_index("market_id")
    r1["neg_risk"] = info["neg_risk"].reindex(r1["market_id"]).to_numpy()
    r1["age_days"] = (r1["entry_period"] * 86_400 - info["start_ts"].reindex(r1["market_id"]).to_numpy()) / 86_400
    r1["deadline"] = info["question"].reindex(r1["market_id"]).str.contains(H.DEADLINE_RE, case=False, regex=True, na=False).to_numpy()
    r1["outcome_side"] = np.where(r1["side"] == 0, "first-listed", "second-listed")
    r1["age_bin"] = pd.cut(r1["age_days"], [-1, 7, 30, 90, 1e5])
    r1["dte_bin"] = pd.cut(r1["dte_at_signal"], [3, 7, 14, 30, 60])
    r1["px_bin"] = pd.cut(r1["entry_px"], [0.90, 0.93, 0.95, 0.975])
    r1["year"] = pd.to_datetime(r1["entry_period"] * 86_400, unit="s").dt.year
    rows = []
    for dim in ("category", "neg_risk", "deadline", "outcome_side", "age_bin", "dte_bin", "px_bin", "year"):
        for level, gg in r1.groupby(dim, observed=True):
            rows.append({"dimension": dim, "level": str(level), **{k: v for k, v in rstats(gg, "").items() if k != "rule"}})
    a6 = pd.DataFrame(rows)
    a6.to_csv(out / "x_a6_r1_breakdowns_all.csv", index=False)
    print(a6.round(2).to_string(index=False))
    r1.to_csv(out / "x_r1_trades_all.csv", index=False)


# =========================================================================== B
def part_b(out: Path, dry: bool) -> None:
    meta = load_meta("closed")
    ml = meta[(meta["category"] == "sports") & (meta["sports_type"] == "moneyline") & meta["game_start_ts"].notna()]
    if dry:
        ml = ml[ml["game_start_ts"] >= pd.Timestamp("2026-09-22", tz="UTC").timestamp()]
    tr = build_pregame_trades(ml)
    f = game_features(tr, ml)
    c = f[f["clean"] & f["payoff"].notna()].copy()
    c["reliable"] = c["league"].isin(RELIABLE_START)
    print(f"sports: {len(f):,} games with tapes, {len(c):,} in the no-hindsight sample "
          f"({int(c['reliable'].sum()):,} in leagues with reliable start times)")
    c.to_parquet(out / "x_sports_games.parquet", index=False)

    section("B1. Does the favourite's price drift into the start? (mid proxies from the tape, cents)")
    rows = []
    for name, g in (("all leagues", c), ("reliable start times", c[c["reliable"]])):
        for h in (72, 48, 24, 12, 6, 3, 1):
            x = g.dropna(subset=[f"mid_{h}h", "mid_0h"])
            x = x[x[f"mid_{h}h"].between(0.05, 0.95)]
            fav = np.where(x[f"mid_{h}h"] >= 0.5, 1.0, -1.0)
            mv = fav * (x["mid_0h"] - x[f"mid_{h}h"])
            r = mean_cluster(mv.to_numpy(), x["cluster"].to_numpy(), x["day"].to_numpy())
            rows.append({"sample": name, "window": f"T-{h}h -> start", "fav_move_c": 100 * r.mean, "t": r.t, "n": r.n,
                         "sd_c": 100 * float(np.std(mv))})
    b1 = pd.DataFrame(rows)
    b1.to_csv(out / "x_b1_favourite_drift.csv", index=False)
    print(b1.round(3).to_string(index=False))

    section("B2. Does the early move continue, and do results confirm it?")
    rows = []
    for name, g in (("all leagues", c), ("reliable start times", c[c["reliable"]])):
        for early, ref in ((72, 24), (24, 6), (6, 1)):
            x = g.dropna(subset=[f"mid_{early}h", f"mid_{ref}h", "mid_0h"])
            x = x[x[f"mid_{ref}h"].between(0.05, 0.95)]
            em = x[f"mid_{ref}h"] - x[f"mid_{early}h"]
            lm = x["mid_0h"] - x[f"mid_{ref}h"]
            r = ols_cluster(lm.to_numpy(), em.to_numpy(), x["cluster"].to_numpy(), x["day"].to_numpy(), names=["early"])
            rows.append({"sample": name, "test": f"late move (T-{ref}h..start) on early move (T-{early}h..T-{ref}h)",
                         "beta": r.beta[1], "t": r.t[1], "n": r.n})
            sur = x["payoff"] - x["mid_0h"]
            tm = x["mid_0h"] - x[f"mid_{early}h"]
            r = ols_cluster(sur.to_numpy(), tm.to_numpy(), x["cluster"].to_numpy(), x["day"].to_numpy(), names=["move"])
            rows.append({"sample": name, "test": f"result minus closing price on the move since T-{early}h",
                         "beta": r.beta[1], "t": r.t[1], "n": r.n})
    b2 = pd.DataFrame(rows)
    b2.to_csv(out / "x_b2_momentum_confirmation.csv", index=False)
    print(b2.round(4).to_string(index=False))

    section("B3. Tickets versus money in the 24h-6h window: what do they predict?")
    x = c.dropna(subset=["mid_6h", "mid_0h", "tickets0_small_24_6", "net_big_usd_24_6", "usd_24_6"]).copy()
    x = x[x["mid_6h"].between(0.05, 0.95) & (x["n_small_24_6"] >= 10)]
    x["tickets_imb"] = x["tickets0_small_24_6"] - 0.5                    # share of small orders backing outcome 0
    x["money_imb"] = (x["net_big_usd_24_6"] / x["usd_24_6"]).clip(-1, 1)  # net large-order dollars, scaled
    x["late_move"] = x["mid_0h"] - x["mid_6h"]
    x["surprise6"] = x["payoff"] - x["mid_6h"]
    x["surprise0"] = x["payoff"] - x["mid_0h"]
    rows = []
    for name, g in (("all leagues", x), ("reliable start times", x[x["reliable"]])):
        for y, ylab in (("late_move", "price move T-6h..start"), ("surprise6", "result minus T-6h price"),
                        ("surprise0", "result minus closing price")):
            r = ols_cluster(g[y].to_numpy(), g[["tickets_imb", "money_imb"]].to_numpy(), g["cluster"].to_numpy(),
                            g["day"].to_numpy(), names=["tickets", "money"])
            rows.append({"sample": name, "outcome": ylab, "b_tickets": r.beta[1], "t_tickets": r.t[1],
                         "b_money": r.beta[2], "t_money": r.t[2], "n": r.n})
    b3 = pd.DataFrame(rows)
    b3.to_csv(out / "x_b3_tickets_vs_money.csv", index=False)
    print(b3.round(4).to_string(index=False))
    q = pd.qcut(x["tickets_imb"], 5, duplicates="drop")
    tab = x.groupby(q, observed=True).agg(n=("late_move", "size"), tickets_share0=("tickets0_small_24_6", "mean"),
                                           late_move_c=("late_move", lambda v: 100 * v.mean()),
                                           surprise_at_6h_c=("surprise6", lambda v: 100 * v.mean()),
                                           surprise_at_start_c=("surprise0", lambda v: 100 * v.mean()))
    tab.to_csv(out / "x_b3_tickets_quintiles.csv")
    print("\nby quintile of the public's ticket share on outcome 0\n", tab.round(3))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/research")
    ap.add_argument("--part", default="AB")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if args.dry_run:
        print("DRY RUN: already-examined slices only")
    if "A" in args.part.upper():
        part_a(out, args.dry_run)
    if "B" in args.part.upper():
        part_b(out, args.dry_run)
    print(f"\ndone in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
