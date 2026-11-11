"""Add up and judge the paper test of resting orders before games (docs/09_sports_rewards.md).

    python scripts/us_rewards_score.py [--state state/us-rewards] [--settle]

Reads what `kht us-rewards` wrote (runs/*/games.csv.gz, runs/*/hits.csv) and
applies the rules fixed in docs/09, section 5. `--settle` looks up how each
finished game settled (public, no key) and keeps the answers in
<state>/settlements.csv. Nothing here places an order.

Writes reports/research/usr_summary.txt, usr_by_programme.csv, usr_by_size.csv,
usr_by_day_all.csv, usr_by_day_thin.csv, usr_by_day_core.csv and usr_fills.csv.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from kht.trading.us_rewards import GRID, PULL, WINDOW

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "research"
PRIMARY = 100                       # contracts on each side: the size the test is judged on
MINIMUM = 1.0                       # the exchange does not pay a reward under a dollar
MIN_GAMES, MIN_DATES, BAR = 2000, 5, 3.0
# The second judged account: programmes in which, in the one look taken before the test (docs/09, section 3),
# an order of 100 contracts held a tenth or more of a side's score. Matched by the start of the programme's name.
THIN = ("itf_moneyline", "doubles_moneyline", "utr_moneyline", "darts_moneyline", "astra_cup_women_moneyline")
# The third: named on 11 November after the history of past games (docs/09, section 4) and before any reading of the test.
CORE = ("itf_moneyline", "utr_moneyline")
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 200)
pd.set_option("display.max_colwidth", 60)


def load(state: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    games = [pd.read_csv(p) for p in sorted(state.glob("runs/*/games.csv.gz"))]
    hits = [pd.read_csv(p) for p in sorted(state.glob("runs/*/hits.csv"))]
    g = pd.concat([x for x in games if len(x)], ignore_index=True) if any(len(x) for x in games) else pd.DataFrame()
    h = pd.concat([x for x in hits if len(x)], ignore_index=True) if any(len(x) for x in hits) else pd.DataFrame()
    log = pd.read_csv(state / "log.csv") if (state / "log.csv").exists() else pd.DataFrame()
    return g, h, log


def per_game_day(g: pd.DataFrame) -> pd.DataFrame:
    """One row per game per US date, the runs added together."""
    sums = ["obs_s", "quote_s", "cap_s", "paid_bid_s", "paid_ask_s", "paid_bid_alone_s", "paid_ask_alone_s", "score_bid_s", "score_ask_s"] \
        + [f"acc_{s}_{x}" for s in ("bid", "ask") for x in GRID]
    g = g.sort_values("last_ts")
    last = g.groupby(["slug", "date"]).tail(1).set_index(["slug", "date"])
    d = g.groupby(["slug", "date"])[sums].sum()
    for col in ("program", "pool", "markets_in_event", "target", "discount", "max_spread", "start"):
        d[col] = last[col]
    # two runs can never watch the same seconds, but if they ever did the excess is scaled away rather than counted twice
    whole = d.groupby("slug")["obs_s"].transform("sum")
    scale = np.minimum(1.0, (WINDOW - PULL) / whole.where(whole > 0, 1.0))
    for col in sums:
        d[col] = d[col] * scale
    d["slice"] = d["pool"] / d["markets_in_event"]
    return d.reset_index()


def game_facts(g: pd.DataFrame) -> pd.DataFrame:
    """Per game: the middle of the book at the last reading before quoting stopped, and what traded while watched."""
    g = g.sort_values("last_ts")
    last = g.groupby("slug").tail(1).set_index("slug")
    first = g.sort_values("first_ts").groupby("slug").head(1).set_index("slug")
    return pd.DataFrame({"mid_pull": last["mid_last"], "vol_last": last["vol_last"], "vol_first": first["vol_first"], "watched_to": last["last_ts"], "start": last["start"]})


def fills(h: pd.DataFrame, x: float) -> pd.DataFrame:
    """The fills of an order of ``x`` contracts on each side: each game and side is filled at most ``x`` in all."""
    if not len(h):
        return pd.DataFrame(columns=["slug", "program", "side", "t1", "px", "qty", "mid1", "start"])
    out = []
    h = h.sort_values("t1")
    for (slug, side), grp in h.groupby(["slug", "side"]):
        left = x
        for r in grp.itertuples():
            size = max(float(r.dv) if pd.notna(r.dv) else 0.0, float(r.cross_qty) if pd.notna(r.cross_qty) else 0.0)
            qty = min(left, size)
            if qty <= 1e-9:
                continue
            out.append({"slug": slug, "program": r.program, "side": side, "t1": r.t1, "px": r.px, "qty": qty, "mid1": r.mid1, "start": r.start})
            left -= qty
            if left <= 1e-9:
                break
    return pd.DataFrame(out)


def settlements(state: Path, slugs: list[str], look_up: bool) -> pd.Series:
    path = state / "settlements.csv"
    have = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["slug", "settle", "asof"])
    if look_up:
        from kht.api.http import Http
        from kht.api.polymarket_us import PolymarketUS

        us = PolymarketUS(Http(rate_per_host={"gateway.polymarket.us": 6.0}))
        known = set(have.loc[have["settle"].notna(), "slug"])
        rows = []
        for slug in slugs:
            if slug in known:
                continue
            try:
                rows.append({"slug": slug, "settle": us.settlement(slug), "asof": int(time.time())})
            except Exception:
                continue
        if rows:
            have = pd.concat([have[~have["slug"].isin([r["slug"] for r in rows])], pd.DataFrame(rows)], ignore_index=True)
            have.sort_values("slug").to_csv(path, index=False)
    return have.dropna(subset=["settle"]).drop_duplicates("slug").set_index("slug")["settle"].astype(float)


def clustered_z(values: np.ndarray, clusters: np.ndarray) -> tuple[float, float, int]:
    """Mean, and its z with each cluster counted as one observation."""
    n = len(values)
    if n < 2:
        return (float(values.mean()) if n else float("nan")), float("nan"), 0
    mean = float(values.mean())
    _, inv = np.unique(clusters, return_inverse=True)
    k = int(inv.max()) + 1
    if k < 2:
        return mean, float("nan"), k
    s = np.bincount(inv, weights=values - mean, minlength=k)
    var = k / (k - 1) * float(np.dot(s, s)) / n**2
    return mean, (mean / var**0.5 if var > 0 else float("nan")), k


def account(d: pd.DataFrame, facts: pd.DataFrame, h: pd.DataFrame, settle: pd.Series, x: float, now: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per game, what an order of ``x`` contracts on each side made: reward by the formula, and fills."""
    d = d.copy()
    for s in ("bid", "ask"):
        d[f"rw_{s}"] = d[f"acc_{s}_{x}"] * d["slice"] / (2.0 * WINDOW)
    f = fills(h, x)
    full = set()
    if len(f):
        tot = f.groupby(["slug", "side"])["qty"].sum()
        full = {k for k, v in tot.items() if v >= x - 1e-9}
        # rule 6: a side that was filled whole stops earning, and the unkind reading is that it earned nothing in that game
        for slug, side in full:
            d.loc[d["slug"] == slug, f"rw_{side}"] = 0.0
    d["reward_formula"] = d["rw_bid"] + d["rw_ask"]
    d["settle"] = d["slug"].map(settle)
    called_off = d["settle"].notna() & (d["settle"] > 1e-9) & (d["settle"] < 1 - 1e-9)
    d.loc[called_off, "reward_formula"] = 0.0                      # rule 7: no reward for a game that was called off
    d["reward_paid"] = np.where(d["reward_formula"] >= MINIMUM, d["reward_formula"], 0.0)   # rule 5: by market and date
    # seconds in which each side would be paid: without us, or with our order where that makes the difference
    d["q_s"] = np.maximum(d["paid_bid_alone_s"], d["paid_bid_s"]) + np.maximum(d["paid_ask_alone_s"], d["paid_ask_s"])
    per = d.groupby("slug").agg(program=("program", "first"), start=("start", "max"), slice=("slice", "first"), markets_in_event=("markets_in_event", "first"),
                                obs_s=("obs_s", "sum"), quote_s=("quote_s", "sum"), cap_s=("cap_s", "sum"), q_s=("q_s", "sum"), max_spread=("max_spread", "first"),
                                share_s=(f"acc_bid_{x}", "sum"), share_s2=(f"acc_ask_{x}", "sum"),
                                reward_formula=("reward_formula", "sum"), reward_paid=("reward_paid", "sum"), settle=("settle", "first"))
    per["called_off"] = per["settle"].notna() & (per["settle"] > 1e-9) & (per["settle"] < 1 - 1e-9)
    # The same reward as the exchange's filed rules word it (docs/09, section 9): a share of the whole pool, by score summed over
    # the period, so that seconds in which a side is not paid give their money to the seconds in which it is. Where a programme has
    # a maximum spread the two readings are the same. Described beside the judged figure, never in place of it.
    rate = (per["q_s"] / per["obs_s"].where(per["obs_s"] > 0)).where(lambda r: r > 0)
    rule = np.minimum(per["slice"] * (per["share_s"] + per["share_s2"]) / (rate * WINDOW), per["slice"])
    per["reward_rule"] = np.where(per["max_spread"].notna(), per["reward_formula"], rule.fillna(0.0))
    per.loc[per["called_off"], "reward_rule"] = 0.0
    per = per.join(facts[["mid_pull"]])
    if len(f):
        f = f.join(per[["settle", "mid_pull"]], on="slug")
        sign = np.where(f["side"] == "bid", 1.0, -1.0)
        f["pnl_settle"] = sign * (f["settle"] - f["px"]) * f["qty"]
        f["pnl_mid"] = sign * (f["mid_pull"] - f["px"]) * f["qty"]
        agg = f.groupby("slug").agg(filled=("qty", "sum"), pnl_settle=("pnl_settle", lambda s: s.sum(min_count=len(s))), pnl_mid=("pnl_mid", lambda s: s.sum(min_count=len(s))))
        per = per.join(agg)
    for col in ("filled", "pnl_settle", "pnl_mid"):
        if col not in per:
            per[col] = np.nan
    per["filled"] = per["filled"].fillna(0.0)
    no_fill = per["filled"] <= 1e-9
    per.loc[no_fill, ["pnl_settle", "pnl_mid"]] = 0.0
    per["day"] = pd.to_datetime(per["start"], unit="s", utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
    per["over"] = per["start"] < now - 12 * 3600                   # finished long enough ago to have settled
    per["net"] = per["reward_paid"] + per["pnl_settle"]
    return per.reset_index(), f


def table_by(per: pd.DataFrame, key: str) -> pd.DataFrame:
    g = per.groupby(key)
    t = g.agg(games=("slug", "size"), hours_quoted=("quote_s", lambda s: s.sum() / 3600.0), reward_formula=("reward_formula", "sum"), reward_paid=("reward_paid", "sum"),
              games_filled=("filled", lambda s: int((s > 1e-9).sum())), contracts_filled=("filled", "sum"), fills_at_settlement=("pnl_settle", "sum"),
              fills_at_last_mid=("pnl_mid", "sum"), net=("net", "sum"), unsettled=("pnl_settle", lambda s: int(s.isna().sum())))
    t["share_of_score"] = g.apply(lambda q: (q["share_s"].sum() + q["share_s2"].sum()) / (2.0 * q["quote_s"].sum()) if q["quote_s"].sum() > 0 else np.nan)
    t["net_a_game"] = t["net"] / t["games"]
    return t.reset_index()


def rehearsal(state: Path) -> list[str]:
    """The order-placing system itself, run on paper under its own limits (docs/10_us_quoter.md). Described, not judged."""
    if not (state / "accrued.json").exists():
        return []
    acc = json.loads((state / "accrued.json").read_text())
    days = pd.Series({(slug, date): v for slug, by in acc.items() for date, v in by.items()}, dtype=float)
    settled = pd.read_csv(state / "settled.csv") if (state / "settled.csv").exists() else pd.DataFrame(columns=["pnl"])
    paper = json.loads((state / "paper.json").read_text()) if (state / "paper.json").exists() else {}
    cycles = pd.read_csv(state / "cycles.csv") if (state / "cycles.csv").exists() else pd.DataFrame()
    actions = pd.read_csv(state / "actions.csv") if (state / "actions.csv").exists() else pd.DataFrame(columns=["action"])
    fills = actions[actions["action"] == "fill"]
    out = ["", "THE REHEARSAL: the order-placing system on paper, under its own limits (config/us_quoter.json). Described, not judged."]
    if len(cycles):
        hours = (cycles["ts"].max() - cycles["ts"].min()) / 3600.0
        out.append(f"from {pd.to_datetime(cycles['ts'].min(), unit='s', utc=True):%d %b %H:%M} to {pd.to_datetime(cycles['ts'].max(), unit='s', utc=True):%d %b %H:%M} UTC ({hours:,.1f} hours); "
                   f"games rested in at once: median {cycles['games'].median():.0f}; most at risk in positions: ${cycles['at_risk'].max():,.2f}")
    out += [f"markets rested in: {days.index.get_level_values(0).nunique() if len(days) else 0:,}; reward by the formula: ${days.sum():,.2f}; "
            f"counting only a market and date that reached $1: ${days[days >= MINIMUM].sum():,.2f}",
            f"fills: {len(fills):,} ({fills['qty'].astype(float).sum() if len(fills) else 0:,.0f} contracts); positions settled: {len(settled):,}, for ${settled['pnl'].sum():,.2f}; "
            f"still open: {len(paper.get('positions') or {}):,}",
            f"net so far, reward after the minimum plus settled positions: ${days[days >= MINIMUM].sum() + settled['pnl'].sum():,.2f}"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=str(ROOT / "state" / "us-rewards"))
    ap.add_argument("--quoter", default=str(ROOT / "state" / "us-quoter"), help="the state folder of kht us-quote, if it has been run")
    ap.add_argument("--settle", action="store_true", help="look up how finished games settled (public data)")
    ap.add_argument("--out", default=str(OUT), help="where the tables are written")
    args = ap.parse_args()
    state, out = Path(args.state), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    g, h, log = load(state)
    lines = ["Paper orders before games on Polymarket US (docs/09_sports_rewards.md). A simulation: no order was placed, and no reward was paid to anyone."]
    if not len(g):
        print("\n".join(lines + ["nothing recorded yet"]))
        return
    now = time.time()
    d, facts = per_game_day(g), game_facts(g)
    finished = sorted(facts.index[facts["start"] < now - 12 * 3600])
    settle = settlements(state, finished, args.settle)
    hours = float(log["minutes"].sum()) / 60.0 if len(log) else float("nan")
    lines.append(f"runs: {len(log)}; hours recorded: {hours:,.1f}; games followed: {d['slug'].nunique():,}; "
                 f"first reading {pd.to_datetime(g['first_ts'].min(), unit='s', utc=True):%d %b %H:%M} UTC, last {pd.to_datetime(g['last_ts'].max(), unit='s', utc=True):%d %b %H:%M} UTC")
    lines.append(f"games that started more than 12 hours ago: {len(finished):,}; of them with a settlement on file: {int(pd.Index(finished).isin(settle.index).sum()):,}")

    # ---- the three judged accounts: 100 contracts a side, programmes where the market on who wins has the pool to itself
    per, f = account(d, facts, h, settle, PRIMARY, now)
    own = per[(per["markets_in_event"] == 1)]
    show = ["games", "hours_quoted", "share_of_score", "reward_formula", "reward_paid", "games_filled", "contracts_filled", "fills_at_settlement", "fills_at_last_mid", "net", "net_a_game"]
    for tag, title, pick in (("all", "R1-all: every such programme", own),
                             ("thin", "R1-thin: the programmes named in advance as thinly quoted (" + ", ".join(THIN) + ")", own[own["program"].str.startswith(THIN)]),
                             ("core", "R1-core: lower-tour tennis only (" + ", ".join(CORE) + ")", own[own["program"].str.startswith(CORE)])):
        judged = pick[pick["over"] & pick["settle"].notna()]           # a game is judged once its settlement is known, filled or not
        mean, z, k = clustered_z(judged["net"].to_numpy(), (judged["day"] + "|" + judged["program"]).to_numpy())
        dates = judged["day"].nunique()
        lines += ["", f"JUDGED ACCOUNT {title}. {PRIMARY} contracts on each side.",
                  f"games judged (started more than 12 hours ago, settlement known): {len(judged):,} over {dates} US dates and {k} date-programme groups; "
                  f"games still waiting for a settlement: {int((pick['over'] & pick['settle'].isna()).sum()):,}"]
        if not len(judged):
            continue
        cap = PRIMARY * judged["cap_s"].sum() / max(judged["quote_s"].sum(), 1.0)
        lines += [f"reward by the published formula: ${judged['reward_formula'].sum():,.2f}; after the $1 minimum by market and date: ${judged['reward_paid'].sum():,.2f}",
                  f"   (as the filed rules word the split, described only: ${judged['reward_rule'].sum():,.2f}; of it in games that reach $1: ${judged.loc[judged['reward_rule'] >= MINIMUM, 'reward_rule'].sum():,.2f})",
                  f"games in which an order was traded against: {int((judged['filled'] > 1e-9).sum()):,} ({100 * (judged['filled'] > 1e-9).mean():.1f}%); contracts: {judged['filled'].sum():,.0f}",
                  f"what those fills made, held to settlement: ${judged['pnl_settle'].sum():,.2f}; valued at the last middle of the book before the start: ${judged['pnl_mid'].sum():,.2f}",
                  f"net: ${judged['net'].sum():,.2f}; a game: ${mean:,.3f}; z with each date-programme group as one observation: {z:.2f}",
                  f"money resting in one game while quoted: about ${cap:,.0f}; game-hours quoted: {judged['quote_s'].sum() / 3600:,.0f}",
                  f"verdict by the rule fixed in advance (at least {MIN_GAMES:,} games over at least {MIN_DATES} dates, mean net above zero with z of {BAR:g} or more): "
                  + ("NOT YET JUDGED, too few games or dates" if len(judged) < MIN_GAMES or dates < MIN_DATES
                     else ("PASSES" if mean > 0 and z >= BAR else "FAILS"))]
        by_day = table_by(judged, "day")
        by_day.round(3).to_csv(out / f"usr_by_day_{tag}.csv", index=False)
        lines += ["", "by US date of the game", by_day[["day"] + show].round(3).to_string(index=False)]
        if tag == "all":
            by_prog = table_by(judged, "program").sort_values("games", ascending=False)
            by_prog.round(3).to_csv(out / "usr_by_programme.csv", index=False)
            lines += ["", "by programme", by_prog[["program"] + show].round(3).to_string(index=False)]
            if len(f):
                f[f["slug"].isin(judged["slug"])].round(4).to_csv(out / "usr_fills.csv", index=False)

    # ---- every size, and the programmes left out of the judged account
    rows = []
    for label, pick in (("own pool", lambda p: p["markets_in_event"] == 1), ("pool shared with other markets of the game, split equally (an assumption)", lambda p: p["markets_in_event"] > 1)):
        for x in GRID:
            p, _ = account(d, facts, h, settle, x, now)
            p = p[pick(p) & p["over"] & p["settle"].notna()]
            if not len(p):
                continue
            m, zz, _ = clustered_z(p["net"].to_numpy(), (p["day"] + "|" + p["program"]).to_numpy())
            rows.append({"programmes": label, "contracts_a_side": x, "games": len(p), "reward_formula": p["reward_formula"].sum(), "reward_paid": p["reward_paid"].sum(),
                         "games_filled": int((p["filled"] > 1e-9).sum()), "contracts_filled": p["filled"].sum(), "fills_at_settlement": p["pnl_settle"].sum(),
                         "fills_at_last_mid": p["pnl_mid"].sum(), "net": p["net"].sum(), "net_a_game": m, "z": zz,
                         "money_in_a_game": x * p["cap_s"].sum() / max(p["quote_s"].sum(), 1.0)})
    if rows:
        sizes = pd.DataFrame(rows)
        sizes.round(3).to_csv(out / "usr_by_size.csv", index=False)
        lines += ["", "every order size (only 100 on the first kind of programme is judged; the rest is description)", sizes.round(3).to_string(index=False)]

    # ---- what is known before games settle: the reward side alone, on everything recorded so far
    everything, _ = account(d, facts, h, pd.Series(dtype=float), PRIMARY, now)
    t = table_by(everything, "program").sort_values("games", ascending=False)
    lines += ["", f"all games recorded so far, settled or not, {PRIMARY} contracts a side: reward by the formula and how often an order was traded against",
              t[["program", "games", "hours_quoted", "share_of_score", "reward_formula", "reward_paid", "games_filled", "contracts_filled", "fills_at_last_mid"]].round(3).to_string(index=False)]
    lines += rehearsal(Path(args.quoter))
    text = "\n".join(lines) + "\n"
    (out / "usr_summary.txt").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
