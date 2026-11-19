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

## 4b. Test Q1: the last tick of a side nobody is standing on

**Fixed at 16:51 UTC on 18 November 2026, after a look at fifty minutes of
the new recorder's first run and before any market it counts had opened.**

**What was seen.** From 15:29 to 16:20 UTC today the gold market had no
bid at all. Gold was 2.8% under its price to beat, "up" was offered at 3¢
for 5,800 to 7,300 contracts, and people were buying it there a few
hundred at a time. A book with a maximum spread pays nobody while one side
is short of the target size, so for that time the $1,000 pool was paying
nobody. One order would have changed that: a bid for the target size,
5,000 contracts, at 1¢. It costs $50 if all of it is sold to. The bid side
would then hold the target, three cents from the offers where six are
allowed, and the whole score of the bid side, which is half of what each
second pays, would belong to that order. By the formula that is $18 for
those fifty minutes. Nobody sold a contract at 1¢ in them.

**The rule** (`last_tick` in `src/kht/trading/top_rule.py`), applied by
the same script to the same recordings as test G1:

1. **When.** At a reading, if the market is open and the book as read
   does *not* qualify: if the bid side holds less than the target size,
   and a bid for the target size at 1¢ would make the book qualify, that
   bid rests until the next reading. Likewise an offer for the target
   size at 99¢ when it is the offer side that is short. While the book
   qualifies as it is, nothing rests.
2. **How much.** Always the target size. Once the account has bought the
   target size at 1¢ in a market, it rests no more bids there, and the
   same for offers at 99¢. So one side of one market can cost at most a
   little under twice the target size times one cent: $100 in gold, $60
   in silver.
3. **Fills, reward, the $1 minimum, what a fill is worth:** rules 4 to 6
   of test G1, unchanged. A contract bought at 1¢ is held to settlement:
   it loses the cent, or it pays a dollar.

**One account is judged: gold and silver together.** The four coins are
described. A market-day counts as in test G1, and only markets whose
window starts after 16:51 UTC on 18 November count.

**The bar.** When at least 10 market-days on at least 6 dates have been
recorded whole and settled:

> The account passes if its net result averages at least $20 a
> market-day, its fills have cost at most a quarter of its reward, and it
> earned a reward on at least 4 of the market-days.

One look. There is no t in this bar. What the rule can lose is fixed by
its construction, so the question is not luck. It is whether the
situation comes back often enough to matter.

**What is already known against it.**

- **Anybody can do it, and the firms already there can do it bigger.**
  It pays only while they do not bother to bid a cent. The day they do,
  the side is shared by size, and 100,000 contracts at 1¢ cost them
  $1,000 at most.
- **It is the kind of order a cap is for.** It is a real order and it is
  filled whenever somebody sells at a cent. But it is seldom filled, and
  under a cap at a share of executed volume an order that is seldom
  filled earns little.
- **The formula is taken at its word,** here as everywhere.

**Added on 18 November at 21:46 UTC, from the first afternoon's
recording, which does not count: it has been tried, and it lost.** At
17:00:00 UTC, eight minutes after this section was pushed, somebody
placed a bid for 5,010 contracts at 1¢ in the gold market, which had
shown no bid at any reading since 15:06. It was sold to a few contracts
at a time
from 17:12. By 17:31 that had taken it under the target size, so the book
stopped qualifying again. Between 17:49:30 and 17:50:00 the rest of it,
4,870 contracts, was sold to in one go. By the formula the bid had earned
about $11, for the 31 minutes in which it made the book qualify. It had
paid $50. Nobody bid again for the rest of the day, and the silver market
had no bid all afternoon.

Why it was sold to is plain once seen. Selling 5,000 contracts at 1¢ into
such a bid earns $50 by the evening on $4,950 put up, with nothing to
fear short of gold rising 2.8% in four hours. Anyone with idle money
takes that. The bid has to rest for about two and a quarter hours to earn
its $50 back, and this one lasted fifty minutes.

**This changes what a pass would mean.** The paper order is not in the
book, so nobody can sell to it. It is counted as traded against only when
somebody else's order at 1¢ is, as happened today. On a day when nobody
else bids, the paper order rests for hours and is never taken, which a
real one would not be allowed to do. So the judged figure is too kind,
and I now expect the real order to lose. The rule and the bar stay as
they were fixed. Beside the judged figure the scoring script now reports
what the result would be if each order were sold to in full fifty minutes
after it first rested, as the one real order seen so far was. That figure
is described and judges nothing.

Whether the bid's appearing eight minutes after this section was made
public is chance, I cannot tell. Its size, the target plus ten, and its
time, the stroke of the hour, look like a program that was already
running. If it was not chance, then whatever this repository finds is
known to others the moment it is pushed. Whether the repository stays
public is the owner's decision.

## 4c. Test K1: small orders at the best prices of the earnings markets

**Fixed at 17:19 UTC on 18 November 2026, after reading the books of the
first such markets twice today (15:05 and 17:09 UTC) and before any event
it counts was listed.**

**What they are.** Since 16 November the exchange lists markets on a
company's quarterly figures two or three days before the company reports:
"Will Intuit report earnings per share above $2.46?", and brackets on
figures such as sales growth. Target reported on 18 November; Walmart,
Williams-Sonoma and Intuit report on the 19th. Their reward programme
(`kpic`) is two days old and pays **$250 a day for each event, for a
target size of 500 contracts**, with a maximum spread of 6¢. For its
target size it is the largest pool on the exchange: the gold market pays
$1,000 a day for 5,000 contracts.

**What was seen.** At 15:05 UTC only 6 of 27 such books qualified. By
17:09 UTC 19 of the 22 still open did: firms had arrived and were resting
575 to 6,500 contracts a side, a cent apart in most. Almost nobody trades
there (10, 2,664 and 1,189 contracts in two days in the three markets
below). Three of the seven events are a single market, which is where a
pool can be counted without guessing how it is shared:

| Event of one market | Best bid and offer at 17:09 UTC | What 100 contracts at those prices would hold | By the formula, a day |
|---|---|---:|---:|
| Intuit, earnings per share | 4,605 at 90¢, 6,571 at 91¢ | 1.8% | $4.50 |
| Walmart, earnings per share | 1,429 at 63¢, 1,391 at 64¢ | 6.6% | $16.50 |
| Williams-Sonoma, earnings per share | 1,016 at 77¢, 1,522 at 78¢ | 7.6% | $19 |

**The danger is the report itself.** The price goes to nothing or to a
dollar the moment the figure is out, and an order still resting is taken
by whoever reads the release first. The time of the report is known in
advance, so the rule leaves before it.

**The rule.** A second copy of the recorder of test G1
(`kht us-top --programmes kpic`, `state/us-kpi/`) reads the whole book of
every earnings market each half minute. `scripts/us_kpi_score.py` applies:

1. **Rules 1 to 4 of test G1, unchanged** (`top_rule.py`): orders rest
   only while the book qualifies without us and its best prices are at
   most three ticks apart; one order at the best bid and one at the best
   offer; 100 contracts a side is judged and the account never holds more
   than that either way; the same fills.
2. **The cut-off.** Nothing rests from 15:00 US Eastern on the day of the
   report if the market's own text says the company reports "after the
   market close", and from midnight US Eastern at the start of that day
   otherwise. The day is in the market's name.
3. **Closing.** At the first reading at or after the cut-off, what the
   account holds is sold to the bids as read, or bought back from the
   offers, as far down the book as it takes, and pays the fee of somebody
   who takes a price (0.095 × price × (1 − price) a contract). What
   cannot be closed is held to the result.
4. **Reward.** By the filed formula with our orders in the book. Each
   second our orders rest in a qualifying book earns the pool divided by
   86,400, times our share of the score. A reading stands for the time to
   the next, at most 60 seconds. Under $1 for a market and a UTC day
   counts as nothing.

**One account is judged: events that are one market, 100 contracts a
side.** An event is one company, one figure and one report date, as the
market names give them. An event counts if it was listed at or after
18:00 UTC on 18 November 2026, first read within six hours of its
listing, read at least 85% of the half minutes from there to the cut-off,
and read again within ten minutes after the cut-off. The events of
19 November were listed before that and count for nothing.

**The bar.** When at least 12 such events on at least 5 report dates are
finished:

> The account passes if its net result (reward after the $1 minimum, plus
> what the fills and the closing made) averages at least $5 an event,
> with t ≥ 3, each event counting as one observation.

One look, at the first check-in after both numbers are reached. Events of
several markets are recorded and described with the pool divided evenly
between their markets, which is an assumption. So is every other order
size, and what the same orders would be paid under a cap.

**Why $5.** 100 contracts a side ties up about $100 for two days.

**What is already known against it.**

- **The firms were there within two days.** A late-comer of 100
  contracts holds 2% to 8% today, and that falls as more arrive.
- **Almost nothing trades.** Under a cap at a share of what an account
  itself trades, an order that is never traded against earns nothing.
- **The cut-off covers the scheduled report and nothing else.** A company
  can warn early, a figure can leak, a date can move.
- **"For each event" is the help page's word** ("Daily (per event)"), as
  it is for games. Nobody has been paid by it.
- **It may be slow.** Outside the reporting season few companies report.
  Twelve events of one market may take until late January. The recording
  job stops on 3 December as it stands; keeping it running for this test
  is a change to the job and not to the rule.

## 4d. Test D1: between a UTR match's listed start and its real one

**Fixed at 17:41 UTC on 18 November 2026, after a look at this afternoon's
books of matches that were waiting to start, and before any match it
counts.**

**Amended at 18:35 UTC the same day, before the recorder's first run in
the job and before any match that counts** (the first are those listed to
start on 19 November, US Eastern). Two clauses were changed, rules 1 and
5 below, and this is why. I ran the new recorder for 45 minutes into a
scratch folder (17:46 to 18:30 UTC, 19 matches, readings half a minute
apart, no errors) and saw something single looks had not shown: **while
a match waits, the exchange keeps moving its listed start forward, ten or
twenty minutes at a time, and once play begins it sets the start to about
the real one.** One match went 17:50, 18:10, 18:30, 18:40 in three
quarters of an hour and had still not begun.

As first written, rule 1 let orders rest only while "the listed start has
passed". With a start that keeps moving, that would have switched the
orders off each time the start was moved on and on again each time it
passed: about 17 minutes of resting in a wait of 45. That was never the
idea, which is the title of this section. Rule 1 now keeps the orders
through the wait, and stops only if the match is put off by more than
half an hour. Rule 5's second way of counting the reward is changed with
it, so that it does not credit the larger pool for time when the listing
itself said the match was still ahead.

The same 45 minutes showed where the orders of before the match go. In
five matches somebody had 340 to 1,190 contracts a side resting until the
listed start itself. Within half a minute of it they were gone, and they
did not come back when the start was moved on. What was left was a few
contracts. Two matches went from waiting to play while being read, 5 and
20 minutes after their first listed start. In both the listing showed
play at the first point or before it, and the book did not move for the
next half minute. None of this counts for the test.

That those orders leave at the listed start to the half minute can be
read two ways, and I cannot tell which is right. Their owners may not
trust the start time, which the listing's score would cure. Or they may
know that the reward stops there, in which case the wait earns less than
either way of counting below, or nothing.

**What was found this afternoon.**

- **The exchange publishes the score.** Its public listing of events
  carries, for tennis, what its data provider says of each match: being
  played or not, the set, the score to the point, and when that was last
  updated. It needs no key.
- **UTR matches do not start when they are listed to.** They are listed
  in groups with one start time and played one after another. In last
  week's recordings the last trade of a UTR match came 2.7 hours after
  its listed start at the median, and more than 3.7 hours after it in a
  quarter of them, where a match takes an hour or two. At 17:28 UTC
  today, 10 of the 19 UTR matches past their listed start were still
  listed as not started, 49 to 209 minutes after it.
- **In that stretch the book is nearly empty.** The people who rest
  orders before a match have taken them away at the listed start (test
  R2 itself leaves ten minutes before it). The people who make prices
  during play have not come. What is left is a contract or two at the
  best prices, and in four of the waiting matches somebody resting 250 or
  more a side, eleven to fourteen cents apart, who has had the same
  thought.
- **A reward pool is running through it, and I do not know which.** If
  the exchange counts "the six hours before the start" back from the
  real start, the stretch is the last part of that period: $10 a match,
  target size 250, maximum spread 7¢. If it counts "play" from the listed
  start, the stretch is the first part of play: $50 a match, target size
  500, maximum spread 6¢. Only an account's earnings record can say.

**The rule.** A new recorder, `kht us-live` (`src/kht/trading/us_live.py`,
`state/us-live/`), follows every UTR match from a quarter of an hour
before its listed start until its market closes. Every half minute it
writes down what the listing says of the match and the whole book.
`scripts/us_delay_score.py` applies:

1. **When anything rests.** From the first reading at which the market
   is open, the listed start has passed, and the listing says in so many
   words that the match has not started: period "NS", not being played,
   no score. From then on at every reading at which the listing still
   says so and the listed start, as it then stands, is past or no more
   than thirty minutes ahead. If the listing could not be read, or says
   anything else, nothing rests.
2. **Where and how much.** 500 contracts on each side, five cents either
   side of the middle of the best bid and best offer as read, rounded
   outwards to a cent (so ten or eleven cents apart). Only if both sides
   show a price and the best prices are at most three ticks apart. The
   account never holds more than 500 either way.
3. **Fills.** Rule 4 of test G1.
4. **Leaving.** From the first reading at which the listing shows play,
   nothing rests, and what was traded against is closed at the prices
   read, down the book and over the next readings if it takes them,
   paying the fee of somebody who takes a price. So on paper an order
   stands for up to half a minute after play shows. A real one would be
   gone in seconds.
5. **The reward, worked out both ways.** *As the six hours before:* $10,
   times the seconds our orders rest in a book that qualifies by that
   period's terms, times our share of the score, over 21,600 seconds. No
   $1 minimum is applied to it alone, because it would be added to what
   an account already resting before the listed start earns in the same
   market and period. *As play:* the seconds that are past the listed
   start as it stands at that reading are counted as play, $50 times the
   same by the terms of play, over the seconds from the first listed
   start to the market's close; the other seconds are counted as the six
   hours before, as above.

**One account is judged: 500 contracts a side, every UTR match listed to
start on or after 19 November 2026, US Eastern time.** A match counts if
it was read from its listed start (no later than a minute after it) until
it was seen to start or to close, at least 85% of the half minutes
between. A match that starts on time counts, as nothing gained and
nothing lost. 250 contracts a side is followed beside it.

**The bar.** When at least 400 such matches on at least 10 US dates are
finished, one of three things is written down:

> **Passes**, if the mean net result per match (reward, plus what the
> fills and their closing made) is above zero with z ≥ 3, each US date
> counting as one observation, with the reward counted as the six hours
> before the start.
>
> **Passes only if play is counted from the listed start**, if that
> holds only with the seconds past the listed start counted as play.
>
> **Does not pass**, otherwise.

One look.

**What is already known against it.**

- **"Not started" is the listing's word.** If it is late, or wrong, the
  orders rest into play, at 500 contracts. The paper account suffers
  that as it is recorded, half a minute at a time.
- **It is not small.** 500 contracts a side is $250 to $500 a match, and
  several matches wait at once.
- **Somebody is already there** in some of these matches, at half the
  size and further from the price.
- **A resting order changes what it rests in.** In the 45 minutes of the
  trial one waiting book lost every order near its price half a minute
  after a sale of a sixth of a contract. Whoever keeps those small
  orders takes them away at the first sign of anything. The paper
  account counts a fill only when a trade is recorded at its price. It
  cannot see the trade that 500 contracts standing there would have
  drawn from somebody who knew why the others had left.
- **What the stretch is paid is not known at all,** which is why the
  verdict has to say which reading it needs. It may be paid nothing: the
  people who rest orders before a match leave at the listed start to the
  half minute, and they may know why. One evening of real orders would
  show it. That needs the order program and a key, and is the owner's
  decision.

**What this says about test R2.** R2 counts its reward over the six hours
before the *listed* start. If the exchange counts those six hours back
from the real start, the first part of R2's resting is outside the paid
period by as long as the match is late: about a sixth of the reward for a
match an hour late, half for one three hours late. R2's rule and bar are
not changed. Its result will be read with this beside it, and the new
recordings will say how late its matches were.

The trial adds one thing to this. Once play begins the exchange sets a
match's start to about the real one. If it works its rewards out
afterwards from that field, "the six hours before the start" are the six
before play, which is the reading under which R2's figure is too high.
I still cannot tell from outside.

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

The order of section 4b looked like a second way: on an afternoon when
the gold market shows no bid, a buy order for 5,000 contracts at 1¢,
earning about $22 an hour by the formula. *Corrected the same day,
21:46 UTC:* somebody placed that order at 17:00 UTC and it was sold to in
full within fifty minutes (section 4b). As a way of learning whether the
exchange pays its formula it would still work, since about $11 of reward
would show on the earnings record. But it costs its $50, which the rugby
order does not. I would not place it.

## 6. Notes while the tests run

*At each check-in:* `python scripts/us_rewards2_score.py --settle`,
`python scripts/us_top_score.py --settle` (which scores G1 and Q1),
`python scripts/us_kpi_score.py --settle` (K1) and
`python scripts/us_delay_score.py --settle` (D1), the figures written
here with their date, and nothing in sections 3 to 4d changed.

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

**18 November, 16:59 UTC. Following the ITF trading as a buyer, looked
at once more and closed.** Section 2 said the trading before an ITF match
points to the winner and left "about a cent" for somebody who follows it.
That was one contract a game in the direction of the game's whole flow, at
the last middle. Done the way a follower would have to do it, it is worse.
Take every trade the week's recordings saw before a game, and buy one
contract the same way at the best price of the next reading, about two
minutes later, paying the fee, and hold it to the result (exploration, on
the same week):

| Programme | Trades followed | Games | A trade, after the fee | t by game |
|---|---:|---:|---:|---:|
| ITF tennis | 3,409 | 1,079 | −1.4¢ | −1.1 |
| ITF, the game-start field a placeholder | 630 | 283 | −2.8¢ | −1.2 |
| UTR tennis | 385 | 189 | −4.4¢ | −1.6 |
| Table tennis | 1,728 | 993 | −3.5¢ | −2.9 |
| E-sports | 2,312 | 254 | −6.2¢ | −1.6 |
| ATP and WTA | 3,769 | 339 | −7.2¢ | −3.6 |

Even at the price the trade itself went at, a follower in ITF is 0.9¢
behind after the fee. In the games whose start time was wrong the paper
orders lost because the price ran away from them during play, not because
somebody else's stale order was left for a late-comer to take: by the
next reading the book had moved. Whoever does take those orders is there
in seconds with the score in front of them. Two-minute readings and no
score feed cannot follow that, and there is no test to make of it.

**18 November, 17:19 UTC. Two more things looked at this afternoon, and
where test K1 came from.** Exploration, read once from public data.

*The exchange's own grouping of markets into events.* A pool is "per
event", so only an event that is one market has a pool that can be
counted without guessing. Earlier today I had grouped markets by their
names, which is wrong outside sports. By the exchange's own listing of
5,367 events, 66 open markets in the programmes that pay by the day are
an event alone.
Apart from the six up-or-down markets already recorded, the large ones
are five UFC main events ($310, target 20,000: deep books), and three
earnings events at $250 a day for a target of 500. Test K1, section 4c,
is the earnings events.

*Daily temperature markets* (the day's high in five cities, six brackets
a day, pool $185 for each event, target 7,500, no maximum spread). Two
findings. Their prices sit within a cent or two of the same contracts on
Kalshi, a busier exchange whose prices I read only as a yardstick, so
there is nothing there for a buyer after the fee. And of 90 markets no
bid side holds the target size, and only 9 offer sides do. Eight of the
nine are brackets the day has already ruled out or all but ruled out,
where somebody offers between 11,600 and 298,000 contracts at 1¢. That is
hundreds of thousands of dollars held against orders that cannot lose,
to collect the pool by size. It is
the rugby market again, every day. A small account can only have its
share by size there. But it is one more sign that orders of this kind are
being paid: nobody ties up that much for nothing.

**18 November, 17:23 UTC. Test K1 is in the recording job.** Its rule
was committed at 17:20 UTC. The job's file was changed at 17:21 UTC to
start the second recorder (`state/us-kpi`), and the run that begins at
about 20:28 UTC is the first to carry it. Tried against the exchange for
two minutes before that, into a scratch folder: 22 earnings markets, each
read every half minute, with its pool, target size, maximum spread,
listing time and "before the open" or "after the close" written down, and
no errors. The events of 19 November will be recorded from this evening
and described. They cannot count: they were listed on 16 and 17 November
and I had read their books. The four check-ins now score Q1 and K1 as
well.

**18 November, 17:45 UTC. Test D1 is in the recording job too.** Its rule
was committed at 17:42 UTC and the job's file changed at 17:43 UTC, so the
run that begins at about 20:28 UTC carries its recorder
(`state/us-live`). Tried against the exchange for three minutes before
that, into a scratch folder: 29 UTR matches followed, each read every
half minute, the listing read seven times, no errors. Of the 29, 10 were
listed as being played or suspended, 1 as finished, and 18 as not
started: 4 not yet at their listed start and 14 more than three hours
past it. Most of those 14 are pairings of a group whose earlier matches
were still going on, with an empty book. The check-ins now score all five tests.

How the idea was reached, for the record. The follow-up on ITF above made
me look for the moment a match really starts. The exchange's event
listing turned out to carry it, with the score. Laying that beside the
listed start times showed that UTR's are not match times but group
times. That is exploration. What it suggests is test D1, on matches not
yet played.

**18 November, 17:51 UTC. A fault of my own making in the recorder of
tests G1 and Q1, found before it could cost anything, and mended.** The
change of 15:36 UTC above taught a new run to take the last market an
earlier run had read as its starting point for finding the next one. I
had it mark that market as finished. But a run lasts five hours and a
market a day: when a run starts, the market of the run before is nearly
always still open. Marked as finished, it would not have been read again,
by that run or any after it. Every market would have been recorded for
the first few hours of its day only, no market-day would ever have been
"recorded whole", and tests G1 and Q1 would have had nothing to judge.

I found it by asking, while reading the newer recorders through, what
happens at the start of a run, and then trying it: a run started from a
folder in which an earlier run had written down an open market read no
book at all. The mended recorder reads such a market like any other until
it sees it closed. Three tests cover it: a run that starts while a market
is open goes on reading it and sees it close; a run that starts between
two markets looks at the old one, finds it closed and leaves it; and a
market whose book cannot be had any more is given up after an hour. Tried
against the exchange from a copy of today's recordings, as tonight's run
will start: all six open markets read from the first half minute, with
their terms and reference prices, no errors.

No recording is affected. The run going since 15:28 UTC has the older
code, which has no such starting point at all. The first run with any of
today's changes begins at about 20:28 UTC and will have the mended code.
The rules and bars of G1 and Q1 are untouched.

**18 November, 17:56 UTC. The job's requests, counted against the
exchange's limit.** The exchange allows twenty requests a second from one
address. With two more recorders in the job I counted what its programs
may ask between them and set the two new ones to three a second each:
eighteen for the five recorders together, and the rehearsal of the order
system reads a few books a minute beside them. The recorder of matches
also waits three minutes before its first reading of the reward schedule,
since every other program reads it the moment it starts. A request that
is refused is tried again, so the cost of going over would have been late
readings, not lost ones. The check-ins look at the gaps between readings.

**18 November, 18:35 UTC. Test D1's rule amended before any of its data
exist.** Section 4d says what was changed and why: the exchange moves a
waiting match's listed start forward a little at a time, which the rule
as first written did not expect. The amendment was made after the rule
was first fixed (17:41 UTC) and before the recorder's first run in the
job (about 20:28 UTC) and the first match that counts (19 November, US
Eastern). The bar is as it was. Three new tests cover the amended
clauses.

**18 November, 21:43 UTC. The first run with today's changes, checked.**
The run that began at 15:28 UTC ended well at 20:27 and started the next
one, which has all of today's code. From its save of 21:27 UTC:

- *The recorder of tests G1 and Q1* picked up the six open markets 82
  seconds after the run before it had last read them, which is the
  restart that the fault mended at 17:51 UTC would have broken. 624
  readings since, exactly half a minute apart, with each market's terms,
  and the exchange's reference price of each asset in fifteen-second
  candles without a gap or a repeat.
- *The earnings recorder (K1)*: 22 markets, 104 readings each, the
  longest gap 33 seconds, with when each was listed and whether its
  company reports before the open or after the close. No errors.
- *The recorder of matches (D1)*: 30 UTR matches, 2,448 readings, the
  longest gap 34 seconds, the listed start, the period and the score on
  every one, and both reward periods' terms for every match. Seven
  matches went from not started to play while being read. No errors.
- *The two paper accounts before games (R2)*: 145 games each, 23 of them
  UTR, as before.

The three scoring scripts read the new files. Nothing is judged: none of
today's markets, events or matches counts.

Two things from those first hours, described only. For test Q1: in the
5.8 hours of today's gold market that were recorded, the paper bid at 1¢
would have rested for 4.1 hours, earned $88 by the formula, and been
sold to for 4,982 contracts, $50. *Looked into at 21:46 UTC:* those
sales were real ones, to a real bid. Somebody placed the very order of
test Q1 at 17:00 UTC and was sold to in full by 17:50. Section 4b now
says what that means: a real order of this kind does not get to rest for
four hours, the paper figure is too kind, and I expect the test's order
to lose in practice whatever its paper result. For test D1: four matches
were followed from their listed start to play. They waited 3, 4, 22 and
26 minutes. The orders would have rested through three of those waits
and been traded against in none.

**19 November, 00:17 UTC. The first markets that count for tests G1 and
Q1 were picked up as they opened.** From the saves of 22:03, 23:03 and
00:03 UTC:

- The six markets of the day before were read to their end and seen to
  close: last open at 21:59:50, closed at 22:00:20.
- The six new ones were first read open 21 seconds (Solana), 4 to 5
  minutes (Bitcoin, Ether, XRP) and 3 minutes 50 seconds (gold and
  silver, whose window began at 23:15) after their windows began. The
  rule for a whole market-day allows 15 minutes. The recorder had looked
  for each by name from a minute before; the exchange opened their books
  a few minutes into the window. Each has its window, price to beat,
  pool, target size and maximum spread written down.
- The new markets' readings are half a minute apart, the longest gap 30
  seconds.
- The reference prices are in fifteen-second candles without a repeat.
  They have one hole of 14 minutes for gold and silver, from 22:01 to
  22:15 UTC, when neither had a market open. No test uses them, and the
  exchange's own history has those minutes if they are ever wanted.

So the first market-day of gold and silver that can count is under way.
It closes at 22:00 UTC today. In its first 35 minutes both books
qualified at every reading, 100 contracts at the best prices would have
held 5% of gold's score and 7% of silver's, and the paper orders were
traded against fifteen times in each. That is described and decides
nothing.

The earnings recorder is running: 22 markets every half minute since
20:28 UTC, no errors. The three events of one market still stand a cent
apart with 1,700 to 6,500 contracts a side. Five of the nineteen brackets
in the events of several markets have never qualified in that time. None
of the events of 19 November counts.

One thing the scan of the reward schedule showed after the rules were
fixed, which changes nothing in them: of 15,929 open markets in daily
programmes, many are paying nobody at the moment they were read, because
one side does not hold the target size or the two sides are too far
apart. Three quarters of the daily Bitcoin brackets, 21 of 27 earnings
markets, 84 of 100 markets on the 2028 state winners. Making such a book
qualify takes the whole target size on both sides, which is market making
with a view on the price and not what either test does. It is noted here
as a third thing to look at once these two have reported.
