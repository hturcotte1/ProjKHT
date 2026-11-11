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

## 6. The two yardsticks, computed

`scripts/lasttick_reach.py`, from 3.6 million one-minute prices a coin
(3.3 million for Solana, listed in August 2020). Committed at 17:31 UTC,
before the history of any market was read
(`config/lasttick_reach.json`, `reports/research/ltr_*`).

How far a result must be from the index to count as out of reach:

| | 6 minutes | 10 minutes | 16 minutes | 22 minutes | Brake: a five-minute change of |
|---|---:|---:|---:|---:|---:|
| Bitcoin, L1-strict | 6.4% | 8.2% | 10.7% | 12.4% | |
| Bitcoin, L1-recent | 3.0% | 3.6% | 4.8% | 5.4% | 1.05% |
| Ether, L1-strict | 7.5% | 9.7% | 12.7% | 15.2% | |
| Ether, L1-recent | 4.1% | 5.1% | 6.5% | 8.5% | 1.41% |
| Solana, L1-strict | 10.6% | 14.5% | 18.0% | 19.9% | |
| Solana, L1-recent | 6.5% | 8.1% | 11.1% | 11.9% | 1.92% |
| XRP, L1-strict | 11.1% | 14.3% | 17.6% | 21.0% | |
| XRP, L1-recent | 6.3% | 8.6% | 11.4% | 13.9% | 2.07% |

The minutes are the time left, plus the age of the index value, plus one.

**L1-strict.** Every figure is set by 2020 or 2021. Its out-of-sample
check holds: the table made from 2020 to 2024 was exceeded in 2025 and
2026 at most once in 11,945 starts (XRP in 2025), against the one in 5,000
it allows.

**L1-recent passed the check fixed for it.** Applied with its brake to
every minute since 2020, the worst it did was Bitcoin in 2020 at 22
minutes: the price went beyond the reach once in 1,643 starts. The bar was
once in 1,000. For the other coins the worst year gave once in 3,200 to
3,700.

What the brake does, for Bitcoin at 16 minutes:

| Year | Minutes the brake stops | Beyond the reach without the brake | With it | Separate occasions that got through |
|---|---:|---:|---:|---:|
| 2020 | 3.7% | once in 650 starts | once in 2,014 | 24 |
| 2021 | 7.4% | once in 857 | once in 2,233 | 20 |
| 2022 | 3.4% | once in 2,872 | once in 4,929 | 13 |
| 2023 | 1.1% | once in 6,570 | once in 6,934 | 7 |
| 2024 | 1.3% | once in 4,972 | once in 12,100 | 5 |
| 2025 | 0.7% | once in 12,223 | once in 30,694 | 4 |
| 2026 | 0.7% | never | never | 0 |

Two things to read off it.

- **The brake does what it was added for, and not more.** It removes two
  thirds of the bad starts of 2020 and 2021. It cannot see a jump that
  comes out of a quiet hour, and a few of those happen every year.
- **What the loss costs.** A trade keeps about 0.9¢ and can lose 99¢. At
  once in 1,643, the worst year, the losses cost 0.06¢ a contract. At the
  rate of 2023 to 2025 they cost about 0.01¢. Against a premium of 0.9¢
  either is small. **This is the whole of the evidence that the trade is
  sound, and it is evidence about coin prices, not about this exchange.**

### The same yardsticks at the settlement itself

*Added at 18:31 UTC on 11 November, after the history of section 8 had been
read. It uses coin prices only. Nothing in the rule was changed by it.*

The figures above take every minute of the year as a moment to trade. The
test trades at one moment a day, the minutes before 5 pm New York time,
and that is not an average moment: large moves are about twice as common
in the American afternoon as over the whole day. So the yardsticks
were also run on that moment alone: the last 3 to 30 minutes before 5 pm
New York on each of the 2,506 evenings since 1 January 2020
(`reports/research/ltr_evenings.csv`, `ltr_evenings_near.csv`).

**L1-strict was never crossed,** for any coin, on any evening.

**L1-recent was crossed on five evenings, each time for one coin:**

| Evening | Coin | Minutes before 5 pm | Reach | Furthest the price went | Where it ended |
|---|---|---:|---:|---:|---:|
| 19 February 2020 | Bitcoin | 16 | 4.8% | 5.8% | 3.1% |
| 11 May 2022 | XRP | 6 | 6.3% | 9.3% | 8.2% |
| 10 October 2025 | XRP | 6 | 6.3% | 8.9% | 5.7% |
| 19 August 2026 | Ether | 10 | 5.1% | 5.3% | 4.2% |
| **8 November 2026** | Ether | 6 | 4.1% | 5.6% | 2.5% |

The last of them was three days before this was written, and inside the
five weeks of section 8. At 21:54 UTC, out of an hour in which neither had
moved by more than 0.2% in five minutes, Bitcoin fell by nearly 2% and
Ether by more than 3% in about three minutes. Over that last quarter of an
hour the index fell 2.0% for Bitcoin and 4.4% for Ether. The brake cannot
see that coming.

Two measures are shown because they answer for different markets. A "hit"
market pays if the price touches its level, so it is exposed to the
furthest the price went. A ladder pays on where the index is at 5 pm, so
it is exposed to where the price ended. By where it ended, L1-recent was
crossed on one evening in 2,506, for XRP in the crash of May 2022. By
the furthest it went, on the five above.

What this changes in how to read L1-recent:

- **Its bad evening is not a rarity of the 2020 kind.** Two of the five
  were in 2026. A level only just out of reach is not safe. It is a level
  the price has passed on the way about once in 1,250 to 2,500 evenings
  for a coin, and has ended beyond once in 2,506 evenings for one coin
  and never for the other three. The trade breaks even at once in 110.
- **The loss falls on the nearest levels.** The orders in section 4 run
  from just beyond the reach to several times it. On 8 November the
  history holds 20 Ether results that the rule called out of reach a
  quarter of an hour before, one of them with an order to trade against.
  All held, the nearest with a gap of 1.6 times the move.
- **Bitcoin carries nine tenths of the orders and was crossed once, in
  2020,** by the furthest the price went and not by where it ended.

What the tables leave to trade, with Bitcoin at $74,200 and the daily
ladder's top level at $81,500: by L1-strict, nothing a quarter of an hour
before the end, and in the last few minutes, if the index value is fresh,
levels above about $79,000. By L1-recent, levels above about $78,000 a
quarter of an hour before the end, and above about $76,500 two minutes
before it.

## 7. The up-or-down markets: a search, fixed at 17:37 UTC

*Fixed before any price of a settled up-or-down market was fetched. The
only price paths seen so far are those of a few Bitcoin markets on
11 November (section 3), and that day is left out.*

38,600 of these markets have settled. This is the same kind of search as
the one run on sports (`docs/06_polymarket_us.md`, section 9): thousands of
rules of one form, and a judge that asks whether any beats the luckiest of
that many worthless rules. Two things lower what to expect. The fee at
even odds is 2.4¢ a contract. And these markets are priced by programs
that read the index every second, where this project sees the book twice a
minute.

**Markets.** Every 5-minute, 15-minute and 1-hour up-or-down market of
the four coins whose window ended by 10 November 2026, 23:59 UTC, and that
settled at 0 or 1. The 122 daily ones are too few and are left out.

**Quotes.** The stored minute prices, each read as the book at the end of
its minute (section 3). A quote counts only if both sides have an asking
price between 1¢ and 99¢ and the two are 1¢ to 10¢ apart.

**A rule:**

> In markets of length L, for coins C, with M minutes left, if the asking
> price of side S is in band B, the spread is at most W and condition K
> holds, buy S at that asking price. Pay the fee. Hold to settlement.

| Part | Values |
|---|---|
| L and M | 5 minutes: 4, 3, 2 or 1 minutes left. 15 minutes: 12, 8, 5, 3, 2, 1. One hour: 45, 30, 15, 10, 5, 3, 2, 1 |
| C | all four coins; Bitcoin; the other three |
| S | "Up"; "Down" |
| B | the twenty price bands of the earlier searches, from 2–5¢ to 98–99.5¢ |
| W | 1¢; 3¢; any real book |
| K | none; the previous window of the same coin and length ended the same way as S; it ended the other way; S has been the dearer side at every stored minute of this window so far; it has not |

That is 32,400 rules. One purchase a market for each rule, of one
contract, since the history has no sizes.

**The judge** is that of `docs/06`, section 4, as corrected there.

- Discovery: windows ending before 3 November 2026. Validation: 3 to
  10 November.
- A rule is a candidate if in discovery it has 150 purchases or more, a
  mean return after the fee of +0.5% or more, and z of 3.0 or more, with
  the variance floored at what fair prices would give and every hour of
  every day counted as one bet.
- A candidate survives if its validation z, on 100 purchases or more, is
  above what the best of the candidates reaches in 95% of 500 worlds where
  every price is right. In those worlds the four coins' results in one
  window are drawn together.
- The whole funnel is also run in 20 such worlds, to count what gets
  through from nothing.

**Whatever happens** the counts will be reported, with a plain table of
asking price against how often that side won, by minutes left. A survivor
would not be a result until it had been seen in live books with sizes,
and a book seen twice a minute may not be able to show it.

### What it found: nothing

`scripts/crypto_updown.py` (`reports/research/crypto_updown_output.txt`,
`ud_*`), run at 18:59 UTC on 11 November.

| | Count |
|---|---:|
| Markets in scope, all with prices fetched | 37,388 |
| With a real book at one purchase time or more | 36,289 |
| Rules in the grid | 32,400 |
| Rules with 150 purchases or more before 3 November | 11,578 |
| Of those, rules that made anything after the fee | 2,460 |
| Best score among them (the bar is 3.0) | 2.62 |
| **Candidates** | **0** |
| Candidates in worlds where every price is right, 20 runs | 0.7 on average, 4 at most; none past the second step |

Not one rule passed the first step. A search this size turns up a
candidate or four by luck in some worlds where there is nothing to find.
Here it turned up none.

What a buyer got, in the 5-minute markets with one minute left, both
sides together:

| Asking price | Quotes | Average ask | Won | Return after the fee |
|---|---:|---:|---:|---:|
| 2–5¢ | 2,813 | 4.0¢ | 1.8% | −58% |
| 5–10¢ | 2,765 | 7.7¢ | 4.2% | −48% |
| 10–20¢ | 1,672 | 14.5¢ | 12.6% | −21% |
| 20–35¢ | 1,296 | 27.5¢ | 27.5% | −6% |
| 35–50¢ | 921 | 42.8¢ | 38.5% | −15% |
| 50–65¢ | 832 | 58.2¢ | 58.4% | −3% |
| 65–80¢ | 1,196 | 73.5¢ | 70.1% | −7% |
| 80–90¢ | 1,262 | 86.0¢ | 84.0% | −4% |
| 90–95¢ | 1,171 | 93.4¢ | 91.5% | −3% |
| 95–98¢ | 2,504 | 97.3¢ | 95.9% | −1.7% |
| 98–99.5¢ | 3,814 | 99.0¢ | 98.8% | −0.3% |

The buyer loses in every row. The long shots lose most: a side offered at
4¢ with a minute to go wins less than half as often as its price says.
That is the same lean as everywhere else in this project, and here too it
belongs to whoever is selling the long shot with a resting order and no
fee, in a market that reprices every second. The full table, for every
length and minute, is in `ud_calibration.csv`. A few of its 198 rows are
above zero, most of them favourites at 80¢ and more in the one-hour
markets, by 1% to 2% on a few hundred quotes each. None comes near the
bar, and in a table that size some rows are above zero by luck.

That the rows lose is also a check on section 3. Had a stored price
belonged to the start of its minute and not its end, "one minute left"
would have been the finished result, and every row would have won.

## 8. L1 on the history of the settled markets

`scripts/lasttick_history.py` (`reports/research/lasttick_history_output.txt`,
`lth_*`). Run at 18:14 UTC on 11 November, after the tables of section 6
were committed. 11,885 settled markets: every daily and weekly ladder,
"hit" market and hourly or daily up-or-down market that ended by
10 November. Each is read once, a quarter of an hour before its end. The
index then is known for 3,031 of the 3,070 settlement times.

**No result that the rule called out of reach came in. Under L1-recent
that is 4,208 results at 37 settlement times; under L1-strict, 1,690.**

| | L1-recent | L1-strict |
|---|---:|---:|
| Results out of reach a quarter of an hour before the end | 4,208 | 1,690 |
| Of those, results that changed | 0 | 0 |
| With an order stored to trade against | 734 | 257 |
| Trades that lost | 0 | 0 |
| Settlement times with a trade | 36 | 17 |
| The traded market had never traded a contract | 494 of 734 | 190 of 257 |

What the 734 were: 299 sales at 1¢ and 327 purchases at 99¢, and 108 at
2¢ to 5¢ or 95¢ to 98¢. 281 in Bitcoin, 252 in Ether, 146 in Solana, 55 in
XRP. A contract kept 1.2¢ on average after the fee.

Four things this adds to what was known.

- **The orders stay.** Of the 734, 98% showed the same price two minutes
  before the end.
- **Nobody takes them.** Two thirds of those markets never traded a
  contract in their whole life, and all but 45 traded under 100. Six
  traded 1,000 or more.
- **They are there most days, in small number.** 30 of the 32 daily
  settlement times had at least one, with 5 or 6 levels in a typical one
  and 11 on average. The weekly settlements on Fridays had 30 to 136. This
  is a count a quarter of an hour ahead. Nearer the end the reach is
  shorter and more levels qualify, which only the live recorder can count.
- **The brake was used once.** On 29 October it stopped Bitcoin and
  Ether, 86 markets. Their results held too.

And four reasons it is not more than it is.

- **It has no sizes.** A stored price says an order was there, not for how
  many contracts.
- **Some of these prices were never in a book.** In 41 markets the stored
  bid was far above what an out-of-reach result is worth, and the rule
  refused them. In 39 of the 41 that "bid" was the market's last trade,
  filled in where the book was empty (`docs/06_polymarket_us.md`,
  section 7). The same filling-in at 2¢ to 5¢ would pass as a real bid, so
  some of the 108 trades away from the last tick may not have been there.
- **Five weeks is one kind of weather.** Bitcoin fell by a seventh in
  these weeks, from $85,800 to $73,800, and no last quarter of an hour
  crossed the reach. That says the period had no day like 12 March 2020.
  It does not say what such a day would do. Section 6 is what speaks to
  that.
- **Zero losses is what this trade shows right up to the day it does
  not.** It is recorded here as a condition met, as section 5 said it
  would be.

## 9. Notes while the test runs

**11 November, 18:15 UTC.** The recorder `kht us-lasttick` was added to the
*us-rewards* job at 17:08 UTC and will run from that job's next run, due
about 19:50 UTC, so the first daily settlement it sees is tonight's at
22:00 UTC. A two-hour trial of it in this session followed the hourly
up-or-down markets through 18:00 UTC and the scoring script ran on what
it wrote. One look was taken at the hourly ladders five minutes before
18:00, since the recorder leaves them out: 536 books. They hold no orders
of the kind L1 trades. On levels sure to win there are bids at 99¢, and on
levels sure to lose there are offers at 1¢: resting orders that gain when
somebody trades against them. The daily ladders are the other way round,
which is what section 4 found.

**An illustration, not a reading of the test.** The books of section 4,
as they stood at 16:50 UTC, judged as if they had been read later with the
index where it was then:

| As if read | L1-recent: markets, contracts, premium | L1-strict |
|---|---|---|
| 15 minutes before the end, index 5 minutes old | 44 markets, 28,794 contracts, $263 | none |
| 2 minutes before the end, index 3 minutes old | 79 markets, 48,437 contracts, $443 | 40 markets, 19,805 contracts, $182 |

Nine tenths of it is Bitcoin. An account with $10,000 would be full either
way, at about $91. The evening's own books will differ.

**11 November, 23:02 UTC. The first evening was not recorded.** The job
on GitHub that carries the recorder lost its machine at 21:40 UTC, twenty
minutes before the daily settlement. A run saved what it had recorded only
at its end, so everything since 19:47 went with the machine. A second copy
of the recorder had been left running in this session as a backup, and it
stopped at about 19:00, when the session went idle. Nothing with sizes
exists for tonight's settlement. The test has not started. Six evenings
are left before 18 November, 12 to 17 November, and the bar asks for five.

What was changed the same evening, between 22:28 and 22:35 UTC:

- The job now saves what it has recorded once an hour, and once more a
  few minutes after 22:00 UTC (`scripts/ci_save_state.sh`). A lost machine
  now costs an hour at most.
- The recorder writes to disk as soon as the markets it follows have
  ended. Before, it wrote every ten minutes.
- A second small job, `us-rewards-watchdog`, is set to look every
  quarter of an hour and starts the recording job if no run of it is
  going. By 23:19 UTC GitHub had not yet started it on its schedule once,
  only when I started it by hand. GitHub starts scheduled jobs less often
  than they ask, so this is a net with wide meshes.
- The job was started again by hand.
- Added at 23:21 UTC: if a run ends badly after more than ten minutes,
  a second job in the same workflow starts the next run at once from a
  fresh machine. This does not wait for GitHub's schedule. It has not
  been seen to work yet: that takes a lost machine.

One mistake of mine on the way: the first version of the changed job file
did not parse, and for about a minute GitHub would not start the job. The
rule of the test and what the recorder writes down are as they were.

**What the stored quotes say about tonight.** These are prices without
sizes, one reading 15 minutes before the end: one more evening of the
history of section 8, not a live reading. 276 markets settled at 22:00
UTC. The Bitcoin index was $74,411.93 at 21:45 and the markets settled on
$74,309.75. By L1-recent 136 results were out of reach, none of them
changed, and 55 had an order to trade against. All 55 held and all were
still there two minutes before the end. By L1-strict: 22 out of reach,
none changed, 6 with an order.

**Somebody sold the Bitcoin ladder tonight, and that is new.** Section 4
says of these 1¢ bids that nobody takes them. On earlier days that is what
the figures show: of the Bitcoin brackets out of reach, 34 of 36 had
traded nothing all day on 10 November, and 36 of 38 on 9 November. Tonight
59 of the 64 daily Bitcoin brackets traded 169.49 contracts or more. On 15
of them 169.49 contracts is the whole day's trading. The exchange's own
figures for those 15 show a single sale at 1¢ on 13, and on the other two
a sale of 169.49 that took half a contract at 2¢ on its way to 1¢. The
stored quotes of those two put it between 17:04 and 17:05 UTC, a minute
after the far brackets were first quoted. 59 lots of 169.49 are 10,000
contracts. Somebody sold 10,000 contracts in equal lots across the ladder
in one go.

That the brackets near the price were part of it is an inference. They
trade all day, so one lot cannot be picked out there. But every one of
them traded at least 169.49 more after 16:50, and equal lots come to a
round 10,000 only if those brackets are counted in.

Who it was cannot be told from public data. It can hardly have been
somebody who had read this repository, which is public: this document was
first pushed at 17:02 UTC, two minutes earlier. What the lots say is
which trade it was, and it is not L1. It is taken up in section 12.

For L1 it means two things. The bids were still there afterwards, since a
sale of 169 leaves most of a bid for 1,000. And from 21:00 UTC the stored
quotes show no two-sided book on the 18 furthest Bitcoin brackets, which
is part of why only 55 of the 136 results out of reach had an order in
the last quarter of an hour. Whether that hour is always like this is
something L1's recorder cannot say: it reads the last 17 minutes.

## 10. The same bids elsewhere on the exchange

The recorder of `state/us/` reads the books of every reward market outside
sports and crypto. At 15:18 UTC on 11 November, 486 of those 2,737 books
had a best bid of 1¢ for 100 contracts or more. Most are long-dated
political long shots, where selling ties money up for months. Some are
ladders that settle soon. The daily ladder on the national average price
of petrol is one: fifteen levels with 1¢ bids of about 900 contracts each,
settled on a figure that is published hours before the market closes.
Nothing has been tested there. It would need the published figure from
outside the exchange, where the crypto index comes from the exchange
itself.

One look at that ladder says the trade is already taken there. On
11 November its seventeen levels were decided by 06:30 UTC, eight and a
half hours before the market closed, and the stored quotes did not change
again. On the levels that had lost, the two stored prices sit together
with no spread, which is what the history shows when one side of the book
is empty. And the two furthest levels had traded 3,266 and 4,046
contracts, where a far level of the crypto ladder has usually traded
none. Somebody sells to those bids. In crypto, so far, almost nobody
does.

## 11. If it holds: what a real version would need

Nothing here is built, and nothing will be sent without the owner's
instruction. It is written down so that the decision, if it comes, is a
small one.

1. **One contract by hand.** In the exchange's app, a few minutes before
   5 pm New York time, on a Bitcoin level far above the price: buy one
   "No" at 99¢, which is the same thing as selling one "Yes" at 1¢. It
   risks 99¢. It answers in one evening what no paper test can: whether
   the order fills, what the account shows, and when the 99¢ comes back.
2. **A key, kept as in `docs/10_us_quoter.md`, section 5:** in the
   environment of the machine that runs the program and nowhere else.
3. **A program that does only this.** The recorder's loop, the rule of
   `src/kht/trading/lasttick_rule.py`, and one kind of order: a limit
   order at the bid's own price that is filled at once or cancelled, never
   an order "at the market". The exchange's API has such an order, and
   the signing and the limits of the existing order system
   (`src/kht/trading/us_live.py`) would be reused. Limits of its own: a
   fixed sum that may be locked at one settlement time, a cap a level,
   Bitcoin only to begin with, and a full stop for the day at the first
   loss, since a loss means the rule or its facts were wrong.
4. **Small first.** $500 locked for a week of evenings keeps about $4.50
   an evening if every order fills. That is not the point of it. The point
   is to learn whether the bids are still there the evening after somebody
   has sold to them.
5. **Further out than the test asks.** The test sells at anything beyond
   the reach, because that is the rule that was fixed. A real version need
   not. On the five evenings of section 6 the price went at most 1.48
   times as far as the reach. In the history, 57% of the trades were on
   results more than 1.5 times the reach away (36% on the daily ladders),
   and 34% more than twice. Staying beyond 1.5 or 2 times the reach gives
   up half or two thirds of the trades and would have kept clear of every
   one of those evenings. That figure was read off after the fact, so it
   is a reason to keep a wide margin and not a tested rule.

## 12. L2: the whole ladder at once, fixed at 23:02 UTC on 11 November

### What tonight's sale points at

A ladder of brackets is a set of results of which exactly one happens.
Tonight's daily Bitcoin ladder had 64: below $66,000, 62 brackets of
$250, and $81,500 or above. Whoever has sold one "Yes" contract in every
bracket pays out exactly $1, whatever the price does. So if the bids of
all the brackets add up to more than $1 and the fees, selling the lot
keeps the difference with no view on the price at all.

Usually they cannot add up to more than $1: that is what a price is. Here
they can, because of section 4. Fifty brackets far from the price still
carry a 1¢ bid each, put there to collect the reward. That is 50¢ on top
of the bids near the price.

The check that a ladder is what it looks like was run on every settled one
(settlements only, no prices): 2,814 ladders, 101 of them daily, 17 weekly
and 2,696 hourly. Every one has both open ends, and in every one exactly
one bracket paid.

L1 sells the far brackets alone and needs a yardstick to say which are
far enough. This needs none. It pays for that by also selling the brackets
near the price at their bids, which are below what those brackets are
worth.

### What was looked at before the rule was fixed

Tonight's ladder only, 11 November.

- **The stored quotes, best bids without sizes.** From 17:30 to 20:30 UTC
  the best bids of the Bitcoin brackets added up to $1.42 to $1.46, with
  50 to 58 of them at 1¢. After fees and the $1, that would leave about
  30¢ to 34¢ for every contract sold in each bracket.
- **The real books at 16:50 UTC, with sizes.** They say the stored figure
  is too kind. Near the price the best bid is often for a fraction of a
  contract, and the bids of real size sit one to five cents lower. At
  16:50 only 26 brackets had a 1¢ bid, and selling ten contracts of every
  bracket would have lost 84¢. The other far brackets were first quoted at
  17:03.
- **Tonight's seller.** With the 16:50 books for the ten brackets near the
  price and 1¢ for the other 49, the sale of 169.49 a bracket brought in
  about $200, cost about $18 in fees, and had $169.49 to pay: about $13
  kept, on about $9,800 locked for five hours. The 59 lots add up to
  $10,000 of contracts, which is what an account of $10,000 can sell if
  every contract sold locks its own dollar.

So it is real, it is small, and it turns on sizes that only a recording
of the books can give. No other evening has been looked at.

### The recorder

The same program as L1's, run a second time beside it with other
settings, so that L1's recording is not touched:
`kht us-lasttick --state state/us-ladder --kinds range --follow 19800 --sweep 120 --budget 3`.
It reads the book of every daily and weekly bracket of the four coins,
three bid and three offer levels with sizes, about every two minutes, from
five and a half hours before the ladder ends. The hourly ladders are left
out, as in L1: their books are nearly empty. It was added to the job on
GitHub the same night and records from that job's next run.

### The rule

1. **A ladder** is the brackets of one coin with the same length and the
   same end, open ends included.
2. **A reading of a ladder** is taken every two minutes, counted back from
   its end: 2 minutes before it, 4 minutes, and so on to 330 minutes. At a
   reading, each bracket's book is the last one recorded for it, if that
   is at most four minutes old. A bracket with nothing that fresh has no
   bids at that reading.
3. **A sale of size Q** sells up to Q contracts of "Yes" in every bracket
   that has a bid: into its recorded bids from the best down, each level
   one fill, and no further than the three recorded levels go. No bracket
   is sold more than Q.
4. **What a sale locks** is the money received, less the fee on every
   fill, less Q. That much is kept whichever bracket pays. If the bracket
   that pays was sold less than Q, more is kept.
5. **The fee** on a fill is 0.095 × contracts × price × (1 − price),
   rounded to the cent, halves to the even cent, as the exchange
   publishes it.
6. **The money** is $10,000 for each settlement time, shared by the
   ladders that end then: first come, first served, and at the same
   reading in the order Bitcoin, Ether, Solana, XRP, daily before weekly.
   A contract sold locks $1 less its price until the ladder settles.
   Nothing is assumed about the exchange asking less for a set of
   brackets of which only one can pay.
7. **The trade.** At the first reading of a ladder at which some size
   locks at least $25: sell, at the size that locks the most. From 30
   minutes before the end, $10 is enough. The sizes tried are those at
   which some bracket's recorded bids run out, and the largest the money
   allows, to a hundredth of a contract. Of two sizes that lock the same,
   the smaller. The reason for two thresholds: there is one sale a
   ladder, so an early sale for a little gives up a later one for more,
   and near the end there is nothing left to wait for.
8. **Once.** A ladder is sold once. At later readings a bracket that had
   no bid at the sale and has one now is sold then, up to the same Q, if
   money is left: that adds money and cannot add to what is paid. No
   bracket is ever sold twice. A paper account that sold again and again
   to the same resting bid would be counting money nobody offered.
9. **The result** of a ladder is the money received, less fees, less the
   number of contracts sold in the bracket that paid.

Beside the judged account the script describes the day: at every reading,
how many brackets had a bid, how many of those at 1¢, and what sizes of
10, 100 and the best size would have locked. That is described, not
judged.

### The bar

By 18 November, when L1 and R1 are also read: at least five evenings
recorded; a sale on at least four of them; at least $20 kept an evening on
average, an evening without a sale counting as nothing; and no ladder
with a loss. An evening counts as recorded if at least 120 of the 165
readings of the daily Bitcoin ladder found fresh books. By its
construction the rule cannot lose on a ladder in which exactly one
bracket pays, so a loss would mean the ladder or the recording is not
what it is taken for.

$20 an evening on $10,000 is a fifth of one percent a day. Below that it
is not worth a program and a key, whatever the certainty.

### What paper cannot show

- **The fills.** A real sale is sixty orders against a book that is shown
  up to 30 seconds late. Orders that find their bid gone are cancelled,
  and that is harmless on a far bracket. On the brackets near the price
  it is not: if those fail and the rest fill, what is left is 10,000
  contracts sold with nothing certain about them. A real version would
  sell the brackets near the price first and the rest only up to what
  those filled.
- **The margin.** If the exchange locks less for a set of brackets of
  which one can pay, the same money goes several times as far. Not known.
- **The other side.** The bids exist to collect a reward. Somebody who is
  sold 1¢ contracts every evening may bid for fewer, or stop.
- **Company.** One seller was there tonight, within a minute of the
  quotes appearing. There is room for a second only as long as the bids
  are bigger than the first one's lots.

### The same arithmetic elsewhere: one look, and a warning

One look, on 11 November at 23:23 UTC, at the books the general recorder
wrote down at 22:23 UTC (`state/us/`, every reward market outside sports
and crypto). No test and no rule.

Of 231 events with three or more markets, 89 have best bids that add up
to more than $1. Almost none of them is this trade, because in almost
none of them does exactly one market pay:

- Lists of nominees, where five or more are named.
- Levels such as "above $3.91", where each level includes the ones
  beyond it.
- Events that read like one winner and are not. TIME's Person of the Year
  has 26 candidates whose bids add up to $1.45, in real size. Its rules
  say that if several are named each of them pays, and that a person
  pictured on the cover of a group pays too. Selling all 26 there is a
  bet, not a certainty.

The two plain one-winner sets in the list, the Federal Reserve's decision
in December and the top artist of the year, have bids adding up to $1.01:
nothing after fees.

So the rule stays where exactly one result pays by arithmetic, the
brackets of a number, and where that was checked on every settled ladder.
Anywhere else the rules of the event have to be read first.

### Notes while the test runs

**11 November, 23:18 UTC.** The rule above was committed at 23:03 UTC
(`cb32873`), the code that applies it at 23:11 (`a3fcaa0`), and the job
file that starts the second recorder at 23:15 (`ead6050`). The run of the
job that was going then keeps its old file, so the second recorder starts
with the next run, at about 03:35 UTC on 12 November, well before that
day's ladders come into its five and a half hours at 16:30. It was tried
first for two and a half minutes in a scratch directory with a longer
lead, so that it had something to read: 126 daily brackets of 12 November,
three readings of each, no errors. The scoring script was run on
tonight's real books of 16:50 UTC laid out as a recording, and on made-up
recordings in its tests. No evening has been recorded yet.

