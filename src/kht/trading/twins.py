"""The same question on two exchanges: pairing Polymarket US markets with polymarket.com.

Polymarket US lists many of the events that polymarket.com lists, usually
under the same title and with the same answers. The two order books are
separate, and a US resident can trade only the first, but anyone can read the
prices of both.

Pairing is deliberately strict, because two markets that look alike can be
different contracts:

* the event titles must be equal once case, accents and punctuation are gone;
* the answer's label must be equal in the same sense. "Above 1.2M" (US) is
  not "1.2M-1.3M" (polymarket.com), "Eric Jones (D)" is not "Democratic
  Party", and neither is paired;
* an event with a single market pairs with an event with a single market.

A pair found this way is a candidate, not a proof that the rules of the two
contracts agree. For settled markets that can be checked: both should have
paid the same side (``scripts/two_venues.py`` reports how often they did).

Only the standard library is used: this runs in the scheduled recorder.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

_DECIMAL = re.compile(r"(?<=\d)\.(?=\d)")
_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3}\b)")


def norm(text: Any) -> str:
    """A title or label with case, accents and punctuation removed.

    Signs that change the meaning of a number are kept as words, so that
    "70+" and "70", or "<1.2M" and "1.2M", stay different.
    """
    s = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode().lower()
    s = _THOUSANDS.sub("", s)
    s = _DECIMAL.sub("p", s)
    for sign, word in (("&", " and "), ("+", " plus "), (">=", " atleast "), ("<=", " atmost "), (">", " over "), ("<", " under "),
                       ("%", " pct "), ("$", " usd ")):
        s = s.replace(sign, word)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


@dataclass(frozen=True)
class Twin:
    us_slug: str
    intl_id: str            # polymarket.com market id
    token_yes: str          # its "Yes" token, for order books and price history
    condition: str
    rule: str               # "label" or "single"
    intl_event_id: str
    intl_question: str
    intl_label: str
    neg_risk: bool


def _tokens(market: dict[str, Any]) -> list[str]:
    raw = market.get("clobTokenIds")
    if isinstance(raw, str):
        import json

        try:
            raw = json.loads(raw)
        except ValueError:
            return []
    return [str(t) for t in raw or []]


def _yes_no(market: dict[str, Any]) -> bool:
    raw = market.get("outcomes")
    if isinstance(raw, str):
        import json

        try:
            raw = json.loads(raw)
        except ValueError:
            return False
    return [str(o).strip().lower() for o in raw or []] == ["yes", "no"]


def index_intl(events: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """polymarket.com events by normalised title."""
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in events:
        key = norm(e.get("title"))
        if key:
            out[key].append(e)
    return out


def _end(value: Any) -> float | None:
    from datetime import datetime

    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def pair_event(us_event: dict[str, Any], candidates: list[dict[str, Any]]) -> list[Twin]:
    """Twins of one US event's markets among polymarket.com events with the same title.

    ``us_event`` needs "title" and "markets" (each with "slug" and "title", the
    answer's label; optionally "endDate"). When several polymarket.com events
    share the title, the one that pairs the most answers wins, and among
    equals the one whose end date is nearest.
    """
    us_markets = [m for m in us_event.get("markets") or [] if m.get("slug")]
    if not us_markets or not candidates:
        return []
    us_end = _end(us_event.get("endDate")) or next((t for t in (_end(m.get("endDate")) for m in us_markets) if t), None)
    best: tuple[int, float, list[Twin]] = (0, float("inf"), [])
    for ev in candidates:
        markets = [m for m in ev.get("markets") or [] if _yes_no(m) and len(_tokens(m)) == 2]
        found: list[Twin] = []
        if len(us_markets) == 1 and len(ev.get("markets") or []) == 1 and markets:
            # one question on each side: the titles already matched
            found.append(_twin(us_markets[0], markets[0], ev, "single"))
        else:
            by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for m in markets:
                key = norm(m.get("groupItemTitle"))
                if key:
                    by_label[key].append(m)
            for um in us_markets:
                key = norm(um.get("title"))
                hits = by_label.get(key) if key else None
                if hits and len(hits) == 1:           # a label used twice in one event pairs with nothing
                    found.append(_twin(um, hits[0], ev, "label"))
        gap = abs((_end(ev.get("endDate")) or 0.0) - us_end) if us_end else 0.0
        if found and (len(found), -gap) > (best[0], -best[1]):
            best = (len(found), gap, found)
    return best[2]


def _twin(us_market: dict[str, Any], m: dict[str, Any], ev: dict[str, Any], rule: str) -> Twin:
    return Twin(us_slug=str(us_market["slug"]), intl_id=str(m.get("id")), token_yes=_tokens(m)[0], condition=str(m.get("conditionId") or ""),
                rule=rule, intl_event_id=str(ev.get("id")), intl_question=str(m.get("question") or ""),
                intl_label=str(m.get("groupItemTitle") or ""), neg_risk=bool(ev.get("negRisk") or m.get("negRisk")))


def pair_all(us_events: Iterable[dict[str, Any]], intl_events: Iterable[dict[str, Any]]) -> dict[str, Twin]:
    """Every twin, by US market slug. A polymarket.com market paired twice is paired with nothing."""
    index = index_intl(intl_events)
    out: dict[str, Twin] = {}
    used: dict[str, list[str]] = defaultdict(list)
    for e in us_events:
        for tw in pair_event(e, index.get(norm(e.get("title")), [])):
            out[tw.us_slug] = tw
            used[tw.intl_id].append(tw.us_slug)
    for slugs in used.values():
        if len(slugs) > 1:
            for s in slugs:
                out.pop(s, None)
    return out
