"""Bulk, resumable downloads of market metadata, price histories and trade tapes.

Everything lands under ``data/`` (git-ignored; fully re-creatable):

    data/meta/<name>.parquet            flat market rows (see markets.flatten_market)
    data/prices/<grain>/part-XXXXX.parquet   long format: market_id, ts, price
    data/trades/<condition_id>.parquet  one trade tape per market

Price downloads are chunked and resumable: each finished chunk is a parquet
part plus an entry in ``done.txt``; re-running skips completed markets.
"""

from __future__ import annotations

import concurrent.futures as cf
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..api import Polymarket
from .markets import flatten_market

DATA_DIR = Path(os.environ.get("KHT_DATA_DIR", "data"))


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------- metadata
def download_market_meta(pm: Polymarket, name: str, **filters: Any) -> pd.DataFrame:
    """Download and flatten every market matching ``filters``; write parquet."""
    out = DATA_DIR / "meta" / f"{name}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    skipped = 0
    t0 = time.time()
    for i, m in enumerate(pm.iter_markets(include_tag=True, **filters)):
        row = flatten_market(m)
        if row is None:
            skipped += 1
        else:
            rows.append(row)
        if (i + 1) % 5000 == 0:
            log(f"meta {name}: {i + 1} markets fetched ({time.time() - t0:.0f}s)")
    df = pd.DataFrame(rows).drop_duplicates("market_id").reset_index(drop=True)
    df.to_parquet(out, index=False)
    log(f"meta {name}: wrote {len(df)} rows ({skipped} non-binary skipped) -> {out}")
    return df


# ------------------------------------------------------------ price panels
def _fetch_series(pm: Polymarket, market_id: int, token: str, bucket: int) -> tuple[int, np.ndarray, np.ndarray, str]:
    try:
        pts = pm.prices_history(token, interval="max", bucket_seconds=bucket)
    except Exception as exc:  # noqa: BLE001 - recorded and retried on the next run
        return market_id, np.empty(0, np.int64), np.empty(0, np.float32), repr(exc)[:200]
    if not pts:
        return market_id, np.empty(0, np.int64), np.empty(0, np.float32), ""
    arr = np.asarray(pts, dtype=np.float64)
    return market_id, arr[:, 0].astype(np.int64), arr[:, 1].astype(np.float32), ""


def download_price_panel(
    pm: Polymarket,
    meta: pd.DataFrame,
    grain: str = "3h",
    bucket_seconds: int = 10_800,
    workers: int = 12,
    chunk: int = 2_000,
) -> None:
    """Download the full-life price series of ``token0`` for every market in ``meta``."""
    out_dir = DATA_DIR / "prices" / grain
    out_dir.mkdir(parents=True, exist_ok=True)
    done_file = out_dir / "done.txt"
    done: set[int] = set()
    if done_file.exists():
        done = {int(x) for x in done_file.read_text().split() if x.strip()}
    todo = meta.loc[~meta["market_id"].isin(done), ["market_id", "token0"]]
    log(f"prices[{grain}]: {len(done)} done, {len(todo)} to fetch")
    part_no = len(list(out_dir.glob("part-*.parquet")))
    t0 = time.time()
    fetched = 0
    for lo in range(0, len(todo), chunk):
        batch = todo.iloc[lo : lo + chunk]
        ids: list[np.ndarray] = []
        tss: list[np.ndarray] = []
        pxs: list[np.ndarray] = []
        ok_ids: list[int] = []
        errors = 0
        with cf.ThreadPoolExecutor(max_workers=workers) as pool:
            futs = [
                pool.submit(_fetch_series, pm, int(mid), str(tok), bucket_seconds)
                for mid, tok in zip(batch["market_id"], batch["token0"])
            ]
            for fut in cf.as_completed(futs):
                mid, ts, px, err = fut.result()
                if err:
                    errors += 1
                    continue
                ok_ids.append(mid)
                if len(ts):
                    ids.append(np.full(len(ts), mid, np.int64))
                    tss.append(ts)
                    pxs.append(px)
        if ids:
            part = pd.DataFrame(
                {"market_id": np.concatenate(ids), "ts": np.concatenate(tss), "price": np.concatenate(pxs)}
            )
            part.to_parquet(out_dir / f"part-{part_no:05d}.parquet", index=False)
            part_no += 1
        with done_file.open("a") as fh:
            fh.write("\n".join(str(i) for i in ok_ids) + "\n")
        fetched += len(batch)
        rate = fetched / max(1e-9, time.time() - t0)
        log(
            f"prices[{grain}]: {fetched}/{len(todo)} ({rate:.1f}/s, {errors} errors this chunk, "
            f"eta {(len(todo) - fetched) / max(rate, 1e-9) / 60:.0f} min)"
        )


def load_price_panel(grain: str = "3h") -> pd.DataFrame:
    parts = sorted((DATA_DIR / "prices" / grain).glob("part-*.parquet"))
    if not parts:
        raise FileNotFoundError(f"no price parts under {DATA_DIR / 'prices' / grain}")
    df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    return df.drop_duplicates(["market_id", "ts"]).sort_values(["market_id", "ts"]).reset_index(drop=True)


def load_meta(name: str) -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / "meta" / f"{name}.parquet")


# ------------------------------------------------------------- trade tapes
TRADE_COLS = ["timestamp", "side", "outcome_index", "price", "size", "proxy_wallet"]


def download_trades(pm: Polymarket, condition_id: str, max_pages: int | None = 300) -> pd.DataFrame:
    """Download (or load from cache) the taker-side trade tape of one market."""
    out = DATA_DIR / "trades" / f"{condition_id}.parquet"
    if out.exists():
        return pd.read_parquet(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        (int(t["timestamp"]), t.get("side"), int(t.get("outcome_index", -1)), float(t["price"]),
         float(t["size"]), t.get("proxy_wallet"))
        for t in pm.iter_trades(condition=condition_id, max_pages=max_pages)
    ]
    df = pd.DataFrame(rows, columns=TRADE_COLS).sort_values("timestamp").reset_index(drop=True)
    df.to_parquet(out, index=False)
    return df


def _download_one(pm: Polymarket, condition_id: str, max_pages: int | None) -> int:
    """Fetch one tape unless it is already on disk; return only a row count.

    Returning the frame itself would keep every tape alive in the futures map
    of ``download_trades_many`` (gigabytes on a large run).
    """
    if (DATA_DIR / "trades" / f"{condition_id}.parquet").exists():
        return -1
    return len(download_trades(pm, condition_id, max_pages))


def download_trades_many(pm: Polymarket, condition_ids: list[str], workers: int = 8, max_pages: int | None = 300) -> None:
    have = {p.stem for p in (DATA_DIR / "trades").glob("*.parquet")}
    todo = [c for c in condition_ids if c not in have]
    log(f"trades: {len(condition_ids) - len(todo)} already on disk, {len(todo)} to fetch")
    t0 = time.time()
    done = 0
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(_download_one, pm, c, max_pages): c for c in todo}
        for fut in cf.as_completed(futs):
            done += 1
            try:
                fut.result()
            except Exception as exc:  # noqa: BLE001
                log(f"trades: {futs[fut]} failed: {exc!r}"[:200])
            if done % 200 == 0:
                rate = done / (time.time() - t0)
                log(f"trades: {done}/{len(todo)} ({rate:.1f}/s, eta {(len(todo) - done) / max(rate, 1e-9) / 60:.0f} min)")
    log(f"trades: finished {done} markets in {time.time() - t0:.0f}s")
