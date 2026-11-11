# 08 — Being paid to leave orders

*11 November 2026. This is a lead, not a result. Nothing here has been
tested with money, and one thing that decides its value cannot be learned
without an account. Section 10, added later the same day, says what the
sports programmes show about that one thing; the sports side of this is in
`docs/09_sports_rewards.md`.*

## 1. What was found

Polymarket US pays people for resting limit orders, whether they fill or
not. It calls this the Liquidity Incentive Program, it is open to every
account with no application, and its whole schedule is public: which
markets, how much, on what conditions
(`GET https://gateway.polymarket.us/v1/incentives`, no key;
`PolymarketUS.iter_incentives`).

It also explains two things the earlier sections could not. The hundreds of
thousands of contracts resting at 1¢ and 99¢ on decided weather markets
(docs/06, section 7) are not there to trade. They are there to be paid. So
are the 500-contract orders at 1¢ and at 99¢ that sit in most markets on the
exchange.

## 2. The rules, from the exchange's own documentation

- Every second, each resting order is scored:
  **discount factor ^ (ticks from the best price) × size**. With a discount
  factor of 0.30, an order one tick behind the best price scores 30% of what
  it would at the best price, two ticks behind 9%.
- A side of a book is paid only while it holds the **target size**, counted
  over everybody's orders from the best price outwards. Orders beyond the
  point where the target is reached score nothing.
- Some programmes also set a **maximum spread**. Then a second pays only if
  both sides reach the target, at prices no further apart than twice that
  spread. Otherwise nobody is paid for that second and its share is lost.
- A programme's **reward pool** is split in proportion to score. There is no
  cap on one person's share: "if you're the only one providing liquidity on
  a second that qualifies, you earn that second's full share of the pool".
- Makers pay no trading fee. Rewards are worked out within five business
  days of a period ending and credited two business days later. Under $1 is
  not paid. The exchange can change every number between periods.

## 3. How much money it is, and a correction

The schedule on 11 November lists 173 programmes over 49,389 markets.

| | Programmes | Sum of their pools |
|---|---:|---:|
| Sports, while a game is live | 55 | $32,836 a period |
| Sports, other periods | 41 | $3,369 |
| Crypto | 15 | $3,220 a day |
| **Everything else** (politics, culture, economics, technology, weather, finance) | **24** | **$1,667 a day**, plus $435 for two programmes paid per live period |

**A correction to something I reported while working.** My first reading
added the pool once for every market it appeared on and got $185,000 a day
outside sports. That is wrong by about a hundred times. The exchange's
rewards page says a pool is "shared across the program's markets — never
summed per market". The culture programme that looked like $34,000 a day is
$40 a day, across 857 markets.

## 4. What is not known

Two things, and they decide whether this is worth cents or dollars.

1. **Is a daily pool per programme or per event?** The page calls these
   periods "Daily (per event)" and defines a period as "the window in the
   event's lifecycle ... with its own reward pool". For a game that is
   plainly one pool per game. For the culture programme it could mean $40 a
   day in all, or $40 a day for each of its 65 events.
2. **How is a second's money divided between several markets that
   qualify?** The documentation describes one market. It says each side of
   a book is "normalized to 1.0" each second, which suggests that every
   qualifying side gets an equal slice however much is resting on it, but
   it does not say so for a programme of hundreds of markets.

Neither can be settled from outside. The exchange reports what each account
earned, by market and day, only to that account.

## 5. What the order books show

Every market with a pool of $10 or more was read with its full order book
(2,287 books, 11 November, about 06:50 UTC, which is the middle of the
night in the United States) and scored by the rules above
(`reward_state` in `src/kht/trading/us_recorder.py`).

**Of 4,574 sides of those books, 1,754 would have been paid that second.**

| Programme | Pool | Target size | Max spread | Markets | Events | Sides paid, of all | Events where nobody is paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| Presidential election 2028 | $500 | 20,000 | none | 177 | 9 | 333 of 354 | 0 |
| Company results (CoreWeave) | $250 | 2,000 | 4¢ | 13 | 3 | **0 of 26** | **3** |
| Dancing With The Stars (live) | $250 | 500 | none | 26 | 4 | 21 of 52 | 2 |
| Politics, high | $225 | 10,000 | none | 33 | 2 | 53 of 66 | 0 |
| Weather (live) | $185 | 7,500 | none | 78 | 13 | 19 of 156 | 9 |
| Politics, middle | $75 | 5,000 | none | 180 | 21 | 140 of 360 | 2 |
| Culture, high | $75 | 500 | none | 140 | 11 | 229 of 280 | 0 |
| Economics, high | $75 | 5,000 | none | 25 | 6 | 23 of 50 | 1 |
| Technology | $50 | 1,000 | none | 103 | 11 | 136 of 206 | 0 |
| Finance | $50 | 500 | none | 65 | 14 | 123 of 130 | 0 |
| Culture, low | $40 | 500 | 6¢ | 857 | 65 | 226 of 1,714 | 40 |
| Diesel prices | $15 | 500 | 6¢ | 107 | about 4 | **0 of 214** | **all** |
| Petrol prices by state | $15 | 500 | 6¢ | 98 | about 5 | **0 of 196** | **all** |

Three things stand out.

- **Some pools are being paid to nobody.** In three programmes not one book
  qualified. Two of them, diesel and state petrol prices, were created the
  day before. The third is on a company's results that are already out, so
  one side of every book has emptied.
- **Somebody is working the rules precisely.** In the low culture programme
  the books that do qualify hold orders like 437.8 contracts at 81¢ against
  416.9 at 93¢: exactly the 12¢ the maximum spread allows, in exactly the
  size that tops the side up to 500.
- **The 500s at 1¢ and 99¢ are a relic.** Where a programme has no maximum
  spread, one order of 500 at 1¢ makes its side reach the target for $5.
  The exchange has since added a maximum spread to its newer programmes,
  and there those orders earn nothing.

## 6. What it might pay a small account

Take one more market made to qualify: the target size resting on both
sides, as far apart as the rule allows. For a target of 500 that ties up
about $450, wherever the price is.

| Programme | If a pool is one for the whole programme | If it is one for each event |
|---|---:|---:|
| Diesel or state petrol prices (nobody else there) | $15 a day: 3.3% a day | the same or more |
| Culture, low | $0.35 a day: 0.08% a day | up to $40 a day: 9% a day |
| Culture, high (join an existing side) | $0.65 a day: 0.14% a day | about $19 a day: 4% a day |
| Technology (target 1,000, about $900) | $0.72 a day: 0.08% a day | about $6 a day: 0.7% a day |
| Politics, low (target 2,000, about $1,800) | $0.15 a day: 0.01% a day | about $7 a day: 0.4% a day |

These assume every qualifying side gets an equal slice, and that nobody else
arrives. The low column is between nothing and 30% a year on money that
mostly just sits there. The high column is far more than any trade found in
this project. Which column is real is the unknown of section 4.

Either way this part is small. Everything outside sports and crypto adds
up to between $1,700 a day and perhaps ten times that, to be shared by
everyone doing it. It suits an account of hundreds or a few thousand
dollars and nothing larger. (Sports is a different size: section 10.)

## 7. Why it fits what the earlier rounds found

A resting order pays no fee, which removes the cost that sank most of the
ideas tested on this exchange. And the earlier rounds say which orders to
rest: offers of "Yes" on long shots, which is the same position as buying
"No". If such an order is filled, the account holds the trade that passed
its tests on polymarket.com and leans the same way here. If it is not
filled, it is paid for waiting. Bids for long shots at a cent or two cost
almost nothing to rest.

## 8. What can go wrong

- **Being filled at the wrong moment.** A resting order is filled when
  somebody knows more: a nomination leaks, a number is published. Orders
  must be pulled before scheduled news, and that needs software watching
  them.
- **The rules change.** The maximum spread was added to stop exactly the
  cheap orders described above.
- **Others arrive.** A pool with one claimant today may have ten next week.
- **It may pay almost nothing,** if the low reading of section 4 is right.
- **Money is tied up,** and offers of "Yes" need collateral of one dollar
  less the price for every contract.

## 9. What happens next

1. **The recorder now tracks it.** Every cycle it reads the schedule and
   notes, for each book, whether each side would be paid and how much score
   there is to share (`state/us/rewards.csv`, and a table in
   `state/us/STATUS.md`). Within days that shows whether the unclaimed
   programmes stay unclaimed, how crowded the others are at different hours,
   and how fast a new programme fills. How others behave is the best
   outside evidence of what it pays: nobody leaves $15 a day lying about for
   long if it is real.
2. **Only a real account can settle it,** and that is the owner's decision,
   not mine. No order has been placed and none will be without
   instruction. The smallest useful test is one market in an unclaimed
   programme, the target size on each side, about $450, left for three
   days, and then the account's own earnings page read for what was
   credited. Its worst case is being filled on one side and holding a small
   position bought or sold six cents from the middle of the book.
3. If that test pays, the system to build is a quoting engine on the
   Polymarket US API: choose markets from the schedule, rest the target
   size, pull before news, and treat a fill as the "No" trade. Nothing of
   that kind exists in this repository yet.

## 10. Added later on 11 November: what sports says about the first unknown, and what it does not

Section 4 could not tell whether a daily pool was one for a whole programme
or one for each event in it. The sports programmes, which section 3 only
counted, settle it for sports and leave it open here.

**In sports a pool is one game's.** A sports programme's periods are
counted from each game's start (before the day, the six hours before the
start, during play), so there is no single period that a programme-wide
pool could belong to. The exchange's definitions say as much: a time period
is "a window during the event lifecycle ... with its own reward pool". The
table in section 3 adds each sports programme's pool once, which is
therefore far too low: for the games listed for one day, the pools come to
about $11,000 for the six hours before the start and $39,000 during play,
in the programmes on who wins alone. `docs/09_sports_rewards.md` takes
sports from there.

**Outside sports it is still not known, and what people do argues for the
small reading.** The daily programmes are labelled "Daily (per event)",
which reads like one pool for each event. But look at the events that have
a single market, where nothing has to be assumed about how an event's pool
is divided. On 11 November there were 30 of them with a book to rest in.
If each really had its programme's whole pool to itself, 100 contracts
resting on each side would be paid, by the formula:

| Market | Programme pool | Score on the bid, on the offer | 100 contracts a side would be paid, a day |
|---|---:|---:|---:|
| Will Congress impeach and remove Hegseth by March 2027 | $75 | 237, 151 | $26 |
| Hegseth out by 31 December | $75 | 111, 3,120 | $19 |
| Jensen Huang out as Nvidia's chief by 31 December | $50 | 299, 145 | $16 |
| Will Congress impeach Hegseth in 2026 | $75 | 872, 386 | $12 |

That is $26 a day on $99 of resting orders. The accounts collecting the
reward in those books are easy to see: exactly 5,000 contracts at 2¢ and
4,999.99 at 99¢ to reach the target of 5,000, and 150 to 250 contracts at
the real price to hold the score. If $75 a day were at stake in that one
market, whoever does this would rest far more than 250 contracts there, and
others would have joined, in the seven weeks some of these programmes have
run. Under the small reading, a pool shared by all of a programme's
markets, the same books pay between 10% and 90% a year on the money
resting, which is about what one would expect people to settle at.

So for these programmes the first unknown stands, and my guess is now the
small reading. It is cheap to settle with a real account: 100 contracts on
each side of one such market, about $100, for a few days, and the earnings
record will show either cents or tens of dollars. That is the owner's
decision.

**And the rules themselves change on 18 November.** The exchange's filing
of the programme's terms with its regulator, found later the same day,
does not settle this question either: it speaks of a reward "for a
Contract and Time Period" and of parameters set "for each set of
Contracts". What it does say is that from 18 November 2026 the exchange
may cap any reward at a percentage of what the account itself traded in
that market. That applies to these programmes as much as to sports, and
where it is used, orders that only rest earn nothing. It is set out in
`docs/09_sports_rewards.md`, section 9.

