"""Rest small orders before games on Polymarket US, on paper or for real.

This is the system that the paper test of docs/09_sports_rewards.md would
turn into if it passes. It rests an order on each side of chosen games in
the six hours before they start, at the price where other people's size
is, to be paid the exchange's published reward. It never takes a price:
every order is sent as one that may only rest. Every order expires by
itself a few minutes after it was last sent, and in any case ten minutes
before the game, so that nothing is left in a book if this program stops.
How to run it, and what it must not be trusted with, are in
docs/10_us_quoter.md.

Two brokers:

* ``PaperBroker`` keeps the orders in memory and fills them from the real
  order books, by the rules of the paper test. It needs no account.
* ``kht.trading.us_live.LiveUSBroker`` sends them to the exchange. It was
  written from the published API and has never been run against it.

Where the orders rest and how a book is scored are taken from
``us_rewards``, so the paper test and this system cannot drift apart.

Only the standard library and ``requests`` are used here.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

from ..api.polymarket_us import PolymarketUS
from . import us_rewards as rw
from .us_recorder import _append

MAX_SIZE = 500.0            # contracts a side: a limit in the code, whatever the configuration says
MAX_GAMES = 100
MIN_QTY = 1.0               # nothing smaller than a contract is sent
SETTLE_AFTER = 3 * 3600     # a paper position is looked up for settlement this long after its game started
BUY_YES, SELL_NO = "ORDER_INTENT_BUY_LONG", "ORDER_INTENT_SELL_SHORT"       # both buy the instrument: they rest on the bid
SELL_YES, BUY_NO = "ORDER_INTENT_SELL_LONG", "ORDER_INTENT_BUY_SHORT"       # both sell it: they rest on the offer
ACTION_FIELDS = ["ts", "action", "slug", "side", "intent", "price", "qty", "expires", "id", "why"]
CYCLE_FIELDS = ["ts", "mode", "candidates", "games", "orders", "placed", "cancelled", "renewed", "filled_games", "at_risk", "equity", "reward_formula", "errors"]
LOG_EVERY = 10              # a line goes to cycles.csv every this many cycles, and whenever something was filled
SETTLED_FIELDS = ["ts", "slug", "bought", "sold", "cost", "proceeds", "settle", "pnl"]


@dataclass(frozen=True)
class QuoterConfig:
    size: float = 100.0                 # contracts on each side of a game
    programmes: tuple[str, ...] = ("itf_moneyline", "utr_moneyline")     # lower-tour tennis: where resting has cost less than it is paid (docs/09, section 4)
    max_games: int = 20                 # games rested in at once
    max_at_risk: float = 1200.0         # dollars: what positions can still lose, plus what every resting order could lose if filled
    max_day_loss: float = 150.0         # dollars lost since midnight UTC at which everything is pulled and the program stops
    min_reward: float = 1.2             # dollars a game must be expected to earn by the formula; the exchange pays nothing under $1
    min_lead: float = 1800.0            # a game closer than this to the time its orders are pulled is not started
    max_filled_games: int = 5           # with this many games holding a position, no new game is started
    refresh: float = 30.0               # seconds between cycles
    scan: float = 300.0                 # seconds between readings of every candidate's book
    expire: float = 180.0               # seconds an order lives after it was last sent
    renew: float = 90.0                 # an order with less than this left is sent again

    def __post_init__(self) -> None:
        if not MIN_QTY <= self.size <= MAX_SIZE:
            raise ValueError(f"size must be between {MIN_QTY:g} and {MAX_SIZE:g} contracts")
        if not 0 < self.max_games <= MAX_GAMES:
            raise ValueError(f"max_games must be between 1 and {MAX_GAMES}")
        if self.renew >= self.expire:
            raise ValueError("renew must be shorter than expire")
        if self.expire < 2 * self.refresh:
            raise ValueError("an order must live at least two cycles, or it would lapse between them")

    @classmethod
    def load(cls, path: Path) -> "QuoterConfig":
        raw = json.loads(Path(path).read_text())
        raw.pop("_comment", None)
        unknown = set(raw) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"unknown settings in {path}: {sorted(unknown)}")
        if "programmes" in raw:
            raw["programmes"] = tuple(raw["programmes"])
        return cls(**raw)


@dataclass
class Order:
    id: str
    slug: str
    side: str               # "bid" or "ask": the side of the book it rests on
    intent: str
    price: float            # always the price of "Yes", as the exchange's API has it
    qty: float              # what is left of it
    expires: float


@dataclass(frozen=True)
class Want:
    slug: str
    side: str
    intent: str
    price: float
    qty: float
    expires: float

    def worst(self) -> float:
        """Dollars this order can lose if it is filled and the game goes against it."""
        return self.qty * (self.price if self.side == "bid" else 1.0 - self.price)


@dataclass
class Position:
    bought: float = 0.0     # contracts of "Yes" bought in all: what the bids have been filled
    sold: float = 0.0       # contracts sold in all: what the offers have been filled
    cost: float = 0.0       # dollars paid for what was bought
    proceeds: float = 0.0   # dollars received for what was sold

    @property
    def net(self) -> float:
        return self.bought - self.sold

    def at_risk(self) -> float:
        """The most this position can still lose: what it would be worth at the worse result, against what was paid."""
        return max(self.cost - self.proceeds - min(self.net, 0.0), 0.0)

    def value(self, price: float) -> float:
        """What it is worth with "Yes" at ``price``, counting the cash already paid and received."""
        return self.proceeds - self.cost + self.net * price


class Broker(Protocol):
    def open_orders(self, slugs: list[str]) -> list[Order]: ...
    def positions(self) -> dict[str, Position]: ...
    def place(self, wants: list[Want]) -> list[str]: ...
    def cancel(self, orders: list[Order]) -> None: ...
    def cancel_all(self, slugs: list[str]) -> None: ...
    def equity(self, marks: dict[str, float]) -> float | None: ...


def wants_for_game(game: dict[str, Any], q: dict[str, Any], pos: Position, cfg: QuoterConfig, now: float) -> tuple[list[Want], list[Want]]:
    """The orders to have resting in one game: those that reduce its position, and those that open one.

    Each side is filled ``cfg.size`` contracts at most over the life of the
    game: what a side has been filled is not offered again. Buying back
    contracts we are short of is sent as a "sell No", and selling contracts
    we hold as a "sell Yes"; either can only shrink the position. The rest
    of a side is sent as an opening order ("buy Yes" on the bid, "buy No"
    on the offer), which the caller may refuse for lack of room.
    """
    if not q.get("quoting"):
        return [], []
    expires = min(game["start"] - rw.PULL, now + cfg.expire)
    if expires - now < 5.0:
        return [], []
    closing: list[Want] = []
    opening: list[Want] = []
    net = pos.net
    for side, price, done, held, close_intent, open_intent in (("bid", q["bid_px"], pos.bought, max(-net, 0.0), SELL_NO, BUY_YES),
                                                                ("ask", q["ask_px"], pos.sold, max(net, 0.0), SELL_YES, BUY_NO)):
        left = cfg.size - done
        close = _whole(min(left, held))
        if close >= MIN_QTY:
            closing.append(Want(game["slug"], side, close_intent, price, close, expires))
        more = _whole(left - close)
        if more >= MIN_QTY:
            opening.append(Want(game["slug"], side, open_intent, price, more, expires))
    return closing, opening


def _whole(qty: float) -> float:
    return float(int(qty + 1e-9))


def expected_reward(game: dict[str, Any], q: dict[str, Any], size: float, now: float) -> float:
    """Dollars the formula would pay orders of ``size`` from now until they are pulled, if the book stayed as it is."""
    share = (q.get("share") or {}).get(int(size)) if q.get("quoting") and float(size).is_integer() else None
    left = game["start"] - rw.PULL - max(now, game["start"] - rw.WINDOW)
    if share is None or left <= 0:
        return 0.0
    return game["pool"] / game["markets_in_event"] * (share[0] + share[1]) / (2.0 * rw.WINDOW) * left


def choose(cands: list[dict[str, Any]], resting: set[str], filled: set[str], cfg: QuoterConfig) -> list[str]:
    """Which games to rest in.

    A game already rested in stays while its book can be rested in: what
    it has accrued counts towards the dollar minimum only if it goes on. A
    game with a position stays so that its other side can close it. New
    games are added by what the formula expects them to pay, best first,
    and none is added while too many games hold a position.
    """
    chosen = [c["slug"] for c in cands if c["quoting"] and (c["slug"] in resting or c["slug"] in filled)]
    if len(filled) >= cfg.max_filled_games:
        return chosen
    new = [c for c in cands if c["quoting"] and c["slug"] not in chosen and c["lead"] >= cfg.min_lead and c["accrued"] + c["expected"] >= cfg.min_reward]
    new.sort(key=lambda c: -c["expected"])
    return chosen + [c["slug"] for c in new[: max(cfg.max_games - len(chosen), 0)]]


def reconcile(wants: list[Want], open_orders: list[Order], now: float, cfg: QuoterConfig) -> tuple[list[Order], list[Want]]:
    """What to cancel and what to send so that the books hold exactly ``wants``.

    An open order is kept if it is wanted as it stands (same market, side,
    kind, price and size) and still has ``cfg.renew`` seconds to live.
    Every other open order in those markets is cancelled, and whatever is
    then missing is sent.
    """
    left = list(wants)
    cancel: list[Order] = []
    for o in open_orders:
        match = next((w for w in left if w.slug == o.slug and w.side == o.side and w.intent == o.intent
                      and abs(w.price - o.price) < 1e-9 and abs(w.qty - o.qty) < 1e-6), None)
        if match is not None and o.expires - now >= cfg.renew:
            left.remove(match)
        else:
            cancel.append(o)
    return cancel, left


class PaperBroker:
    """Orders kept in memory and filled from the real order books. No account, nothing sent."""

    def __init__(self) -> None:
        self.orders: dict[str, Order] = {}
        self.pos: dict[str, Position] = {}
        self.cash = 0.0             # dollars realised by positions that have settled
        self.n = 0

    def open_orders(self, slugs: list[str]) -> list[Order]:
        want = set(slugs)
        return [o for o in self.orders.values() if o.slug in want]

    def positions(self) -> dict[str, Position]:
        return self.pos

    def place(self, wants: list[Want]) -> list[str]:
        ids = []
        for w in wants:
            self.n += 1
            oid = f"paper-{self.n}"
            self.orders[oid] = Order(oid, w.slug, w.side, w.intent, w.price, w.qty, w.expires)
            ids.append(oid)
        return ids

    def cancel(self, orders: list[Order]) -> None:
        for o in orders:
            self.orders.pop(o.id, None)

    def cancel_all(self, slugs: list[str]) -> None:
        self.orders.clear()

    def equity(self, marks: dict[str, float]) -> float:
        """Settled results plus open positions at the given prices (at 50c where no price is known)."""
        return self.cash + sum(p.value(marks.get(s, 0.5)) for s, p in self.pos.items())

    def save(self, path: Path) -> None:
        """Keep the positions and the settled total between runs. Orders are not kept: a run pulls them when it ends."""
        path.write_text(json.dumps({"cash": self.cash, "n": self.n, "positions": {s: asdict(p) for s, p in self.pos.items()}}, sort_keys=True))

    @classmethod
    def load(cls, path: Path) -> "PaperBroker":
        b = cls()
        if path.exists():
            raw = json.loads(path.read_text())
            b.cash, b.n = float(raw.get("cash", 0.0)), int(raw.get("n", 0))
            b.pos = {s: Position(**p) for s, p in (raw.get("positions") or {}).items()}
        return b

    # ------------------------------------------------------------ the paper exchange
    def expire(self, now: float) -> None:
        for oid in [oid for oid, o in self.orders.items() if o.expires <= now]:
            del self.orders[oid]

    def trade(self, slug: str, prev: dict[str, Any], cur: dict[str, Any], t0: float) -> list[dict[str, Any]]:
        """Fill this market's resting orders from what its book did between two readings (the rule of docs/09, section 5)."""
        mine = [o for o in self.orders.values() if o.slug == slug]
        if not mine:
            return []
        bids, asks = [o for o in mine if o.side == "bid"], [o for o in mine if o.side == "ask"]
        q = {"bid_px": max((o.price for o in bids), default=-1.0), "ask_px": min((o.price for o in asks), default=2.0)}
        out = []
        for h in rw.hits(prev, q, cur, t0):
            size = max(float(h["dv"] or 0.0), float(h["cross_qty"] or 0.0))
            for o in (bids if h["side"] == "bid" else asks):
                if abs(o.price - h["px"]) > 1e-9 or size <= 1e-9:
                    continue
                qty = min(o.qty, size)
                size -= qty
                o.qty -= qty
                p = self.pos.setdefault(slug, Position())
                if o.side == "bid":
                    p.bought, p.cost = p.bought + qty, p.cost + qty * o.price
                else:
                    p.sold, p.proceeds = p.sold + qty, p.proceeds + qty * o.price
                out.append({"slug": slug, "side": o.side, "intent": o.intent, "price": o.price, "qty": round(qty, 4), "id": o.id})
                if o.qty < MIN_QTY:
                    self.orders.pop(o.id, None)
        return out

    def settle(self, slug: str, price: float) -> dict[str, Any]:
        """Close a position at the price its game settled at."""
        p = self.pos.pop(slug)
        pnl = p.value(price)
        self.cash += pnl
        return {"slug": slug, "bought": round(p.bought, 4), "sold": round(p.sold, 4), "cost": round(p.cost, 4), "proceeds": round(p.proceeds, 4),
                "settle": price, "pnl": round(pnl, 4)}


@dataclass
class Resting:
    """One game as it was left at the end of a cycle: other people's book, and what of ours rests in it."""
    ts: float
    book: dict[str, Any]                                  # other people's orders as read: scored with ours added, and paper orders are filled against the next
    bid: tuple[float, float] | None                       # our price and size
    ask: tuple[float, float] | None


@dataclass
class Engine:
    state: Path
    cfg: QuoterConfig
    broker: Broker
    us: PolymarketUS
    mode: str = "paper"
    now: Callable[[], float] = time.time
    schedule: dict[str, dict[str, Any]] = field(default_factory=dict)
    quotes: dict[str, dict[str, Any]] = field(default_factory=dict)       # slug -> its book as last read and scored, with the time
    resting: dict[str, Resting] = field(default_factory=dict)
    accrued: dict[str, dict[str, float]] = field(default_factory=dict)    # slug -> US date -> dollars by the formula
    day: tuple[str, float] | None = None                                  # the UTC date and the equity it began with
    starts: dict[str, float] = field(default_factory=dict)                # slug -> when its game starts, for every market we sent an order to
    checked: dict[str, float] = field(default_factory=dict)               # slug -> when its settlement was last looked up
    read_at: float = -1e18
    scanned_at: float = -1e18
    errors: int = 0
    cycles: int = 0

    def __post_init__(self) -> None:
        self.state.mkdir(parents=True, exist_ok=True)
        path = self.state / "accrued.json"
        if path.exists():
            self.accrued = json.loads(path.read_text())
        path = self.state / "starts.json"
        if path.exists():
            self.starts = {s: float(v) for s, v in json.loads(path.read_text()).items()}

    # ---------------------------------------------------------------- reading
    def games(self, t: float) -> dict[str, dict[str, Any]]:
        """The games that may be rested in now: the configured programmes, a pool of their own, inside their six hours."""
        if t - self.read_at >= rw.REFRESH:
            try:
                self.schedule = rw.games(list(self.us.iter_incentives(statuses="active")))
                self.read_at = t
            except Exception:
                self.errors += 1
        return {s: g for s, g in self.schedule.items()
                if g["program"].startswith(self.cfg.programmes) and g["markets_in_event"] == 1 and g["start"] - rw.WINDOW <= t < g["start"] - rw.PULL}

    def read(self, slugs: list[str], games: dict[str, dict[str, Any]], mine: dict[tuple[str, str, float], float]) -> dict[str, dict[str, Any]]:
        """Read these books now, as other people's orders alone.

        A book that cannot be read, or is not open, is left out, and nothing
        is rested blind. Our own resting orders (``mine``) are taken out of
        a real book before it is looked at. Otherwise the price "where other
        people's size is" could be the price where only our own order is,
        and we would stay there after everyone else had left.
        """
        books = {}
        for slug in slugs:
            try:
                raw = self.us.book(slug)
            except Exception:
                self.errors += 1
                continue
            if not raw or (raw.get("state") or "MARKET_STATE_OPEN") != "MARKET_STATE_OPEN":
                continue
            b = rw.read_book(raw)
            if mine:
                b = {**b, "bids": _without(b["bids"], slug, "bid", mine), "asks": _without(b["asks"], slug, "ask", mine)}
            books[slug] = b
            self.quotes[slug] = {**rw.quote_state(b, games[slug]), "ts": self.now()}
        return books

    # ---------------------------------------------------------------- scoring what has passed
    def credit(self, slug: str, game: dict[str, Any], prev: Resting, t: float) -> None:
        """Add what the formula pays our orders for the time since this game was last looked at."""
        lo, hi = max(prev.ts, game["start"] - rw.WINDOW), min(t, game["start"] - rw.PULL)
        if hi <= lo or t - prev.ts > rw.MAX_GAP or (prev.bid is None and prev.ask is None):
            return
        bids, asks = prev.book["bids"], prev.book["asks"]
        tick = rw.infer_tick([p for p, _ in bids + asks]) if bids or asks else 0.01
        at: dict[str, tuple[float | None, float]] = {}
        for side, mine, levels in (("bid", prev.bid, bids), ("ask", prev.ask, asks)):
            if mine is None:
                at[side] = (rw.reward_walk(levels, game["target"], game["discount"], tick)[0], 0.0)
            else:
                at[side] = rw.side_with_order(_with_level(levels, mine[0], side), mine[0], mine[1], game["target"], game["discount"], tick)
        paid = rw._paid(at["bid"][0], at["ask"][0], game["max_spread"])
        share = (at["bid"][1] if paid[0] else 0.0) + (at["ask"][1] if paid[1] else 0.0)
        by_date = self.accrued.setdefault(slug, {})
        key = rw.et_date(prev.ts)
        by_date[key] = by_date.get(key, 0.0) + game["pool"] / game["markets_in_event"] * share * (hi - lo) / (2.0 * rw.WINDOW)

    def settle_paper(self, t: float) -> list[dict[str, Any]]:
        """On paper, close the positions of games that are over at what they settled at."""
        if not isinstance(self.broker, PaperBroker):
            return []
        out = []
        for slug in list(self.broker.pos):
            if t < self.starts.get(slug, 0.0) + SETTLE_AFTER or t - self.checked.get(slug, -1e18) < 600.0:
                continue
            self.checked[slug] = t
            try:
                price = self.us.settlement(slug)
            except Exception:
                self.errors += 1
                continue
            if price is not None:
                out.append({"ts": int(t), **self.broker.settle(slug, float(price))})
        return out

    # ---------------------------------------------------------------- one cycle
    def step(self) -> dict[str, Any]:
        t = self.now()
        if (self.state / "STOP").exists():
            return self.stop("the file STOP exists")
        games = self.games(t)
        had = set(self.resting)
        known = sorted(set(self.starts) | set(games))
        mine: dict[tuple[str, str, float], float] = {}
        if self.mode != "paper":                        # in a real book our own orders are among the levels that are read
            for o in self.broker.open_orders(known):
                key = (o.slug, o.side, round(o.price, 6))
                mine[key] = mine.get(key, 0.0) + o.qty
        # every cycle: the games we rest in, and a share of the others, oldest reading first, so that each is read once in cfg.scan seconds
        others = sorted((s for s in games if s not in had), key=lambda s: self.quotes.get(s, {}).get("ts", -1e18))
        share = len(others) if self.scanned_at < 0 else max(1, math.ceil(len(others) * self.cfg.refresh / self.cfg.scan))
        books = self.read([s for s in games if s in had] + others[:share], games, mine)
        self.scanned_at = t

        # 1. what happened since the last cycle
        fills: list[dict[str, Any]] = []
        for slug, prev in list(self.resting.items()):
            game = self.schedule.get(slug)
            if game is not None:
                self.credit(slug, game, prev, t)
                if slug in books and isinstance(self.broker, PaperBroker) and t - prev.ts <= rw.MAX_GAP:
                    fills += self.broker.trade(slug, prev.book, books[slug], prev.ts)
        self.resting.clear()
        if isinstance(self.broker, PaperBroker):
            self.broker.expire(t)                   # after the fills: an order that lapsed in the interval was resting for part of it
        settled = self.settle_paper(t)

        # 2. where things stand
        positions = self.broker.positions()
        filled = {s for s, p in positions.items() if abs(p.net) >= MIN_QTY and s in games}
        at_risk = sum(p.at_risk() for p in positions.values())
        marks = {s: q["mid"] for s, q in self.quotes.items() if q.get("mid") is not None}
        equity = self.broker.equity(marks)
        today = datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")
        if equity is not None:
            if self.day is None or self.day[0] != today:
                self.day = (today, equity)
            if self.day[1] - equity >= self.cfg.max_day_loss:
                return self.stop(f"down ${self.day[1] - equity:,.2f} since midnight UTC, at the limit of ${self.cfg.max_day_loss:,.2f}")

        # 3. which games, and which orders
        cands = []
        for slug, game in games.items():
            q = self.quotes.get(slug)
            seen = q is not None and (slug in books or (slug not in had and t - q["ts"] <= self.cfg.scan + self.cfg.refresh))
            cands.append({"slug": slug, "quoting": bool(seen and q.get("quoting")), "lead": game["start"] - rw.PULL - t,
                          "expected": expected_reward(game, q or {}, self.cfg.size, t), "accrued": sum(self.accrued.get(slug, {}).values())})
        chosen = choose(cands, had, filled, self.cfg)
        books.update(self.read([s for s in chosen if s not in books], games, mine))      # nothing is sent on an old reading
        open_orders = self.broker.open_orders(known)
        wants: list[Want] = []
        room = self.cfg.max_at_risk - at_risk
        for slug in chosen:
            if slug not in books:
                continue
            closing, opening = wants_for_game(games[slug], self.quotes[slug], positions.get(slug, Position()), self.cfg, t)
            wants += closing
            worst = max((sum(w.worst() for w in opening if w.side == side) for side in ("bid", "ask")), default=0.0)
            if opening and worst <= room + 1e-9:        # both sides cannot lose together: the worse one is what the game can cost
                wants += opening
                room -= worst
        cancel, send = reconcile(wants, open_orders, t, self.cfg)
        if len(send) > 4 * self.cfg.max_games + 8:
            return self.stop(f"{len(send)} orders to send in one cycle: more than this configuration can need")

        # 4. do it, and remember what is now resting
        if cancel:
            self.broker.cancel(cancel)
        ids = self.broker.place(send) if send else []
        for w in send:
            self.starts[w.slug] = games[w.slug]["start"]
        for slug in {w.slug for w in wants}:
            b = books[slug]
            bid = [(w.price, w.qty) for w in wants if w.slug == slug and w.side == "bid"]
            ask = [(w.price, w.qty) for w in wants if w.slug == slug and w.side == "ask"]
            self.resting[slug] = Resting(t, b, (bid[0][0], sum(q for _, q in bid)) if bid else None, (ask[0][0], sum(q for _, q in ask)) if ask else None)

        # 5. write it down. An order sent again unchanged, only to push its expiry out, is counted and not listed.
        same = lambda o, w: (o.slug, o.side, o.intent) == (w.slug, w.side, w.intent) and abs(o.price - w.price) < 1e-9 and abs(o.qty - w.qty) < 1e-6
        renewed_orders = [o for o in cancel if any(same(o, w) for w in send)]
        renewed_wants = [w for w in send if any(same(o, w) for o in cancel)]
        rows = [{"ts": int(t), "action": "fill", **f} for f in fills]
        rows += [{"ts": int(t), "action": "cancel", **asdict(o), "expires": int(o.expires)} for o in cancel if o not in renewed_orders]
        rows += [{"ts": int(t), "action": "place", "id": i, **asdict(w), "expires": int(w.expires)} for i, w in zip(ids, send) if w not in renewed_wants]
        _append(self.state / "actions.csv", ACTION_FIELDS, rows)
        _append(self.state / "settled.csv", SETTLED_FIELDS, settled)
        (self.state / "accrued.json").write_text(json.dumps(self.accrued, sort_keys=True))
        held = set(positions)
        self.starts = {s: v for s, v in self.starts.items() if s in held or t < v + SETTLE_AFTER}       # forget games that are over and flat
        self.quotes = {s: q for s, q in self.quotes.items() if s in games or s in held}
        (self.state / "starts.json").write_text(json.dumps(self.starts, sort_keys=True))
        if isinstance(self.broker, PaperBroker):
            self.broker.save(self.state / "paper.json")
        line = {"ts": int(t), "mode": self.mode, "candidates": len(games), "games": len(self.resting), "orders": len(open_orders) - len(cancel) + len(send),
                "placed": len(send), "cancelled": len(cancel), "renewed": len(renewed_wants), "filled_games": len(filled), "at_risk": round(at_risk, 2),
                "equity": "" if equity is None else round(equity, 2), "reward_formula": round(self.reward(), 4), "errors": self.errors}
        if self.cycles % LOG_EVERY == 0 or fills or settled:
            _append(self.state / "cycles.csv", CYCLE_FIELDS, [line])
        self.cycles += 1
        return line

    def reward(self, minimum: float = 0.0) -> float:
        """Dollars accrued by the formula; with ``minimum``, counting only a market and date that reached it."""
        return sum(v for by_date in self.accrued.values() for v in by_date.values() if v >= minimum)

    def stop(self, why: str) -> dict[str, Any]:
        """Take every order of ours out of the books, and say why."""
        try:
            self.broker.cancel_all(sorted(self.starts))
        finally:
            _append(self.state / "actions.csv", ACTION_FIELDS, [{"ts": int(self.now()), "action": "stop", "why": why}])
        self.resting.clear()
        return {"stopped": why}

    def run(self, minutes: float, sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
        """Cycle for ``minutes``. However it ends, the orders are pulled."""
        started = self.now()
        line: dict[str, Any] = {}
        try:
            while self.now() - started < minutes * 60.0:
                t = self.now()
                line = self.step()
                if "stopped" in line:
                    break
                pause = self.cfg.refresh - (self.now() - t)
                if pause > 0:
                    sleep(pause)
        finally:
            if "stopped" not in line:
                self.stop("the run ended")
            (self.state / "STATUS.md").write_text(self.status())
        return line

    def status(self) -> str:
        t = self.now()
        positions = self.broker.positions()
        lines = [f"# Orders before games on Polymarket US ({self.mode}): {stamp(t)}", "",
                 "On paper: nothing is sent to the exchange." if self.mode == "paper" else "LIVE: these are real orders.", "",
                 f"- reward accrued by the published formula: ${self.reward():,.2f}; counting only a market and date that reached $1: ${self.reward(1.0):,.2f}",
                 f"- games with a position: {len(positions)}; at risk in them: ${sum(p.at_risk() for p in positions.values()):,.2f}"]
        if isinstance(self.broker, PaperBroker):
            lines.append(f"- settled so far: ${self.broker.cash:,.2f}")
        lines += ["", "The reward is what the formula gives for the orders that rested. It is not money anyone has been paid.", ""]
        return "\n".join(lines)


def _without(levels: list[tuple[float, float]], slug: str, side: str, mine: dict[tuple[str, str, float], float]) -> list[tuple[float, float]]:
    """One side of a book as read, less our own orders that were resting in it."""
    out = []
    for px, qty in levels:
        qty -= mine.get((slug, side, round(px, 6)), 0.0)
        if qty > 1e-9:
            out.append((px, qty))
    return out


def _with_level(levels: list[tuple[float, float]], price: float, side: str) -> list[tuple[float, float]]:
    """The same side with an empty level at ``price`` if it has none there, so that an order can be scored at it."""
    if any(abs(px - price) < 1e-9 for px, _ in levels):
        return levels
    return sorted(levels + [(price, 0.0)], reverse=(side == "bid"))


def stamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
