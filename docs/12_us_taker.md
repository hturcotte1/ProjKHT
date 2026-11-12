# The program that would place the last-tick sales

*Written 12 November 2026. It is a tool and not a result. Whether the
trade it places is worth placing is test L1, which is still running
(`docs/11_crypto_us.md`, sections 5 and 9). No order has been placed by
it, by me or by anything else in this project, and no key was used.*

## 1. What it does

`kht us-take` follows the crypto markets of Polymarket US through their
last quarter of an hour. On each reading of an order book it asks the rule
of test L1 one question: is this a result the price can no longer reach,
with somebody still bidding for it? If so it sells "Yes" to that bid, at
the bid's own price, and holds to settlement. That is all it does.

The decision is not in this program. It is `lasttick_rule.decide`, the
function the paper test is scored with, called on the same kind of
reading. What this program adds is what an account needs around a rule:

- one order a market, ever;
- a fixed sum that may be tied up at one settlement time;
- whole contracts only;
- a record of every order and what became of it;
- a full stop at the first loss.

## 2. Its limits

In `config/us_taker.json`, as shipped:

| Setting | Shipped value | Meaning |
|---|---|---|
| `yardstick` | `recent` | Which definition of "out of reach": the second one of `docs/11`, with its brake, or `strict`, the first |
| `money` | 500 | Dollars that may be tied up at one settlement time. A contract sold at 1¢ ties up 99¢ |
| `cap` | 500 | Contracts in one market, at most |
| `coins` | Bitcoin | The coins it looks at |
| `sides` | `sell` | `sell`: sell "Yes" at 5¢ or less where it will pay nothing. `buy` (off): buy "Yes" at 95¢ or more where it will pay $1 |
| `stop_on_loss` | on | See section 3 |

In the code, whatever the file says: never more than $10,000 at one
settlement time, never more than 2,000 contracts a market, never a sale
above 5¢ or a purchase below 95¢.

With the shipped settings the most it can lose on one evening is about
$500, if every level it sold came in. The most it can make on one evening
is about $4.50. Those two numbers are the trade. What makes it worth
considering is how seldom the first happens, and `docs/11`, section 6, is
the whole of what is known about that.

## 3. What keeps it from doing harm

- **It takes and never rests.** Every order is a limit order at the price
  it was decided on, filled at once or cancelled. It is never an order
  "at the market", and nothing of it stays in the book.
- **One order a market.** The market is written down as used before the
  order goes out. If the program dies in between, it will not send a
  second order after it is started again.
- **An order is sent once.** If the answer is lost, the order may or may
  not have gone through. The program does not try again. It writes "not
  known, look at the account" and leaves that market alone.
- **A loss stops it.** When a market it sold comes in after all, it
  writes a file `STOP` beside its records and sends nothing more until a
  person removes the file. A loss here is not bad luck to trade through.
  It means the rule or one of its facts was wrong.
- **It never buys back, never cancels, and never touches another
  market.** The only order it knows is the one described above.
- **Live trading is hard to switch on.** The same three conditions as the
  other order program (`docs/10_us_quoter.md`): a switch in the
  environment, the key in the environment and nowhere else, and one extra
  package.

## 4. Running it without an account

On paper, against live books. An order is "filled" against the very book
it was decided on, and nothing is sent anywhere:

```bash
kht us-take --minutes 60
```

As a replay, over an evening the recorder wrote down. This needs no
network at all unless `--settle` is given, and it writes to a temporary
directory so that it cannot mix with anything else:

```bash
kht us-take --replay state/us-lasttick --settle
```

The replay is the useful one. On the same recording it makes the trades
the paper test's small account makes, and a test holds the two to that
(`tests/test_us_taker.py`). So when the paper test has an evening, this
program has been run on that evening too.

It writes `actions.csv` (every order: wanted, filled, fee, how far out of
reach), `settled.csv`, `positions.json` and a `STATUS.md` in words.

## 5. Before any real order

This is the owner's decision. If it is taken, in this order:

1. **The paper test first.** L1 is read on 18 November. If it has not
   passed, stop here.
2. **One contract by hand,** as `docs/11`, section 11, describes. It
   answers what no program can: whether such an order fills at all, what
   the account shows, and when the 99¢ comes back.
3. **A key, in the environment of the machine that will run this and
   nowhere else,** exactly as in `docs/10_us_quoter.md`, section 5, steps
   1 and 2.
4. **A preview run, which sends no order.** It reads live books, decides
   as it would for real, and sends each order to the exchange's own
   preview, which checks an order without placing it. This is the first
   time this code meets the exchange, and it is where a mistake in it
   should show.

   ```bash
   kht us-take --preview --minutes 30
   ```

   Start it about 25 minutes before 5 pm New York time, when the daily
   markets are in their last quarter of an hour.
5. **A small real run, watched:** the shipped settings, or smaller. One
   evening.

   ```bash
   kht us-take --live --minutes 30
   ```

6. **Then look at the account** beside `actions.csv`: did each order fill
   for what the program says, at the price it says, and did the money
   come back after settlement?

## 6. What has not been checked

- **The live part has never met the exchange.** It was written from the
  published API reference, read on 12 November 2026, and tested against a
  stand-in. Three things in it are read off the documentation and could
  be wrong: that a sale of "Yes" is sent as a purchase of "No" with the
  price of "Yes"; that an order sent with "wait for the result" comes
  back with its fills; and the names of the fields the fills come back
  in. The preview run and the first real order are what check them.
- **Whether such an order fills.** The public book is shown up to 30
  seconds late. On paper the bid is always still there.
- **What the other side does.** `docs/11`, section 9: on 11 November
  somebody else began selling to these bids.
- **It does not do test L2,** the sale of a whole ladder at once. That
  needs every leg to fill, and what to do when some do not is not a small
  question. It is not built.
