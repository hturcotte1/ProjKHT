# 11 — Crypto on Polymarket US, and a test of the last tick

*11 November 2026. Sections 1 to 4 are what was looked at on this day.
Section 5 fixes a test, L1, before the history of these markets is read
and before any of its live data exist. Nothing here has been tested with
money. No order has been placed.*

## 1. Why this round exists

Crypto was the one part of Polymarket US that the earlier rounds left
out: `scripts/download_us.py` skipped it. It is the newest part of the
exchange and the fastest. Its markets settle on an index price, so there is
nothing to forecast about a person or a game, only about how far a price
can move in the time left.

## 2. What is there

Counted from the exchange's public list at 16:41 UTC: 488,254 crypto
markets that have closed, 485,805 of them settled.

| Kind | What it asks | Coins | Closed so far | First settled |
|---|---|---|---:|---|
| Hourly ladders | above a level, or inside a bracket, at the top of the hour | BTC, ETH, SOL, XRP | 440,057 | 5 October (BTC), 15 October |
| Daily ladders | the same at 5 pm New York time | all four | 6,359 | 5 October (BTC), 15 October |
| Weekly ladders | the same on Friday at 5 pm | all four | 2,039 | 9 October |
| "Hit" markets | touches a level before the week or month ends | all four | 303 | 8 October |
| Up or down, 5 minutes | index at the end at or above the start | all four | 23,502 | 22 October |
| Up or down, 15 minutes | the same | all four | 12,634 | 22 September (BTC), 15 October |
| Up or down, 1 hour | the same | all four | 3,229 | 22 September (BTC), 15 October |
| Up or down, 1 day | the same | all four | 122 | 5 October (BTC), 15 October |

Every market settles on a CF Benchmarks real-time index (BRTI for
Bitcoin). The value used is the average of the sixty one-second index
prices in the minute before the moment in question. Tick 1¢. Taker fee
0.095 × price × (1 − price) a contract for a small account, rounded to the
cent on an order; resting orders pay nothing. A contract sold short locks
$1 less the price received until settlement.

Where the trading is, from 544 books read at about 15:55 UTC:

- **The 5-minute Bitcoin market is the busiest thing on the exchange.**
  145,714 contracts in one five-minute market, a 1¢ spread. Fifteen
  minutes: 62,983. One hour: 25,504. The other coins trade a hundredth of
  that.
- **The hourly ladders are nearly empty.** Only 6% to 15% of their books
  had orders on both sides, and the typical level had never traded.

## 3. Three things measured about the data

**The public order book is a picture taken every 30 seconds.** Two Bitcoin
books were read once a second for seven minutes. The book that came back
changed every 30 seconds and not between. When it changed it was under a
second old. So a reader without an account sees each market at most twice a
minute. For a tennis match six hours ahead this does not matter. For a
five-minute market it decides what can be tested: nothing that needs to act
between two pictures.

**A stored minute price is the price at the end of that minute.** The
exchange's price history gives one point a minute. Twenty-four fast markets
were followed for fourteen minutes and their stored points compared with
the books seen. A point labelled 16:31:00 fits the book at 16:32:00 (the
two differ by 11¢ on average, both sides added), not the book at 16:31:00
(34¢). Every earlier use of this history
was in markets that do not move in a minute, and none is changed by this.
In a five-minute market it is the difference between a price with a minute
to go and a price when the result is known.

**The reward pools on the ladders are worked by somebody who posts exactly
the size the programme asks for.** The daily Bitcoin ladder has a pool of
$500 a day over 63 levels, with a target size of 1,500 contracts and a
maximum spread of 5¢. On a level far above the price the book was: a bid of
1¢ for 1,500 contracts, an offer of 100 at 2¢ and 5,000 at 3¢. On a level
far below: bids of 105 at 98¢ and 5,250 at 97¢, and no offer. The same
sizes repeat down the ladder. A 100-contract order beside these would hold
about a twentieth of a side. Nothing here is richer for a small account
than the tennis lead of `docs/09_sports_rewards.md`, and the price moves
all day, which tennis before a match does not.

## 4. What nobody takes

To be paid, a market needs orders on both sides within the maximum spread.
On a level the price cannot reach, the only bid that can be posted is the
lowest one: 1¢. So whoever works these pools bids 1¢, for the target size,
on levels that are all but certain to pay nothing.

Anybody may sell to that bid. Selling a contract at 1¢ that then pays
nothing keeps the 1¢, less a fee of about a tenth of a cent. It locks 99¢
until the market settles.

Two things were looked at before this section was written. They are the
whole of what is known, and they are not a test.

- **Yesterday's daily Bitcoin ladder (10 November).** The index finished
  between $73,750 and $74,000. On eight of the ten levels from $76,250 to
  $78,500 the stored quotes show a 1¢ bid through the last stored minute
  before the end. Of the 23 levels from $77,250 up, 19 traded no contract
  all day.
- **Today's books at 16:50 UTC,** five hours before the end. 58 daily
  markets across the four coins had a best bid of 1¢, for 69,276 contracts.
  In the daily Bitcoin ladder, 11 of the 18 such levels had never traded.
  The books of five levels were compared with the stored history at the
  same moment, and a real 1¢ bid shows there as "Yes 2¢, No 99¢". A level
  with no bid and no trade has no stored history at all.

Sold in the last minutes, 69,276 contracts would bring about $628 after
the fee, for $68,600 locked until settlement. **Why nobody does it is not
known.** It may be too small for a firm. The market is five weeks old. Or
there may be an obstacle that only an account would show. The last of
these cannot be settled on paper.

The hourly ladders do not have these bids: two of 300 Bitcoin levels had
one, an hour before the end. The long-dated markets have them in enormous size
(1.5 million contracts bid at 1¢ on Bitcoin reaching $150,000 by the end of
December) and there they are a different thing. Selling locks 99¢ for
seven weeks to make 0.9¢. That is the return of a savings account, and
people do take it.

## 5. L1: the test, fixed before the history is read

**This is the trade that fooled two earlier rounds.** A rule that buys at
99¢ and has not lost yet looks perfect and proves nothing
(`docs/04_second_round.md`, test A1). And in the price history of this
exchange, eighteen such rules turned out to be buying from nobody
(`docs/06_polymarket_us.md`, section 7). So this test is built differently
on both counts. It trades only against orders seen in a live book, with
their sizes. And it does not count "it has not lost" as evidence for
anything.

### The trade

In the last minutes before a crypto market settles, on a result the price
can no longer reach in the time left: sell "Yes" to the best bid where
"Yes" will pay nothing, or buy "Yes" at the best offer where it will pay $1.
Hold to settlement.

### Out of reach

1. **Where the price is.** The exchange publishes the index itself: every
   five-minute up-or-down market carries the index value at its start as
   its "price to beat". The level used is the newest of these for the
   coin. It is never more than a few minutes old, and its age is counted
   below. If it is older than 10 minutes, nothing is traded.
2. **How far the result is.** For "above a level": the gap between the
   level and the index, as a share of the index. For a bracket: the gap to
   its nearest edge. For a "hit" market that has not been hit: the gap to
   the level. For up or down: the gap between the index and the market's
   own price to beat.
3. **How far the price can go.** From one-minute prices of each coin since
   1 January 2020 (Binance's public data, against USDT), for a horizon of
   h minutes: take every minute as a start, and measure the largest move
   either way within the next h minutes, using each minute's high and low.
   For each calendar year take the move that only one start in 5,000
   exceeded. The **reach** for that coin and horizon is the largest of
   those yearly figures, and never less than 1%. The table is computed by
   `scripts/lasttick_reach.py` and committed before the history of the
   markets is read.
4. **Out of reach** means the gap is larger than the reach for a horizon
   of: the minutes left, plus the age of the index value in minutes,
   plus one.

The reach is set from the worst year on purpose. 2020 and 2021 moved far
more than 2026 does, and the next bad year is not announced.

### The rule

- **Markets:** every crypto market on Polymarket US of the kinds in
  section 2, except the 5- and 15-minute markets and the hourly ladders.
  The hourly ladders have almost no orders of this kind. The 5- and
  15-minute markets carry no reward programme, so nobody is paid to post
  them. And there are thousands of both a day.
- **When:** at a reading of the book taken between 15 and 2 minutes before
  the market's end.
- **What:** if the result is out of reach, trade against the best price on
  the losing side of the book: the best bid if "Yes" will pay nothing, the
  best offer if it will pay $1. Take the size shown there, up to 2,000
  contracts. One trade a market, at the first reading that qualifies.
- **Unless the book disagrees.** A sale is made only at 5¢ or less and a
  purchase only at 95¢ or more. A bid of 40¢ on a result this rule calls
  out of reach does not mean somebody is giving money away. It means the
  rule has a fact wrong: a stale index, a level misread. Such readings are
  counted and reported, and not traded. *(Added at 17:11 UTC on
  11 November, before the reach table existed and before any history or
  live reading was scored. The rule as first committed said "whatever
  that price is".)*
- **Cost:** the taker fee of 0.095 × price × (1 − price) a contract.
- **Result:** what the market settled at.

### Two accounts

- **L1-all** takes every trade the rule finds.
- **L1-10k** has $10,000 to lock at each settlement time and takes trades
  in the order they are found until it is used up. It is what a small
  account would see.

### A second yardstick, added at 17:21 UTC, before anything was scored

*What had been seen when this was added: the reach table for Bitcoin by
the definition above, from minute prices. No book, quote or result of any
market had been scored under any rule.*

By that definition the reach comes from 2020. The move within 16 minutes
that one start in 5,000 exceeded was 10.7% in 2020, 9.6% in 2021, 5.5% in
2022, and 4.3%, 4.8%, 3.8% and 3.2% in the four years since. So a quarter
of an hour before the end, a level has to be about 11% from the price to
count as out of reach. The daily Bitcoin ladder ends about 10% above the
price.
**The rule as written will trade almost nothing.** It stays in the test
exactly as written, under the name **L1-strict**, and will be reported
whatever it shows.

The table also shows what is blunt about that yardstick. The 2020 figure
is set by two days, 12 and 13 March. One number for every evening treats
each of them like those two. And on those two days nobody needed a table
to know: the price had been falling by whole percents every few minutes
for hours.

**L1-recent** is the same rule with a yardstick in two parts.

1. **The reach comes from 2023 to 2026 only,** computed the same way.
2. **A brake.** Take the index levels published in the hour before the
   reading, one every five minutes. If any two in a row differ by more
   than a set amount, nothing is traded in that coin at that reading. The
   amount is the five-minute change that one interval in 1,000 exceeded
   in 2023 to 2026. If fewer than six such changes are known, nothing is
   traded.

Its test is fixed here too. The yardstick, brake included, is applied to
every minute from 2020 to 2026 as if it were a reading, at horizons of 3,
6, 10, 16, 22 and 30 minutes. **In no year, at no horizon and for no coin
may the price have gone beyond the reach more often than one start in
1,000.** That would cost about a tenth of the premium. The years 2020 to
2022 took no part in setting the table and are the hard ones. If this
fails, L1-recent is not a yardstick and nothing scored under it counts.

So there are four accounts: L1-strict and L1-recent, each as "all" and as
"10k". The bar below is read for L1-recent, with this check in place of
the one written there for 2025 and 2026, and L1-strict is shown beside it.

### What will count as evidence, and what will not

The profit of this trade is a premium that can be read off the book, less a
loss that is rare and large. Three weeks of paper trading can measure the
first and cannot measure the second. So:

1. **The orders.** How many contracts stand at the last price on
   out-of-reach results at each settlement, in live books with sizes, and
   whether they are still there in the last 15 minutes. This is what the
   recorder is for.
2. **The loss, bounded from outside.** How often each coin has moved
   further than the reach, counted on six years of minute prices and shown
   year by year. And a check out of sample: the reach computed from 2020 to
   2024 only, set against the moves of 2025 and 2026.
3. **The history of the markets,** read once the table is committed. For
   every settled daily and weekly ladder, "hit" market and hourly or daily
   up-or-down market: the stored quote 15 minutes before the end, the index
   from the 15-minute up-or-down market that started at that moment, and
   the result. It says how often the orders were there and whether any
   out-of-reach result ever came in. It has no sizes, and about one stored
   price in fifty on this exchange was never in a book.
4. **The paper accounts,** for what they are: the premium collected, and
   any loss.

**L1 will be called worth a small real test if,** by 18 November: at least
five daily settlements have been recorded live; L1-10k collected at least
$50 a day on average; no out-of-reach result came in, live or in the
history; and the out-of-sample check holds, meaning 2025 and 2026 exceeded
the 2020–2024 reach no more often than one start in 5,000. A zero in the
loss column is a condition here. It is not the proof. The proof, such as it
is, is item 2.

### What paper cannot show

- **Whether the order would fill.** A bid seen in a picture of the book up
  to 30 seconds old is nearly always still there for a market that has not
  traded all day. Only a real order shows it.
- **Whether an account may do it.** Selling short at 1¢ is described in
  the exchange's documents as an ordinary sale. It has not been tried.
- **What the other side does next.** Each sale costs whoever posts these
  bids about $15 a level. One day of it may be enough for them to pull the
  bids before the end. Then this is over, at no cost.
- **The rules change on 18 November** (`docs/09_sports_rewards.md`,
  section 9). If rewards are capped by what an account trades, the bids may
  go, or may grow.
- **A loss, when it comes, takes several levels at once,** and all four
  coins tend to move together. One bad settlement would cost a few days of
  the premium, not one trade's worth.

## 6. The up-or-down markets

38,600 have settled. A search over rules that buy one side at its asking
price, like the one run on sports, is planned and is not registered here.
Two things lower what to expect from it. The fee at even odds is 2.4¢ a
contract, and these markets are priced by programs that read the index
every second, where this project sees the book twice a minute. It will be
fixed in writing before its prices are joined to its results.
