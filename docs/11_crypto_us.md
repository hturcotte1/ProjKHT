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
- 12 November, 00:42 UTC: the nearest thing to that was tried once. A
  small job on GitHub was made to fail on purpose with the same follow-up
  job behind it. The follow-up ran, read when its run had started, and
  took the "failed within ten minutes" branch, which starts nothing. So
  the condition and the reading work. The one step not exercised is the
  command that starts the next run, and that same command has ended
  every normal run of the job so far. The test job was removed again.
  By then the watchdog had still not been started by GitHub's schedule,
  two hours after it was added, so the restart inside the job is the
  protection that counts.

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

**12 November, 09:04 UTC.** Nothing to score yet, as expected: the first
daily settlement the recorder can see is tonight's. From 22:43 UTC on
11 November to 08:00 UTC it took 1,080 readings of 40 markets, the hourly
up-or-down markets of the four coins at ten hours. The rule called all of
them within reach and traded none, under both yardsticks. The job's log
says both recorders were running, with no errors. The order program was
replayed over the same readings and sent no order, which is what the
scoring script says it should.

**13 November, 09:09 UTC. The first evening recorded live, and the bids
are not there.** The settlement of 12 November at 22:00 UTC was followed
whole: 256 markets, 5,376 readings, from 21:43 to 22:01.

| | L1-recent | L1-strict |
|---|---:|---:|
| Results out of reach | 169 | 98 |
| Of them, with nobody to trade against | 133 | 96 |
| Trades | 36 | 2 |
| Of them, for a contract or more | 2 | 0 |
| Contracts | 930 | 0.2 |
| Premium after the fee, all of it and the $10,000 account alike | $8.42 | $0.00 |
| Lost | 0 | 0 |
| Refused because the book disagreed | 0 | 0 |

The bar asks the $10,000 account for $50 a day. It collected $8.42, and
none of it from the trade this test was built on. The two trades of any
size were purchases at 99¢ of levels sure to pay, in Ether and XRP. The
other 34 were sales and purchases of a tenth of a contract. Not one 1¢
bid of real size was left to sell to: of 798 readings that showed a best
bid of 1¢, ten were for 100 contracts or more.

The second recorder, which watches the brackets for five and a half
hours, shows why. From 16:30 to 21:00 UTC the daily Bitcoin ladder
carried 1¢ bids of about 1,000 contracts on 38 to 47 of its 58 brackets.
After 21:00 it carried 1¢ bids on 29 brackets, for three to eight
contracts in all. Two things took the big bids away. One of the two firms that post
them withdraws its bid from a bracket as soon as part of it has been
sold to. And between 21:00 and 21:02 somebody sold to the whole of the
other firm's bid, 1,005 contracts, on each of the 18 brackets from
$77,000 up, which were nearly 8% and more above the price: about 19,100
contracts. On 11 November those brackets had traded nothing but the 169
contracts of section 9's seller, so this is a second newcomer in two
days.

So section 4 was wrong where it said the bid is left until the end. The
history showed a 1¢ bid still standing in the last minutes, and it was
right about the price. The history has no sizes, and the bid that stays
is for a tenth of a contract. I wrote that the history could not show
sizes. I did not think the size would be that. L1 as written looks for
its trade in a quarter of an hour in which there is nothing left to
trade, and four more evenings will not change that. It runs to
18 November as fixed and will be reported as it comes out.

The order program was replayed over the same readings. It sent two
orders, the two trades of real size, for $8.38: the scoring script's
figure less the trades of under one contract, which the program does not
send.

**14 November, 09:08 UTC.** Two settlements are recorded. The second,
Friday 13 November, had no daily ladder: the weekly markets settled, 576
of them, followed whole from 21:43 to 22:02. L1-recent found eight
trades there, one of them for a whole contract, and collected two cents.
Over the two evenings the $10,000 account has $8.44, which is $4.22 a
day against a bar of $50. Nothing lost. L1-strict has nothing. The order
program, replayed, sent three orders for $8.39: the scoring script's
three trades of a contract or more.

*At each check-in while the test runs:* the order program of
`docs/12_us_taker.md` is run on paper over the recordings
(`kht us-take --replay state/us-lasttick --settle`, with a configuration
for all four coins and $10,000). It should make the sales the scoring
script's small account makes. If it does not, one of the two is wrong and
that comes before anything else.

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

A second look, at 09:03 UTC on 12 November, at that day's ladder says the
same more plainly. It was decided: 98¢ bid for "above $3.905" and 2¢ for
"above $3.91". Bids of 1¢ stood on two levels only, for about 900
contracts each. On the thirteen levels from $3.925 up there was no bid
left at all, only offers at 1¢, and the four highest had each traded
about 1,800 contracts. The 1¢ bids had been there and somebody had sold
to all of them. The exchange showed the markets as closed at that hour.

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
   *Since 12 November this program exists:* `kht us-take`, described in
   `docs/12_us_taker.md`. It runs on paper and over recorded evenings.
   Its connection to the exchange has never been run.
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

It describes one more thing, added at 00:30 UTC on 12 November, before
anything was recorded. Every sale is put once more to the books of the
next reading, two minutes on: each leg as an order for the size it sold,
at the lowest price it sold at. The script says how many legs would still
have filled whole and what the sale would have locked with only those
fills. If the legs near the price have shrunk and the far ones have not,
that figure is below zero. It is the paper's nearest answer to the first
thing listed under "What paper cannot show".

### The bar

By 18 November, when L1 and R1 are also read: at least five evenings
recorded; a sale on at least four of them; at least $20 kept an evening on
average, an evening without a sale counting as nothing; and no ladder
with a loss. An evening counts as recorded if at least 120 of the 165
readings of the daily Bitcoin ladder found fresh books. By its
construction the rule cannot lose on a ladder in which exactly one
bracket pays, so a loss would mean the ladder or the recording is not
what it is taken for.

*Corrected at 00:25 UTC on 12 November, before anything was recorded:*
the exchange lists no daily ladder on Fridays, only the weekly one, which
settles that evening. On a Friday the weekly Bitcoin ladder is the one
whose readings are counted.

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
- **The margin.** The exchange's documentation says it can tie up less
  for a set of brackets of which one can pay. See the next heading.
  Whether that is switched on for an ordinary account is not known.
- **The other side.** The bids exist to collect a reward. Somebody who is
  sold 1¢ contracts every evening may bid for fewer, or stop.
- **Company.** One seller was there tonight, within a minute of the
  quotes appearing. There is room for a second only as long as the bids
  are bigger than the first one's lots.

### What the exchange ties up for a ladder: its own documentation

Read on 12 November, after the rule above was fixed. Four pages of the
exchange's public documentation bear on it
([collateral and margin](https://docs.polymarket.us/market-structure/collateral-and-margin),
[mutually exclusive collateral return](https://docs.polymarket.us/market-structure/mutually-exclusive-collateral-return),
[directional collateral return](https://docs.polymarket.us/market-structure/directional-collateral-return),
[crypto questions](https://docs.polymarket.us/faqs/crypto-faqs)).
What they say:

- A contract sold short ties up $1, and the sale price is credited: what
  the account can still spend falls by $1 less the price. That is what
  the rule above assumes.
- A ladder of price brackets is, in the exchange's own words, "one
  mutually exclusive event per expiry": exactly one bracket settles Yes.
- For such an event there is something called collateral return. "When
  collateral return is enabled on your account" and the account is short
  in several results of one event, the requirement is "reduced by the
  smaller offsetting position size". The example is 9,000 contracts short
  in one candidate and 1,000 in another: 9,000 tied up, not 10,000.
- What is freed may be used in other events. It may not be used to add
  to the event it came from.
- Buying back one of the legs means giving the freed money back first.
  If it has been spent elsewhere, the order to buy back is refused.
- The ladders of "above" levels and the one-touch markets do not qualify
  for this or for its sister rule.

What they do not say: how an account gets it switched on, and what three
or more legs come to. The example has two. Its reasoning, that only one
result can pay, gives the largest leg for any number of legs, and I take
it so below. That is my reading and not a quotation.

What it means here:

- **Opening still takes a dollar a contract.** Freed money cannot go back
  into the same ladder, so every leg has to be paid for out of money that
  did not come from it. The seller of 11 November fits this exactly:
  10,000 contracts in 59 lots is what $10,000 opens at a dollar a
  contract.
- **Once it stands, a sold ladder ties up its largest leg.** For that
  seller about $170, with the other $9,800 free for other ladders that
  evening. The rule above lets the four coins' ladders share one $10,000.
  With collateral return each could be opened with nearly all of it, one
  after the other.
- **It bears on L1 as well.** The far brackets of one ladder are one
  event, so of all the brackets L1 sells in a ladder at most one can turn
  against it. L1's accounts tie up a dollar a contract and take no credit
  for this. The far "above" levels are different: several of them can
  pay at once, and nothing is netted there.

**A second account, added at 00:25 UTC on 12 November, before anything
was recorded.** The same rule, the same $10,000 and the same bar, with
collateral return taken as switched on. A sale must still be opened with
$1 less its price for every contract, out of money the same ladder has
not freed. Once sold, a ladder counts as tying up its largest leg at a
dollar a contract, and the rest is free for the other ladders. The first
account, written before this was read, stays the judged one. Both are
reported, and this says which came first.

### The same arithmetic elsewhere: one look, and a warning

One look, on 11 November at 23:23 UTC, at the books the general recorder
wrote down at 22:23 UTC (`state/us/`, every reward market outside sports
and crypto). No test and no rule.

Of 231 events with three or more markets, 89 have best bids that add up
to more than $1. Almost none of them is this trade, because in almost
none of them does exactly one market pay:

- Lists of nominees, where several are named.
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

**A second look, 12 November, 00:29 UTC: the sets that do have one
winner.** The exchange's list of open events (5,548 of them, with the best
bid of every market) was read once. By their names 242 events with three
or more markets ask who wins one thing: a title, a race, an award. 96 of
them have a bid on at least four fifths of their markets. In those the
best bids add up to $0.93 at the middle, $1.02 at the upper tenth and
$1.07 at the most. After the fee on each sale, one of the 96 leaves
anything over the dollar, and that one less than a cent. The sets that
settle within two weeks, a Grand Prix, a tennis final, a television
contest, stand at $1.01 to $1.03 before fees.

That is where such sums would be left by somebody who sells whole sets
whenever it pays, and the exchange's collateral return makes that cheap
to do. So this trade is not waiting to be found in sports or awards. The
daily crypto ladder, at $1.42 to $1.46 for hours on 11 November, is the
exception, and the 1¢ reward bids are why.

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

**12 November, 09:04 UTC.** The second recorder is running: the log of the
run that began at 03:34 UTC says so, and it ended with no errors and no
readings, which is right, since no ladder came within five and a half
hours of its end before 08:33. The run going now will meet today's
ladders at 16:30 UTC. The scoring script was run on what there is and
says nothing has been recorded yet.

**13 November, 09:09 UTC. The first evening.** The second recorder took
20,916 readings of 126 brackets in the four daily ladders, from 16:30 to
22:00 UTC on 12 November. 164 of the 165 readings of the Bitcoin ladder
found fresh books, so the evening counts.

- **The judged account sold once.** The Bitcoin ladder at 18:42 UTC, 198
  minutes before the end: up to 182.68 contracts in each of its 58
  brackets, $227.94 in, $19.60 in fees, $182.68 to pay at most. Locked: $25.66. At
  settlement it kept $28.24, since the bracket that paid had only 180.10
  contracts bid for. It took the whole $10,000 to open.
- **The second account did the same and no more.** No other ladder ever
  locked $10. The best reading of the Ether ladder locked 80¢, Solana's
  and XRP's a few cents. Their 1¢ bids are fewer and the bids near the
  price are for too little.
- **Two minutes later the same sale would have lost.** Put to the books
  of the next reading, 50 of the 58 legs still filled whole and the sale
  locked −$10.50. That is not a quirk of that reading. A sale would have
  locked $25 or more at 3 of the 164 readings and $10 or more at 64. Of
  those 64, 16 still locked anything two minutes on. The far bids stand
  still. The bids near the price do not, and the whole of what is locked
  is smaller than what they move in two minutes.
- **The equal-lot seller came back, smaller.** At 19:04 UTC, 46 contracts
  in each of about 50 Bitcoin brackets, those near the price included:
  about 2,300 contracts.
- **The far bids were taken whole at 21:00**, as section 9 describes.

One evening, and the bar asks for five. As it stands: the certain version
of this trade exists, on the Bitcoin ladder only, at about $25 on $10,000,
and on paper it depends on sixty orders all meeting the book that was
read. That is the first thing listed under "What paper cannot show", and
the two-minute figure says it is not a small thing.

**14 November, 09:08 UTC. The second evening: nothing.** On Fridays the
exchange lists no daily ladder, and the weekly ladders that settled on
13 November carry none of the 1¢ bids. Bitcoin's weekly ladder has 80
brackets. At most 15 of them had any bid, and the seven with a 1¢ bid
had one contract between them. Ether's and XRP's had none. No reading of
any of the four ladders locked anything, so the judged account made no
sale, and neither did the second account. No equal-lot seller came.

Over the two evenings the judged account has kept $28.24, which is
$14.12 an evening against a bar of $20, with a sale on one evening of
two.

One figure in the scoring script's description was misleading and was
changed today. Where no size locks anything, the table of each ladder's
day printed what its largest bid would have lost, as if that were the
best on offer. It now prints "nothing". The rule and the account are
untouched.

## 13. L3: the same bids while they are there, fixed at 09:12 UTC on 13 November

### Why a third test

L1 sells in the last quarter of an hour. The first evening recorded live
showed that the bids worth selling to are gone by then (section 9). They
stand from about 16:30 to 21:00 UTC, which is five and a half hours to
one hour before the daily settlement. Whoever wants them has to sell
hours ahead and not minutes ahead. That is a different risk, so it gets
its own yardstick and its own test. L1 and L2 run on as they were fixed.

What was looked at before this was fixed: the evening of 12 November in
the second recorder's books, as section 9 and section 12 report it, and
the afternoon of 11 November. Nothing else. So 12 November can only ever
be an illustration here. The test is the evenings from tonight.

### The trade, and how it differs from L1

Selling "Yes" to a 1¢ bid on a bracket far from the price, and holding
to settlement. As in L1 a contract sold keeps 0.9¢ and ties up 99¢. Two
things are different.

- **More time.** With hours to go the price can go much further than in a
  quarter of an hour, so "far" has to be further.
- **Brackets only, and at most one of them can pay.** L1 also sells
  "above" levels, and if the price runs through several of those they all
  pay. A ladder of brackets is one event with one result. However many of
  its brackets were sold, the price can end in one. So an evening's sales
  in one ladder collect 0.9¢ a contract on every bracket and can lose 99¢
  a contract on one. With twenty brackets sold at the same size that is
  18¢ collected against 99¢ at risk once, where a single L1 sale is 0.9¢
  against 99¢.

That second point is why this yardstick asks for less than L1's. It is
also the whole of the reason, and if it is wrong the test will say so
with a loss.

### Far enough: the yardstick, fixed here before it is computed

1. **What is sold:** brackets of the daily and weekly ladders of the four
   coins. No "above" levels, no "hit" markets, no up-or-down markets.
2. **Distance:** how far the index, as the exchange last published it, is
   from the bracket's nearer edge, as a share of the index. A bracket the
   index is in is never sold.
3. **Time ahead:** the time left to the bracket's end, plus the age of
   the index level, plus one minute, rounded up to the next five minutes.
4. **The reach.** From one-minute prices of each coin since 1 January
   2020, the same files as L1: take every minute as a start and measure
   how far the price stood from there that many minutes later. For each
   calendar year take the distance that only one start in 500 ended
   beyond. The reach is the largest of those yearly figures, at least 1%,
   and never less than the reach for a shorter time. A bracket is far
   enough if its distance is larger than the reach.
5. **Why "ended" and one in 500, where L1 has "went" and one in 5,000.** A
   bracket pays on where the price ends, not on what it touches. And the
   nearest bracket sold is the only one this figure is tight for. If one
   start in 500 ends beyond its edge on either side, under one in 1,000
   ends beyond it on its side, and fewer still in that very bracket. The
   sale keeps nine in 1,000. Every bracket further out is safer than
   that.
6. **The brake** is L1's, unchanged: nothing is sold if any five-minute
   change of the index in the hour before was larger than the coin's
   limit, or if fewer than six of those changes are known.
7. **The check that goes with it,** fixed now: with the brake, in no
   coin, year and time ahead did starts end beyond the reach more often
   than one in 500. If that does not hold, the yardstick is not used and
   this test does not run.

It is made by `scripts/lasthours_reach.py` and uses coin prices only.

### The yardstick, computed

Run at 09:18 UTC on 13 November, after the definition above was committed
(`caa6002`, 09:12 UTC). The reach, as a share of the price:

| Minutes ahead | 30 | 60 | 120 | 180 | 240 | 330 |
|---|---:|---:|---:|---:|---:|---:|
| Bitcoin | 3.97% | 5.34% | 7.41% | 9.05% | 10.18% | 10.99% |
| Ether | 5.02% | 6.87% | 8.90% | 10.27% | 11.61% | 12.87% |
| Solana | 8.36% | 10.76% | 14.53% | 17.50% | 20.07% | 24.31% |
| XRP | 8.18% | 10.94% | 14.38% | 16.44% | 18.93% | 21.39% |

Every figure is set by 2020 or 2021. This year alone would give Bitcoin
2.72% an hour ahead where the table has 5.34%.

The check holds. With the brake, the worst coin, year and time ahead is
Solana in 2020, four hours ahead: one start in 581 ended beyond the
reach.

At the settlement time itself, from so many minutes before 5 pm New York
to 5 pm, on the 2,506 evenings since 2020 (2,283 for Solana), leaving out
the evenings the brake stops: how many ended beyond the reach.

| Minutes before | 60 | 120 | 180 | 240 | 300 |
|---|---:|---:|---:|---:|---:|
| Bitcoin | 0 | 1 | 0 | 0 | 0 |
| Ether | 1 | 3 | 1 | 1 | 1 |
| Solana | 0 | 0 | 0 | 0 | 0 |
| XRP | 0 | 3 | 3 | 3 | 2 |

That is about what one start in 500 should give, and it shows what the
bad evening looks like. On 13 April 2024 Bitcoin ended 7.95% from where
it stood two hours earlier, against a reach of 7.41%, and Ether and XRP
went beyond theirs the same evening. A seller by this rule who was still
selling two hours before the end could have lost a bracket in each of
three ladders at once.

**An illustration, counted for nothing: the evening of 12 November,**
which was looked at before the rule was fixed.

| | Sales | Contracts | Premium after the fee | Tied up | Largest single sale |
|---|---:|---:|---:|---:|---:|
| L3-all | 70 | 35,068 | $317.86 | $34,717 | $1,980 |
| L3-10k | 17 | 10,101 | $91.55 | $10,000 | $995 |

Nothing lost. Of the 70 bids sold to, 68 still stood as large at the
bracket's next reading, two minutes on. Two thirds of L3-all is the
Bitcoin ladder: 43 brackets, $208.70. The $10,000 account was full within
a quarter of an hour of the recording's start, on the furthest brackets:
ten of Bitcoin's, 10.9% and more from the price, six of Ether's and one
of XRP's.

The last column is the other half of the trade. The $10,000 account
collects about $90 an evening and its largest sale is $995. If the price
ends in that bracket, eleven evenings of collecting are gone. And it need
not be alone: its largest sales in Ether and XRP were $495 each, and
13 April 2024 shows the coins going together.

### The rule

1. **Readings** are the second recorder's: every bracket's book about
   every two minutes from 330 minutes before its end. A reading counts
   from 330 minutes to 2 minutes before the end.
2. **The index level** is the newest one the recorder had seen published
   when the reading was taken, if it is at most ten minutes old.
3. **The sale.** If the bracket is far enough and the brake is clear:
   sell to the best bid, if that bid is at 5¢ or less, for the size shown
   at that price and at most 2,000 contracts. One sale a bracket.
4. **The fee** is 0.095 × price × (1 − price) a contract, as in L1.
5. **Two accounts,** as in L1. L3-all takes every sale. L3-10k has
   $10,000 to tie up at each settlement time, a dollar less the price
   for every contract, and takes sales in the order they come until it
   is used up. The exchange's collateral return is not assumed.
6. **Reported beside them:** for each ladder its largest sale, which is
   the most that ladder can lose; the sales of a contract or more; and
   how many of the bids sold to were still there at the next reading.

### The bar

Five evenings are left before 18 November: tonight, when only the weekly
ladders settle, and 14 to 17 November. By then: at least four evenings
recorded; L3-10k collected at least $50 an evening on average; and no
bracket it sold paid. One loss in five evenings would not be bad luck.
It would mean the yardstick is wrong.

### What is already known against it

- **Others are there.** On 12 November somebody sold to 19,100 contracts
  of these bids at 21:00 UTC, and an equal-lot seller took 46 a bracket at
  19:04. On paper this account sells as soon as its yardstick lets it,
  which for the furthest brackets is before either of them. In the book,
  whoever comes first has the bid, and one of the two firms that post
  these bids withdraws what is left as soon as it is hit.
- **The bids may not last.** Every sale costs the firm that posted the
  bid about $10 a bracket. The reward rules change on 18 November.
- **A loss, when it comes, comes in company.** It is one bracket of one
  ladder. But the four coins move together, so four ladders can lose on
  the same evening.
- **Paper fills.** The far bids stood still for hours on 12 November, so
  this is less of a worry than in L2. It is still paper.

### Notes while the test runs

**14 November, 09:08 UTC. The first evening that counts, and it was a
Friday.** Only the weekly ladders settled on 13 November. They were
recorded whole: 42,164 readings of 254 brackets from 16:30 to 22:01 UTC.

| | Sales | Of a contract or more | Contracts | Premium after the fee | Largest single sale | Lost |
|---|---:|---:|---:|---:|---:|---:|
| L3-10k | 5 | 1 | 54.7 | $0.99 | $53.17 | 0 |
| L3-all | 5 | 1 | 54.7 | $0.99 | $53.17 | 0 |

All five were in Bitcoin's weekly ladder at the first reading, 13% and
more from the price, and all five bids still stood at the next reading.
246 brackets were far enough and had nobody bidding. The firms that post
1¢ bids on the daily ladders do not post them on the weekly ones, at
least not on the day they settle. There was nothing to leave at 21:00
and nobody sold anything whole.

Verdict by the bar: not yet judged, one evening of the four asked for.
The bar is $50 an evening on average. With 99¢ on the first, the four
daily evenings to come would have to bring about $62 each. The evening
of 12 November, which counts for nothing, would have brought $92.

