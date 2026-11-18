# Round six: Polymarket US only

*Begun 18 November 2026, 14:38 UTC, on the owner's instruction: "keep
looking ... look exclusively at Polymarket US for alpha that we can
extract". Sections 1 and 2 are a second reading of what was already on
disk, and a fresh look at the exchange. That is exploration: it can
suggest, and it proves nothing. Sections 3 and 4 fix two new paper tests
before any of their data exist. No order has been placed and no key was
used.*

## 1. Where the last round left things

Four paper tests ended this morning and none passed (`README.md`). Two
things in them were worth a second look.

- The reward orders before games (test R1) lost money, and nearly all of
  the loss was the ITF tennis tour. Somebody was on the other side of
  those fills and was right. Who, and can it be followed?
- One programme in that test did what the idea said it would: UTR tennis.
  It had been named in advance only as half of an account, so it counted
  for nothing. It is where a new test can start.

And one thing had never been done: reading the exchange's reward rules as
filed with its regulator against what is actually resting in its books,
market by market, to see who collects the rewards and how.

## 2. What the second reading found

### The ITF loss, taken apart

**The trading before an ITF match says who wins.** For each game of test
R1, add up the trading that hit the paper orders: contracts bought minus
contracts sold. Then take one contract in that direction at the last
middle of the book before the start, and hold it to the result.

| Programme | Games with trading | One contract with the flow made | t | Dates ahead |
|---|---:|---:|---:|---|
| ITF tennis | 1,108 | +4.25¢ | 3.59 | 7 of 7 |
| Table tennis | 976 | −0.87¢ | −0.57 | 3 of 7 |
| ATP and WTA | 339 | −3.38¢ | −1.41 | 2 of 7 |
| E-sports | 253 | −1.77¢ | −0.63 | 3 of 7 |
| UTR tennis | 188 | −2.22¢ | −0.70 | 3 of 7 |

Against the first price seen it is 5.8¢ (t 4.5). The price itself moved
only 1.6¢ with the flow. So in ITF, and nowhere else, the people who trade
before the match know something the price does not take in. That is what
the paper orders were losing to.

**Part of it is not "before the match" at all.** The exchange's own record
of each market carries the time the game started. For most sports it
agrees with the start time the recorder was given. For ITF it does not:

| Programme | Games with trading | The exchange's game start is more than 10 minutes before the listed start |
|---|---:|---:|
| ITF tennis | 1,109 | 23.5% |
| Darts | 60 | 26.7% |
| UTR tennis | 190 | 3.2% |
| Tennis doubles | 79 | 2.5% |
| E-sports | 253 | 2.4% |
| ATP and WTA | 339 | 0.0% |
| Table tennis | 985 | 0.0% |

In all but one of those 261 ITF games the game-start field is a
placeholder (midnight) and the listed start kept being moved. In one in
seven of them the market's last trade came *before* the start the recorder
was working to: the match was over. The paper orders were resting through play, at prices from
before it, against people watching the score.

Split that way, test R1's ITF account at 100 contracts a side looks like
this:

| ITF games | Games | Reward | Fills, held to the result | The same at the price before the start | Net |
|---|---:|---:|---:|---:|---:|
| Start time cannot be trusted | 560 | $1,176 | −$2,407 | −$244 | −$1,231 |
| Start time agrees | 1,066 | $689 | −$1,487 | −$395 | −$798 |

So the mis-timed games are the worse half, about 12¢ lost on every
contract filled. But the other half loses too. And in the games whose
start time agrees, trading with the flow still made 3.8¢ a contract
(847 games, t 2.7).

**It is real, and it is not worth following as a buyer.** Somebody taking
the flow's side pays half the spread and the fee. The fee is 0.095 × price
× (1 − price), about 2¢ to 2.4¢ a contract through the middle of the price
range, where the effect is. That leaves about a cent, on one week, found
after the fact. It is written down here and not made into a test.

What it does give is a reason never to rest orders in ITF again, and a
reason to trust a programme where this does not happen.

### UTR: the programme where the arithmetic held

Test R1's rules, unchanged, on UTR games alone, all 486 of them:

| Contracts a side | Reward after the $1 minimum | Fills, held to the result | Net | A game | z by date | Dates ahead |
|---:|---:|---:|---:|---:|---:|---|
| 100 | $585 | −$227 | +$358 | $0.74 | 1.94 | 6 of 7 |
| 250 | $1,323 | −$234 | +$1,089 | $2.24 | 2.97 | 7 of 7 |
| 500 | $1,666 | −$206 | +$1,460 | $3.00 | 2.15 | 6 of 7 |

The pool is $10 a match. At 100 contracts the paper order held 27% of the
score, so other people are already resting there and collecting; they have
been since the programme began on 8 October. Few people trade UTR before
the match: 5,400 contracts hit the paper orders in a week, against 76,000
in ITF. About 23 UTR matches were in their six hours at any moment, 54 at
most, with about $97 resting in each for every 100 contracts.

This is one week, and UTR was picked out after seeing it. Section 3 tests
it on games that have not been played.

### How the reward formula treats the top of the book

The filed rules (`docs/09_sports_rewards.md`, section 9) score a side like
this: walk from the best price outwards until the target size is reached;
every order on the way scores its size times the discount factor raised
to the number of ticks from the best price; a participant's share of the
side is its score over everybody's. The discount factor is 0.3 to 0.5 in
most programmes.

Two consequences I had not drawn.

- **One tick is worth more than three times the size.** An order one tick
  behind the best price scores 30% to 50% of what it would at the best
  price. Test R1 put its orders at the first price with 20 of other
  people's contracts behind it, because "a tenth of a contract at the best
  price ... is not a price anybody stands behind" (`docs/09`, section 5,
  rule 3). So wherever a tenth of a contract stood at the best price, the
  paper order stood a tick behind it and gave away most of its score.
- **Those tenths of a contract are not noise. They are how the reward is
  collected.** Somebody rests the target size far from the price, where it
  will never trade and scores next to nothing, and a tenth of a contract
  at the best price, which then holds nearly all of the side's score. In
  the gold market on 13 November at 15:33 UTC the best bid was a tenth of
  a contract at 62¢ and the next bid was 5,000 contracts at 51¢. By the
  formula the tenth of a contract held 92% of the bid side.

The amended rules in force from today name "placing quotes with no bona
fide intent to trade" as gaming and let the exchange cap a reward at a
share of what the account itself trades. Both are aimed at exactly this.
No cap is published yet. An order of real size at the best price is the
opposite case: it is the thing the programme says it pays for.

### The reward schedule on 18 November

Read at 15:04 UTC: 54,716 markets, and outside the games 88 daily
programmes. What stands out for a small account:

**Programmes that are one market.** Their pool belongs to that market
whatever the exchange means by "shared across a programme's markets"
(`docs/08_rewards.md`, section 4).

| Market, listed afresh each day | Pool a day | Target size | Maximum spread | Who is there |
|---|---:|---:|---:|---|
| Gold up or down | $1,000 | 5,000 | 3¢ | two or three firms, 5,000 to 15,000 contracts a side |
| Silver up or down | $750 | 3,000 | 3¢ | the same |
| Bitcoin up or down | $400 | 10,000 | 3¢ | not enough: see below |
| Ether, Solana, XRP up or down | $150 | 2,000 | 5¢ | not enough on two of three |

**Books that are paying nobody.** A programme with a maximum spread pays
a second only if both sides hold the target size at prices no more than
twice that spread apart. At 15:06 to 15:15 UTC today:

- gold had no bid at all (7,315 contracts offered at 3¢): not paid;
- Bitcoin reached its 10,000 at 13¢ on the bid and 32¢ on the offer, 19¢
  apart where 6¢ is allowed: not paid;
- Solana and XRP reached theirs at prices 18¢ and 22¢ apart, where 10¢ is
  allowed: not paid;
- silver had no bid either: not paid;
- Ether qualified.

In the three-hourly snapshots of the last week the gold and silver books
qualified at 71% and 73% of the readings.

**What a small order at the best price would hold there.** In the same
snapshots, 100 contracts joining the best bid of the gold market would
have held 3% of the bid side at the median, and 13% on average, because
now and then the firms stand a tick or more behind and the best price is
almost empty. Those are also the moments when it is most dangerous to be
there. Section 4 measures both.

**The size game, which a small account cannot play.** On long shots the
best offer is 1¢ and nobody can better it, so the score goes by size
alone. In the futures on the NFL and NBA champions somebody offers 200,000
to 350,000 contracts at 1¢ or 2¢ on one long shot after another.

**A market that was decided three days ago and still pays.** The Rugby
League World Cup final was played on 15 November: Australia 32, New
Zealand 12. On 18 November the two markets on the winner were still open
(they are listed to 30 November) and their programme still pays $600 a
day between them, with no maximum spread. There is a bid of 164,495
contracts at 99¢ on Australia and an offer of 164,193 at 1¢ on New
Zealand. That is about $325,000 resting where it cannot lose, for up to
$600 a day, 0.18% a day. A late-comer gets the same 0.18% on whatever it
adds, for as long as the market stays open.

It is small. But it is the one place found where the reward can be
collected with no risk from the market at all, which makes it the cleanest
way to learn the thing no paper test can show: whether the exchange pays
what its formula says (section 5).

## 3. Test R2: resting orders before UTR matches

**Fixed at 15:27 UTC on 18 November 2026, before any game it counts had
entered its six hours.**

The recorder of test R1 is started again as it was. Its rules are those of
`docs/09_sports_rewards.md`, section 5, and are not changed. From the same
readings of each order book it now keeps a second paper account beside the
first, which differs in one thing only:

- **first account** (`state/us-rewards`): each order rests at the first
  price, counting from the best, by which other people's orders add up to
  20 contracts. This is rule 3 of test R1.
- **second account** (`state/us-rewards-top`): each order rests at the
  best price itself, whatever rests there.

Everything else is the same for both: six hours before the listed start
until ten minutes before it; a reading about every two minutes; nothing
rests if the two prices are more than 10¢ apart; the reward by the
published formula with our order in the book; under $1 for a market and a
US date counts as nothing; a fill whenever the running totals say an order
at our price could have been traded against, with us first in line; fills
held to the result; a called-off game pays what it settled at and earns
nothing.

**Two accounts are judged**, both on UTR games only (the programme
`utr_moneyline_day_of`), and only on games whose listed start is on or
after 19 November 2026, US Eastern time:

- **R2-utr**: the first account at 250 contracts a side. This is last
  week's UTR result asked again of new games. 250 is the size at which
  last week's result was clearest, which is a choice made after seeing
  it; that is why it has to be shown again.
- **R2-top**: the second account at 100 contracts a side. This is new. It
  asks whether standing at the best price, as the formula rewards, pays
  for the extra fills it invites.

**The bar, for each.** A game is judged once it started more than 12
hours ago and its settlement is on file. When at least 800 UTR games on
at least 12 US dates have been judged:

> The account passes if its mean net result per game (reward after the $1
> minimum, plus fills at settlement) is above zero with z ≥ 3, each US
> date counting as one observation.

There is one look at the verdict, at the first check-in after both
numbers are reached. Earlier looks are written down and decide nothing.
Every other programme and every other order size is recorded and
described, and judged by nobody.

**What a pass would be worth, and what it would not.** At 250 contracts a
side last week's games made about $155 a day on paper with about $5,600
resting on average. A pass would say the formula's arithmetic holds for
UTR over three weeks. It would not say the exchange pays the formula. It
would not say the programme will still be there, uncapped, in a month.

**The start-time fault.** In UTR the listed start was wrong in 44 games of
486 last week, and those 44 lost $108 at 100 contracts a side. The rule is
not changed to dodge them: a real order could not have known. They are in
the judged account.

## 4. Test G1: small orders at the best prices of the single-market programmes

**Fixed at 15:27 UTC on 18 November 2026, before the first market it
counts had opened.**

A new recorder, `kht us-top` (`src/kht/trading/us_top.py`,
`state/us-top/`), reads the whole book of each daily up-or-down market
(gold, silver, Bitcoin, Ether, Solana, XRP) every thirty seconds, which is
as often as the public book changes, with the running totals of trading.
It decides nothing. The rule is applied afterwards by
`scripts/us_top_score.py`, and is `src/kht/trading/top_rule.py`:

1. **When anything rests.** At a reading, only if the market is open, the
   book as read qualifies for its reward without us (both sides hold the
   target size, at prices no more than twice the maximum spread apart),
   and the best bid and best offer are at most three ticks apart.
2. **Where.** One order at the best bid and one at the best offer, as
   read. A price is never improved and never crossed.
3. **How much.** 100 contracts a side is the size that is judged. 25, 50,
   250 and 500 are followed beside it. The account never holds more than
   its order size either way: what it already holds is taken off its bid,
   and what it already owes is taken off its offer.
4. **Fills.** Between two readings: if contracts traded, and their average
   price, a newer last trade or a new low was at or below our bid, the bid
   is filled for as many contracts as traded, up to its size; likewise the
   offer, with the high. If other people's offers now stand at our bid or
   below, the bid is filled for their size. This puts us first in line
   and sends all the trading through us. It is the fill rule of test R1.
5. **Reward.** By the filed formula, with our orders in the book: for each
   second the book qualifies, our share of each side's score, halved and
   summed; divided by the seconds the market was open; times the pool. A
   reading stands for the time to the next one, at most 60 seconds. Under
   $1 for a market and a day counts as nothing.
6. **What a fill is worth.** Held to settlement, or closed by the opposite
   fill. No fee, since a resting order pays none.

**One account is judged: gold and silver together, 100 contracts a side.**
A market-day counts if it was recorded whole: first read within 15 minutes
of the start of its window, read at least 85% of the half minutes it was
open, and seen to close. Only markets whose window starts after 15:27 UTC
on 18 November count.

**The bar.** When at least 10 market-days on at least 6 dates have been
recorded whole and settled:

> The account passes if its net result (reward after the $1 minimum, plus
> what the fills made) averages at least $20 a market-day, with t ≥ 3,
> each market-day counting as one observation.

One look, at the first check-in after both numbers are reached. The four
coins are recorded and described, and so is what the same orders would
have been paid under a cap of 100%, 50% and 10% of what they traded.

**Why $20.** 100 contracts a side ties up about $100 a market. Below $20 a
day on that, the risk of being the order at the front of a fast market is
not being paid for.

**What is already known against it.**

- **The good seconds are the dangerous ones.** The order holds most of a
  side's score exactly when the firms have stepped back from the best
  price. They step back when the price is moving.
- **A thirty-second book.** A real order at the best price can be traded
  against at any moment. The paper account sees the totals move only
  every half minute, and follows the best price only that often. The fill
  rule is unkind to make up for it. It may not be unkind enough.
- **Rule 1 is also the weakness.** The account rests only while others
  make the book qualify. If they see a small order collecting beside them
  they can stand at the best price themselves, and the share falls to a
  few percent.
- **The exchange can cap it.** Under a cap an order that is seldom traded
  against is paid little. That is reported with the result.

## 5. What no paper test can show, and the cheapest way to learn it

Every reward figure in this project is the published formula applied to
recorded books. Nobody has been paid a cent of it. Three things are taken
on trust: that the exchange pays what the formula says; how a programme's
pool is shared between its markets; and that a small account's orders
are scored like anyone's.

Only an account's own earnings record can settle these. Until today every
way of getting one meant taking some market risk. The rugby market of
section 2 does not: a bid at 99¢ on a result that is already known can
only be filled at a profit, and by the formula it earns its share of that
market's pool every day it stays open. About 1,100 contracts ($1,089
resting) should earn about $2 a day if the market's share of the pool is
$300, enough to clear the $1 minimum and to be read off an earnings
record. It needs no program and no key, only an order placed by hand, and
it is the owner's decision.

## 6. Notes while the tests run

*At each check-in:* `python scripts/us_rewards2_score.py --settle` and
`python scripts/us_top_score.py --settle`, the figures written here with
their date, and nothing in sections 3 and 4 changed.

**18 November, 15:31 UTC. Both tests are recording.** The rules above were
committed at 15:27 UTC. The recording job was started again at 15:28 UTC
(run 59 of *us-rewards*), with the second paper account, the new
recorder, the ladder recorder and the order system rehearsing on UTR
matches only. The watchdog that restarts it is switched on again. The job
stops by itself on 3 December.

Tried against the exchange for two and a half minutes before that, into a
scratch folder: the new recorder found the six markets, read each every
half minute and wrote their terms down, with no errors. Tomorrow's gold
and Bitcoin markets are already listed but have no book until their
window starts, so the recorder looks for each by name from a minute
before and waits for it.

Check-ins are set for 20, 24 and 27 November and 2 December. The first
whole market-day of G1 is the gold and silver window that opens at 23:15
UTC tonight. The first games of R2 are those of 19 November, US Eastern.

**18 November, 15:36 UTC. A fault in the new recorder, found by reading
it again and mended before it could cost a market-day.** The recorder
found each day's new market from the one before it, but only while that
one was still being read. Gold's and silver's close at 22:00 UTC and the
next open at 23:15, so the hand-over would have been left to the reading
of the reward schedule, a quarter of an hour apart, and the first reading
of the new market could have come later than the 15 minutes section 4
allows. It now asks every market it knows of, closed or not, and a run
that starts between two markets takes the last one an earlier run read
as its starting point. Three tests cover it. The job's run that began at
15:28 UTC still has the old code; the run after it, at about 20:28 UTC,
installs the new one, well before 23:15. The rule and the bar are
untouched.

**18 November, 16:41 UTC. The first hourly save, checked.** The job's
first save came at 16:29 UTC. The new recorder had 618 readings of the six
markets from 15:29 to 16:20, half a minute apart (the longest gap 33
seconds), with each market's pool, target size, maximum spread, window and
price to beat written down. Both paper accounts before games were being
kept from the same 313 games, 61 of them UTR, and the order system was
rehearsing on UTR. No errors. The run is still going. Today's markets and
games count for neither test.

**18 November, 16:47 UTC. The exchange publishes its own reference
prices, and the recorder now keeps them.** Its documentation lists an
"Asset Prices" call that needs no key: the price its gold, silver and coin
markets settle on, as candles down to one second
(`/v1/asset-prices/history`; for gold and silver a Chainlink spot stream,
for the coins the market's reference index). One-minute candles go back to
20 October for gold and to 1 September for Bitcoin. The recorder now
writes fifteen-second candles of each market's asset beside the books
(`prices.csv.gz`), from the job's next run at about 20:28 UTC. Nothing in
test G1 uses them: its rule stands at other people's prices and has no
view of its own. They are there so that each paper fill can be set
against where the price went in the minutes after it, which says in days
what day-end results would take weeks to say, and so that a rule with a
view of its own can be tried on the same recordings later.

One thing the scan of the reward schedule showed after the rules were
fixed, which changes nothing in them: of 15,929 open markets in daily
programmes, many are paying nobody at the moment they were read, because
one side does not hold the target size or the two sides are too far
apart. Three quarters of the daily Bitcoin brackets, 21 of 27 earnings
markets, 84 of 100 markets on the 2028 state winners. Making such a book
qualify takes the whole target size on both sides, which is market making
with a view on the price and not what either test does. It is noted here
as a third thing to look at once these two have reported.
