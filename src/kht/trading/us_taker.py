"""The program that would place the trades of test L1: sales to the last-tick bids.

docs/11_crypto_us.md, sections 5 and 11; docs/12_us_taker.md.

    In the last minutes before a crypto market on Polymarket US settles,
    on a result the price can no longer reach, sell "Yes" to the best bid
    where "Yes" will pay nothing (or buy "Yes" at the best offer where it
    will pay $1), and hold to settlement.

Which trade, on which reading, is decided by ``lasttick_rule.decide`` and
by nothing in this file. What this file adds is what an account needs
around the rule: one order a market, a fixed sum that may be tied up at one
settlement time, a hard stop at the first loss, and a record of every
order and what became of it.

It runs three ways:

* on paper (the default): an order is "filled" against the very book it
  was decided on. Nothing is sent anywhere;
* as a replay: the same, over books the recorder ``kht us-lasttick`` wrote
  down on an earlier evening;
* live, or as a preview that sends each order to the exchange's preview
  call only. Both need the switches and the key of ``us_live.py``.

STATUS of the live part: written from the exchange's published API
reference (docs.polymarket.us, read on 12 November 2026) and exercised in
tests against a stand-in for the network. **It has never been run against
the exchange.** No credentials were available when it was written. The
steps before it is trusted with money are in docs/12_us_taker.md.

What the live part will and will not do:

* every order is a limit order at the price of the bid (or offer) it was
  decided on, filled at once or cancelled ("immediate or cancel"). It is
  never an order "at the market", and nothing of it is left resting;
* a sale is refused here above 5 cents and a purchase below 95 cents,
  whatever the rule or the configuration says, and no order is larger than
  ``MAX_CAP`` contracts;
* an order request is sent once and never repeated. If its answer is lost,
  the market is marked "not known" and left alone for a person to look at;
* it never buys back, never cancels, never touches any other market.
"""

from __future__ import annotations

import csv
import json
import math
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

from . import lasttick_rule as rule
from .us_recorder import _amount, parse_book

MAX_MONEY = 10_000.0        # dollars that may be tied up at one settlement time: a limit in the code, whatever the configuration says
MAX_CAP = rule.CAP          # contracts a market, at most
MIN_QTY = 1.0               # nothing smaller than a contract is sent, and only whole contracts
SETTLE_AFTER = 60           # a position is looked up for settlement this long after its market ended
ACTION_FIELDS = ["ts", "mode", "slug", "side", "price", "wanted", "filled", "fee", "tied_up", "note", "left", "level", "gap", "reach"]
SETTLED_FIELDS = ["ts", "slug", "side", "price", "qty", "fee", "settle", "pnl"]


@dataclass
class TakerConfig:
    yardstick: str = "recent"            # "recent" (the second yardstick, with its brake) or "strict" (the first)
    money: float = 500.0                 # dollars that may be tied up at one settlement time
    cap: float = 500.0                   # contracts a market, at most
    coins: tuple[str, ...] = ("btc",)
    sides: tuple[str, ...] = ("sell",)   # "sell": sell "Yes" at 5c or less. "buy": buy "Yes" at 95c or more
    stop_on_loss: bool = True            # after any loss, send nothing more until a person removes the STOP file
    sweep: float = 40.0                  # seconds between two readings of one book
    reach_file: str = "config/lasttick_reach.json"

    def __post_init__(self) -> None:
        self.coins, self.sides = tuple(self.coins), tuple(self.sides)
        if self.yardstick not in ("recent", "strict"):
            raise ValueError(f"unknown yardstick {self.yardstick!r}")
        if not set(self.sides) <= {"sell", "buy"} or not self.sides:
            raise ValueError(f"sides must be 'sell', 'buy' or both, not {self.sides!r}")
        if not 0 < self.money <= MAX_MONEY:
            raise ValueError(f"money must be above 0 and at most {MAX_MONEY:,.0f}")
        if not MIN_QTY <= self.cap <= MAX_CAP:
            raise ValueError(f"cap must be between {MIN_QTY:g} and {MAX_CAP:g} contracts")

    @classmethod
    def load(cls, path: Path) -> "TakerConfig":
        raw = {k: v for k, v in json.loads(Path(path).read_text()).items() if not k.startswith("_")}
        return cls(**raw)

    def yardsticks(self, root: Path) -> tuple[dict[str, dict[int, float]], dict[str, float] | None]:
        """The reach table of the chosen yardstick, and its brake if it has one."""
        path = Path(self.reach_file) if Path(self.reach_file).is_absolute() else root / self.reach_file
        if self.yardstick == "recent":
            return rule.load_recent(path)
        return rule.load_reach(path), None


@dataclass(frozen=True)
class Ticket:
    """One order: sell (or buy) ``qty`` contracts of "Yes" at ``price``, at once or not at all for the rest."""
    slug: str
    side: str
    price: float
    qty: float
    end: float

    def tied_up(self, qty: float | None = None) -> float:
        """Dollars this order ties up until the market settles, for ``qty`` contracts (all of it if not given)."""
        q = self.qty if qty is None else qty
        return q * ((1.0 - self.price) if self.side == "sell" else self.price)


@dataclass
class Fill:
    qty: float | None        # contracts filled; None if the answer was lost and it is not known
    price: float
    fee: float
    note: str = ""


class Taker(Protocol):
    def take(self, ticket: Ticket, book: dict[str, Any]) -> Fill: ...


def order_body(t: Ticket) -> dict[str, Any]:
    """One order as the API wants it. Raises rather than send anything outside the limits."""
    if t.side == "sell":
        if not 0.01 - 1e-9 <= t.price <= rule.SELL_AT_MOST + 1e-9:
            raise ValueError(f"a sale at {t.price} is outside 1c to {rule.SELL_AT_MOST * 100:.0f}c")
        intent = "ORDER_INTENT_BUY_SHORT"            # buying "No" is how the API says selling "Yes" short; the price stays the price of "Yes"
    elif t.side == "buy":
        if not rule.BUY_AT_LEAST - 1e-9 <= t.price <= 0.99 + 1e-9:
            raise ValueError(f"a purchase at {t.price} is outside {rule.BUY_AT_LEAST * 100:.0f}c to 99c")
        intent = "ORDER_INTENT_BUY_LONG"
    else:
        raise ValueError(f"unknown side {t.side!r}")
    if not MIN_QTY <= t.qty <= MAX_CAP or t.qty != math.floor(t.qty):
        raise ValueError(f"size {t.qty} is not a whole number of contracts between {MIN_QTY:g} and {MAX_CAP:g}")
    return {"marketSlug": t.slug, "type": "ORDER_TYPE_LIMIT", "price": {"value": f"{t.price:.4f}".rstrip("0").rstrip("."), "currency": "USD"},
            "quantity": int(t.qty), "tif": "TIME_IN_FORCE_IMMEDIATE_OR_CANCEL", "intent": intent,
            "manualOrderIndicator": "MANUAL_ORDER_INDICATOR_AUTOMATIC", "synchronousExecution": True, "maxBlockTime": "5"}


def read_fill(resp: dict[str, Any] | None, t: Ticket) -> Fill:
    """What an order's answer says was filled. The answer lists execution reports; each carries the order as it then stood."""
    filled, px, fee, rejected = None, None, 0.0, ""
    for e in (resp or {}).get("executions") or []:
        o = e.get("order") or {}
        cum = rule._f(o.get("cumQuantity"))
        if cum is not None and (filled is None or cum >= filled):
            filled = cum
            avg = o.get("avgPx")
            px = _amount(avg) if isinstance(avg, dict) else rule._f(avg)
        got = e.get("commissionNotionalCollected")
        got = _amount(got) if isinstance(got, dict) else rule._f(got)
        fee += got or 0.0
        if str(e.get("type") or "").endswith("REJECTED"):
            rejected = str(e.get("orderRejectReason") or e.get("text") or "rejected")
    if filled is None:
        return Fill(0.0, t.price, 0.0, f"rejected: {rejected}") if rejected else Fill(None, t.price, 0.0, "the answer carried no execution report")
    if filled <= 0:
        return Fill(0.0, t.price, 0.0, f"rejected: {rejected}" if rejected else "nothing filled")
    if px is None or px <= 0:
        px = t.price
    elif t.side == "sell" and px > 0.5:
        px = 1.0 - px                               # the answer gave the price of "No"
    if fee <= 0:
        fee = rule.THETA * px * (1.0 - px) * filled
    return Fill(filled, px, fee, "filled" if filled >= t.qty - 1e-9 else "filled in part")


class PaperTaker:
    """Fills an order against the very book it was decided on. Sends nothing."""

    def take(self, ticket: Ticket, book: dict[str, Any]) -> Fill:
        if ticket.side == "sell":
            px, shown = rule._f(book.get("bid1")), rule._f(book.get("bid_qty1"))
            ok = px is not None and px >= ticket.price - 1e-9
        else:
            px, shown = rule._f(book.get("ask1")), rule._f(book.get("ask_qty1"))
            ok = px is not None and px <= ticket.price + 1e-9
        qty = math.floor(min(ticket.qty, shown or 0.0)) if ok else 0.0
        if qty <= 0:
            return Fill(0.0, ticket.price, 0.0, "nothing filled")
        return Fill(float(qty), ticket.price, rule.THETA * ticket.price * (1.0 - ticket.price) * qty, "filled" if qty >= ticket.qty else "filled in part")


class LiveTaker:
    """Sends orders to Polymarket US through the connection of ``us_live.py``. See the module's warning before using it."""

    def __init__(self, wire: Any, preview: bool = False):
        self.wire, self.preview = wire, preview
        self.previews: list[Any] = []

    def take(self, ticket: Ticket, book: dict[str, Any]) -> Fill:
        body = order_body(ticket)                    # checked before anything is sent
        if self.preview:
            self.previews.append(self.wire._call("POST", "/v1/order/preview", body=body))
            return Fill(0.0, ticket.price, 0.0, "previewed, not sent")
        try:
            resp = self.wire._call("POST", "/v1/orders", body=body)
        except Exception as exc:                     # the request may or may not have reached the exchange: never send it again
            return Fill(None, ticket.price, 0.0, f"not known, look at the account: {str(exc)[:160]}")
        return read_fill(resp, ticket)


@dataclass
class Held:
    slug: str
    side: str
    price: float
    qty: float
    fee: float
    end: float
    ts: float

    def tied_up(self) -> float:
        return self.qty * ((1.0 - self.price) if self.side == "sell" else self.price)


@dataclass
class Counters:
    readings: int = 0
    orders: int = 0
    filled: int = 0
    unknown: int = 0
    settled: int = 0
    lost: int = 0
    pnl: float = 0.0
    errors: int = 0
    why: dict[str, int] = field(default_factory=dict)


class Engine:
    """Applies the rule of L1 to book readings as they come and places what it says through a broker."""

    def __init__(self, state: Path, cfg: TakerConfig, broker: Taker, reach: dict[str, dict[int, float]], brake: dict[str, float] | None = None,
                 mode: str = "paper", now: Callable[[], float] = time.time):
        self.state, self.cfg, self.broker, self.reach, self.brake, self.mode, self.now = Path(state), cfg, broker, reach, brake, mode, now
        self.state.mkdir(parents=True, exist_ok=True)
        saved = json.loads((self.state / "positions.json").read_text()) if (self.state / "positions.json").exists() else {}
        self.held: dict[str, Held] = {s: Held(**p) for s, p in (saved.get("held") or {}).items()}
        self.done: set[str] = set(saved.get("done") or [])          # markets an order has been sent to: never a second one
        self.latest: dict[str, tuple[float, float]] = {}            # coin -> (index level, the moment it is the level of)
        self.history: dict[str, dict[float, float]] = {}            # coin -> {moment: level}, for the brake only
        self.n = Counters()

    # ------------------------------------------------------------------ what it knows
    def on_index(self, coin: str, level: float, at: float) -> None:
        """A level of the index the exchange has just published: where the price is, as far as the rule may know."""
        level, at = rule._f(level), float(at)
        if level and level > 0 and (coin not in self.latest or at >= self.latest[coin][1]):
            self.latest[coin] = (level, at)
        self.on_history(coin, level, at)

    def on_history(self, coin: str, level: Any, at: float) -> None:
        """A level of the index at an earlier moment. Used for the brake and for nothing else."""
        level = rule._f(level)                       # a recording gives it as text
        if level and level > 0:
            self.history.setdefault(coin, {})[float(at)] = level

    def stopped(self) -> str | None:
        path = self.state / "STOP"
        return (path.read_text().strip() or "stopped by the file STOP") if path.exists() else None

    def tied_up(self, end: float) -> float:
        return sum(h.tied_up() for h in self.held.values() if h.end == end)

    # ------------------------------------------------------------------ one reading
    def on_book(self, market: dict[str, Any], row: dict[str, Any], ts: float) -> Fill | None:
        """One reading of one market's book. Sends at most one order, and never a second to the same market."""
        slug = market["slug"]
        self.n.readings += 1
        if slug in self.done or market.get("coin") not in self.cfg.coins:
            return None
        level, at = self.latest.get(market.get("coin", ""), (None, None))
        history = sorted(self.history.get(market.get("coin", ""), {}).items())
        trade, why = rule.decide(market, row, ts, level, at, self.reach, self.brake, history)
        self.n.why[why] = self.n.why.get(why, 0) + 1
        if trade is None or trade["side"] not in self.cfg.sides:
            return None
        if self.stopped():
            return None
        end = float(market["end"])
        per = (1.0 - trade["price"]) if trade["side"] == "sell" else trade["price"]
        room = self.cfg.money - self.tied_up(end)
        qty = math.floor(min(trade["qty"], self.cfg.cap, MAX_CAP, room / per if per > 0 else 0.0) + 1e-9)
        if qty < MIN_QTY:
            return None                                 # no money left for this settlement time: the market may be tried again if some is freed
        ticket = Ticket(slug, trade["side"], trade["price"], float(qty), end)
        self.done.add(slug)
        self._save()                                    # before the order goes out: a crash after sending must not lead to a second order
        self.n.orders += 1
        fill = self.broker.take(ticket, row)
        if fill.qty is None:
            self.n.unknown += 1
        elif fill.qty > 0:
            self.n.filled += 1
            self.held[slug] = Held(slug, ticket.side, fill.price, fill.qty, fill.fee, end, ts)
        self._act({"ts": round(ts, 1), "mode": self.mode, "slug": slug, "side": ticket.side, "price": ticket.price, "wanted": ticket.qty,
                   "filled": "" if fill.qty is None else fill.qty, "fee": round(fill.fee, 4), "tied_up": round(ticket.tied_up(fill.qty or 0.0), 2), "note": fill.note,
                   "left": round(trade["left"], 1), "level": trade["level"], "gap": round(trade["gap"], 5), "reach": round(trade["reach"], 5)})
        self._save()
        return fill

    # ------------------------------------------------------------------ afterwards
    def settle(self, slug: str, value: float, ts: float | None = None) -> float | None:
        """A held market has settled at ``value`` (what "Yes" paid). Returns what the position made."""
        h = self.held.pop(slug, None)
        if h is None:
            return None
        pnl = rule.pnl({"qty": h.qty, "price": h.price, "side": h.side, "fee": h.fee}, float(value))
        self.n.settled += 1
        self.n.pnl += pnl
        _append(self.state / "settled.csv", SETTLED_FIELDS, {"ts": round(self.now() if ts is None else ts, 1), "slug": slug, "side": h.side, "price": h.price,
                                                             "qty": h.qty, "fee": round(h.fee, 4), "settle": value, "pnl": round(pnl, 4)})
        if pnl < -1e-9:
            self.n.lost += 1
            if self.cfg.stop_on_loss:
                (self.state / "STOP").write_text(f"stopped after a loss of ${-pnl:,.2f} on {slug}, settled {stamp(self.now() if ts is None else ts)}. "
                                                 "A loss means the rule or its facts were wrong. Remove this file only after looking.\n")
        self._save()
        return pnl

    def due(self, ts: float) -> list[str]:
        """Held markets that ended long enough ago to have settled."""
        return [s for s, h in self.held.items() if ts >= h.end + SETTLE_AFTER]

    # ------------------------------------------------------------------ the live loop
    def run(self, minutes: float, us: Any, sleep: Callable[[float], None] = time.sleep, max_cycles: int | None = None) -> dict[str, Any]:
        """Follow the open crypto markets for ``minutes``, reading each book in the rule's window and acting on it at once."""
        from . import us_lasttick as lt

        started, markets, listed_at, cycles, tried = self.now(), {}, -1e18, 0, set()
        lead = rule.FIRST + 90.0
        while self.now() - started < minutes * 60.0 and (max_cycles is None or cycles < max_cycles):
            t = self.now()
            soon = any(m["horizon"] not in lt.SKIP and m["end"] - lead - lt.LIST_QUIET <= t <= m["end"] + lt.AFTER for m in markets.values())
            if t - listed_at >= (lt.LIST_BUSY if soon else lt.LIST_QUIET):
                try:
                    fresh = {m["slug"]: m for m in (lt.terms(raw) for raw in us.iter_markets(closed=False, categories="crypto")) if m is not None}
                    markets = {**{s: m for s, m in markets.items() if t <= m["end"] + lt.AFTER}, **fresh}
                    listed_at = t
                    for coin, lv in lt.index_levels(markets, t).items():
                        self.on_index(coin, lv["level"], lv["at"])
                except Exception:
                    self.n.errors += 1
            active = [s for s in lt.followed(markets, t, lead) if markets[s]["coin"] in self.cfg.coins and s not in self.done and t < markets[s]["end"]]
            if active and self.brake is not None:
                self._look_up_levels(us, {markets[s]["coin"] for s in active}, t, tried)
            for slug in active:                          # one after the other: each order follows its own reading at once
                try:
                    self.on_book(markets[slug], parse_book(us.book(slug)), self.now())
                except Exception:
                    self.n.errors += 1
            for slug in self.due(self.now()):
                try:
                    value = us.settlement(slug)
                    if value is not None:
                        self.settle(slug, value)
                except Exception:
                    self.n.errors += 1
            cycles += 1
            pause = (self.cfg.sweep if active else 20.0) - (self.now() - t)
            if pause > 0 and self.now() - started + pause < minutes * 60.0:
                sleep(pause)
            elif pause > 0:
                break
        self.write_status()
        return {"mode": self.mode, "minutes": round((self.now() - started) / 60.0, 1), "cycles": cycles, **{k: v for k, v in asdict(self.n).items() if k != "why"}}

    def _look_up_levels(self, us: Any, coins: set[str], t: float, tried: set[tuple[str, float]]) -> None:
        """The brake needs the index at each five-minute mark of the last hour. Ask for the marks not yet known (public, no key)."""
        first = int(t - rule.BRAKE_WINDOW - rule.BRAKE_STEP) // rule.BRAKE_STEP * rule.BRAKE_STEP
        for coin in sorted(coins):
            if coin not in rule.PRODUCT:
                continue
            for at in range(first, int(t) + 1, rule.BRAKE_STEP):
                if float(at) in self.history.get(coin, {}) or (coin, float(at)) in tried:
                    continue
                tried.add((coin, float(at)))
                try:
                    self.on_history(coin, _amount((us.market(rule.updown_slug(coin, "5m", at)).get("assetPriceTerms") or {}).get("priceToBeat")), float(at))
                except Exception:
                    self.n.errors += 1

    # ------------------------------------------------------------------ files
    def _save(self) -> None:
        tmp = self.state / "positions.json.tmp"
        tmp.write_text(json.dumps({"held": {s: asdict(h) for s, h in self.held.items()}, "done": sorted(self.done)}, indent=1))
        tmp.replace(self.state / "positions.json")

    def _act(self, row: dict[str, Any]) -> None:
        _append(self.state / "actions.csv", ACTION_FIELDS, row)

    def write_status(self) -> None:
        (self.state / "STATUS.md").write_text(self.status_text())

    def status_text(self) -> str:
        n = self.n
        lines = ["# Sales to the last-tick bids", "",
                 f"*Written by `kht us-take` at {stamp(self.now())}, mode: {self.mode}."
                 + (" Nothing was sent anywhere.*" if self.mode in ("paper", "replay") else "*"), "",
                 f"- yardstick: {self.cfg.yardstick}; coins: {', '.join(self.cfg.coins)}; sides: {', '.join(self.cfg.sides)}; "
                 f"at most ${self.cfg.money:,.0f} tied up at one settlement time and {self.cfg.cap:g} contracts a market",
                 f"- readings: {n.readings:,}; orders: {n.orders}; filled: {n.filled}; answer not known: {n.unknown}; errors: {n.errors}",
                 f"- settled: {n.settled}; lost: {n.lost}; made in all: ${n.pnl:,.2f}",
                 f"- held now: {len(self.held)} markets, ${sum(h.tied_up() for h in self.held.values()):,.2f} tied up"]
        if self.stopped():
            lines.append(f"- **STOPPED:** {self.stopped()}")
        if n.why:
            lines += ["", "| How the rule judged a reading | Readings |", "|---|---:|"] + [f"| {k} | {v:,} |" for k, v in sorted(n.why.items(), key=lambda kv: -kv[1])]
        return "\n".join(lines) + "\n"


def replay(engine: Engine, books: list[dict[str, Any]], markets: dict[str, dict[str, Any]], index: list[dict[str, Any]],
           levels: dict[str, list[tuple[float, float]]] | None = None, settlements: dict[str, float] | None = None) -> dict[str, Any]:
    """Run the engine over a recording of ``kht us-lasttick``: its book readings and index levels in the order they came.

    ``levels`` are index levels looked up since, by coin, for the brake
    only. ``settlements`` is what "Yes" paid in each market, where known.
    """
    for coin, rows in (levels or {}).items():
        for at, level in rows:
            engine.on_history(coin, level, at)
    for r in index:                                   # as the scorer does: every recorded level may serve the brake once its moment has passed
        engine.on_history(r["coin"], r["level"], float(r["at"]))
    events = [(float(r["ts"]), 0, i, r) for i, r in enumerate(index)] + [(float(r["ts"]), 1, i, r) for i, r in enumerate(books)]
    for ts, kind, _, r in sorted(events, key=lambda e: e[:3]):
        if kind == 0:
            if r["coin"] not in engine.latest or float(r["at"]) >= engine.latest[r["coin"]][1]:
                engine.latest[r["coin"]] = (float(r["level"]), float(r["at"]))
        else:
            m = markets.get(r["slug"])
            if m is not None:
                engine.on_book(m, r, ts)
    for slug in list(engine.held):
        if settlements and slug in settlements:
            engine.settle(slug, settlements[slug], ts=engine.held[slug].end + SETTLE_AFTER)
    engine.write_status()
    return {"mode": engine.mode, **{k: v for k, v in asdict(engine.n).items() if k != "why"}}


def load_recording(rec: Path) -> dict[str, Any]:
    """What ``kht us-lasttick`` wrote under ``rec``, ready for ``replay``: readings, markets, index levels, and what is known since.

    Read with the standard library only, so that a replay needs nothing
    the trading engine itself does not need.
    """
    import gzip

    books: list[dict[str, Any]] = []
    index: list[dict[str, Any]] = []
    markets: dict[str, dict[str, Any]] = {}
    for run in sorted((rec / "runs").glob("*")) if (rec / "runs").exists() else []:
        if (run / "books.csv.gz").exists():
            with gzip.open(run / "books.csv.gz", "rt", newline="") as fh:
                books += list(csv.DictReader(fh))
        if (run / "index.csv").exists():
            with (run / "index.csv").open(newline="") as fh:
                index += list(csv.DictReader(fh))
        if (run / "markets.csv").exists():
            with (run / "markets.csv").open(newline="") as fh:
                for m in csv.DictReader(fh):
                    old = markets.get(m["slug"])
                    if old is not None and not m.get("price_to_beat"):
                        m["price_to_beat"] = old.get("price_to_beat", "")       # a market followed in two runs: the price to beat is whichever run had it
                    markets[m["slug"]] = m
    levels: dict[str, list[tuple[float, float]]] = {}
    if (rec / "levels.csv").exists():
        with (rec / "levels.csv").open(newline="") as fh:
            for r in csv.DictReader(fh):
                if rule._f(r.get("level")):
                    levels.setdefault(r["coin"], []).append((float(r["at"]), float(r["level"])))
    settlements: dict[str, float] = {}
    if (rec / "settlements.csv").exists():
        with (rec / "settlements.csv").open(newline="") as fh:
            for r in csv.DictReader(fh):
                if rule._f(r.get("settle")) is not None:
                    settlements[r["slug"]] = float(r["settle"])
    return {"books": books, "markets": markets, "index": index, "levels": levels, "settlements": settlements}


def _append(path: Path, fields: list[str], row: dict[str, Any]) -> None:
    new = not path.exists()
    with path.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)


def stamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
