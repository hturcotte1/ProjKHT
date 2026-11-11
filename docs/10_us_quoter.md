# 10 — The system that would rest the orders

*11 November 2026. On paper this runs. For real it has never run: no
account, no key and no order has been involved in writing it. It exists so
that if the paper test of `docs/09_sports_rewards.md` passes, and the owner
decides to try it with money, nothing has to be built first.*

## 1. What it does

`kht us-quote` rests one order on each side of a few chosen games on
Polymarket US during the six hours before they start, to be paid the
exchange's published reward for resting orders. It follows the rules of the
paper test, with the limits a real account needs added on top.

Every cycle, which is every 30 seconds:

1. It reads the public reward schedule (every half hour), the order books
   of the games it is resting in (every cycle), and a tenth of the other
   candidates' books, so that each is read once in five minutes.
2. It credits itself what the published formula pays its resting orders for
   the time since the last cycle. This is its own arithmetic, kept so that
   it can later be set beside what the exchange actually credits.
3. It chooses games: those it is already in, then the ones the formula
   expects to pay most, up to its limits.
4. For each chosen game it works out the two orders: at the price on each
   side where other people's orders add up to 20 contracts, as in the paper
   test.
5. It compares that with the orders that are open, cancels what is no
   longer right and sends what is missing.

Code: `src/kht/trading/us_quoter.py` (the decisions and the paper broker),
`src/kht/trading/us_live.py` (the connection to the exchange),
`config/us_quoter.json` (the settings).

## 2. Its limits

| Setting | Default | What it does |
|---|---:|---|
| `size` | 100 | Contracts on each side of a game. The code refuses more than 500 whatever the file says |
| `programmes` | the five of R1-thin | Only games in these reward programmes, and only where the market on who wins has the pool to itself |
| `max_games` | 20 | Games rested in at once |
| `max_at_risk` | $1,200 | What open positions can still lose, plus what the worse side of every game could lose if it were filled. A game that does not fit gets no opening orders |
| `max_day_loss` | $150 | Lost since midnight UTC at which every order is pulled and the program stops |
| `min_reward` | $1.20 | A game is started only if the formula expects it to earn this much; the exchange pays nothing under $1 for a market and a day |
| `min_lead` | 30 minutes | A game closer than this to the time its orders are pulled is not started |
| `max_filled_games` | 5 | With this many games holding a position, no new game is started |
| `expire`, `renew` | 180 s, 90 s | Each order lives three minutes and is sent again after ninety seconds |

Each side of a game is filled 100 contracts at most. What has been filled
is not offered again. The other side then works to close the position:
selling what was bought, or buying back what was sold.

## 3. What keeps it from doing harm

- **It cannot take a price.** Every order is sent with the exchange's
  "rest only" flag. If such an order would trade at once, the exchange
  rejects it. So it never pays the fee and never crosses a spread.
- **Its orders remove themselves.** Every order carries an expiry three
  minutes ahead, and never later than ten minutes before the game. If the
  program stops, loses its connection or is killed, its orders are gone
  within three minutes without anybody doing anything.
- **It does not rest blind.** If a game's book cannot be read in a cycle,
  that game's orders are cancelled in that cycle.
- **It stops when told.** An empty file named `STOP` in its state folder
  makes it cancel its orders and end. So does the end of a run, however the
  run ends.
- **An order request is never repeated.** If the answer to one is lost, a
  repeat could place the order twice. The next cycle reads the open orders
  again and works from what is really there.
- **It never cancels "everything".** The exchange's cancel-all takes a list
  of markets, and an empty list means the whole account. The code refuses
  to send an empty list.
- **Limits are in the code as well as the settings.** No order above 500
  contracts or outside 1¢ to 99¢ can leave, and an order of the wrong kind
  for its side is refused before anything is sent.

## 4. Running it on paper

```bash
kht us-quote --config config/us_quoter.json --state state/us-quoter --minutes 60
```

No account is needed. The orders are kept in memory and filled from the
real order books by the rule of `docs/09`, section 5: if contracts traded
at an order's price or through it since the last reading, the order is
taken to be first in line for all of them. Positions are closed at what
their game settled at, three hours after its start.

| File under the state folder | Contents |
|---|---|
| `actions.csv` | Every order placed, moved, cancelled and filled, and every stop with its reason. An order sent again unchanged, to push its expiry out, is not listed |
| `cycles.csv` | A line every ten cycles and whenever something is filled: games, orders, what is at risk, the account's value, the reward by the formula so far |
| `accrued.json` | Reward by the formula for each market and US date |
| `settled.csv` | Paper positions closed at settlement, with their result |
| `paper.json` | The paper positions, kept between runs |
| `STATUS.md` | A summary when a run ends |

**A rehearsal is running.** From its second run on 11 November, the
*us-rewards* job on GitHub also runs this program on paper, with the
settings in `config/us_quoter.json`, and commits `state/us-quoter/`. It is
the system as it would really be used: 20 games at a time instead of all
of them, with its limits on. `scripts/us_rewards_score.py` describes what
it did under the judged accounts. It is not one of them, because it
chooses its games, and a test must not.

## 5. Before any real order

This is the owner's decision. No order has been placed and none will be
without instruction. If it is taken, in this order:

1. **An account and a key.** A Polymarket US account with identity checks
   done, then a key from polymarket.us/developer. The exchange shows the
   secret once.
2. **The key goes in the environment of the machine that will run this, and
   nowhere else.** Not in this repository, not in a settings file, not in a
   chat.

   ```bash
   export POLYMARKET_US_KEY_ID=...
   ```

   ```bash
   export POLYMARKET_US_SECRET_KEY=...
   ```

   ```bash
   export KHT_ENABLE_LIVE=yes-trade-real-money
   ```

   ```bash
   pip install -e ".[live-us]"
   ```

3. **A preview run, which sends no order.** It signs in, reads the
   account's open orders and positions, and sends every order it would
   place to the exchange's own preview, which checks an order without
   placing it. This is the first time any of this code meets the exchange,
   and it is where a mistake in it should show.

   ```bash
   kht us-quote --preview --minutes 5
   ```

4. **One order of one contract, by hand,** in the exchange's app, in one
   of the games the preview chose, to see where it rests and what the
   account shows.
5. **A small real run:** `size` 25, `max_games` 5, `max_at_risk` 150,
   `max_day_loss` 30, for a day, watched.

   ```bash
   kht us-quote --live --minutes 360
   ```

6. **The comparison that matters.** Rewards are worked out within five
   business days and credited two days later. Then:

   ```bash
   kht us-earnings --since 2026-11-20
   ```

   sets what the exchange credited for each market and date beside what
   this program's own arithmetic said it should be. If the two agree, the
   formula is real and the paper results mean what they say. If the
   exchange credited far less, the idea is finished at the cost of a small
   test.

## 6. What it costs to run, in money

The exchange checks resting orders against an account's buying power one
market at a time. In its words, this "lets liquidity providers quote across
many markets without fully funding every resting quote simultaneously".
Orders of $50 in twenty games need $50 of buying power, not $1,000. A fill
uses real money, and the exchange then cancels by itself any resting order
elsewhere that is no longer covered.

So the money an account needs is set by what it could lose, not by how many
games it rests in. That is why this program limits itself by `max_at_risk`,
which counts every resting order as if it were filled, and not by the
account's balance.

## 7. What it does not do, and what has not been checked

- **It has never met the exchange.** The connection was written from the
  published API reference and the exchange's own Python SDK, and tested
  against a stand-in. Step 3 above exists because of this.
- **In live use it treats every open order in a game's market as its own**
  and will cancel it. It should have the account, or at least those
  markets, to itself.
- **What a real position can lose is taken as a dollar a contract.** The
  account's own figures for cost have not been checked against a real
  account, so the safe bound is used. This makes the limit bite sooner
  than it needs to.
- **The day-loss stop in live use reads the account's buying power plus
  the value of its positions.** That reading is unchecked too, and resting
  orders move it by a few tens of dollars.
- **It reads books every 30 seconds, by asking.** A professional system
  listens to a stream and reacts within a second. Between two readings a
  resting order can be left behind by the market. The paper test counts
  that unkindly; real life may be kinder or worse.
- **It follows no news and no scores.** It relies on leaving the book ten
  minutes before the recorded start, and on the recorded start being
  right, which it nearly always is (`docs/06_polymarket_us.md`,
  section 10).
- **It has no view on who will win.** It only rests where other people
  already rest real size, on both sides, and takes what the formula pays
  for being there.
