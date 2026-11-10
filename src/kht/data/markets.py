"""Normalise Gamma market payloads into flat, typed rows.

Gamma returns ~120 loosely-typed fields per market. Research and trading only
need a few dozen, with consistent types, so everything downstream works from
the flat row produced by :func:`flatten_market`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..api.polymarket import parse_json_list

# Top-level topic tags, in priority order: the first one present on a market
# becomes its ``category``. They mirror the categories of the fee schedule.
CATEGORY_TAGS = [
    ("sports", "sports"),
    ("esports", "sports"),
    ("crypto", "crypto"),
    ("crypto-prices", "crypto"),
    ("geopolitics", "geopolitics"),
    ("politics", "politics"),
    ("elections", "politics"),
    ("world-elections", "politics"),
    ("global-elections", "politics"),
    ("finance", "finance"),
    ("economy", "economics"),
    ("economics", "economics"),
    ("fed", "economics"),
    ("business", "finance"),
    ("stocks", "finance"),
    ("tech", "tech"),
    ("ai", "tech"),
    ("weather", "weather"),
    ("mentions", "mentions"),
    ("pop-culture", "culture"),
    ("culture", "culture"),
    ("movies", "culture"),
    ("music", "culture"),
    ("science", "culture"),
    ("world", "geopolitics"),
]

# feeType prefixes are a reliable fallback when tags are missing.
FEE_TYPE_CATEGORY = {
    "sports": "sports",
    "crypto": "crypto",
    "finance": "finance",
    "politics": "politics",
    "economics": "economics",
    "culture": "culture",
    "weather": "weather",
    "tech": "tech",
    "mentions": "mentions",
    "geopolitics": "geopolitics",
}


def parse_ts(value: Any) -> float:
    """Parse the several timestamp spellings Gamma uses into epoch seconds (NaN if absent)."""
    if value in (None, ""):
        return float("nan")
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace("Z", "+00:00")
    if " " in s and "T" not in s:
        s = s.replace(" ", "T", 1)
    # e.g. "2026-10-26T03:17:16.107395+00:00:00" or "...+00"
    if s.endswith("+00:00:00"):
        s = s[: -len(":00")]
    elif s.endswith("+00"):
        s = s + ":00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        try:
            dt = datetime.fromisoformat(s[:19])
        except ValueError:
            return float("nan")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _f(value: Any, default: float = float("nan")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def categorise(tag_slugs: list[str], fee_type: str | None) -> str:
    slugs = set(tag_slugs)
    for slug, cat in CATEGORY_TAGS:
        if slug in slugs:
            return cat
    if fee_type:
        for prefix, cat in FEE_TYPE_CATEGORY.items():
            if fee_type.startswith(prefix):
                return cat
    return "other"


def flatten_market(m: dict[str, Any]) -> dict[str, Any] | None:
    """Flatten one Gamma market. Returns None for markets that are not binary."""
    outcomes = parse_json_list(m.get("outcomes"))
    tokens = parse_json_list(m.get("clobTokenIds"))
    if len(outcomes) != 2 or len(tokens) != 2:
        return None
    final = [_f(x) for x in parse_json_list(m.get("outcomePrices"))]
    winner = float("nan")
    if len(final) == 2:
        if final[0] >= 0.99 and final[1] <= 0.01:
            winner = 0.0
        elif final[1] >= 0.99 and final[0] <= 0.01:
            winner = 1.0
    events = m.get("events") or []
    ev = events[0] if events and isinstance(events[0], dict) else {}
    tags = m.get("tags") or []
    tag_slugs = [str(t.get("slug") or "").lower() for t in tags if isinstance(t, dict)]
    fee = m.get("feeSchedule") or {}
    fee_type = m.get("feeType")
    return {
        "market_id": int(m["id"]),
        "condition_id": m.get("conditionId"),
        "question": m.get("question"),
        "slug": m.get("slug"),
        "event_id": int(ev["id"]) if ev.get("id") else -1,
        "event_slug": ev.get("slug"),
        "event_title": ev.get("title"),
        "outcome0": str(outcomes[0]),
        "outcome1": str(outcomes[1]),
        "token0": str(tokens[0]),
        "token1": str(tokens[1]),
        "start_ts": parse_ts(m.get("startDate")),
        "end_ts": parse_ts(m.get("endDate")),
        "closed_ts": parse_ts(m.get("closedTime")),
        "created_ts": parse_ts(m.get("createdAt")),
        "game_start_ts": parse_ts(m.get("gameStartTime")),
        "volume": _f(m.get("volumeNum", m.get("volume")), 0.0),
        "liquidity": _f(m.get("liquidityNum", m.get("liquidity")), 0.0),
        "closed": bool(m.get("closed")),
        "winner": winner,
        "final0": final[0] if len(final) == 2 else float("nan"),
        "neg_risk": bool(m.get("negRisk")),
        "fee_rate": _f(fee.get("rate"), 0.0),
        "fee_rebate": _f(fee.get("rebateRate"), 0.0),
        "fee_type": fee_type,
        "tick": _f(m.get("orderPriceMinTickSize"), 0.01),
        "min_size": _f(m.get("orderMinSize"), 5.0),
        "sports_type": m.get("sportsMarketType"),
        "line": _f(m.get("line")),
        "uma_status": m.get("umaResolutionStatus"),
        "tags": "|".join(tag_slugs),
        "category": categorise(tag_slugs, fee_type),
        "is_game": "games" in tag_slugs or m.get("gameStartTime") not in (None, ""),
        "is_recurring": "recurring" in tag_slugs,
        # live snapshot fields (meaningful for open markets only)
        "best_bid": _f(m.get("bestBid")),
        "best_ask": _f(m.get("bestAsk")),
        "last_price": _f(m.get("lastTradePrice")),
        "spread": _f(m.get("spread")),
        "volume_24h": _f(m.get("volume24hr"), 0.0),
        "accepting_orders": bool(m.get("acceptingOrders")),
        "version": m.get("version"),
    }
