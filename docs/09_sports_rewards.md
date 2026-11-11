# 09 — Rewards in sports games, and a paper test fixed in advance

*11 November 2026. A lead with a test attached. Nothing here has been
tested with money, and nobody has been paid anything. Sections 1 to 4 are
what was looked at; section 5 fixes a test before any of its data exist;
results will be added from section 8 on.*

## 1. What this adds to docs/08

`docs/08_rewards.md` found that Polymarket US pays people for leaving
orders resting, looked at the programmes outside sports, and could not tell
whether a pool was for a whole programme or for each event in it. That one
question decided whether the idea was worth cents or dollars.

Sports answers it. Seven-eighths of the exchange is sports, nearly all of
the reward money is there, and in sports a pool can only belong to one
game, because its periods are counted from that game's start:

- **early**: from listing until six hours before the start;
- **day-of**: the six hours before the start;
- **live**: from the start until settlement.

Three things say a pool is one game's.

1. **The exchange's wording.** A time period is "a window during the event
   lifecycle ... with its own reward pool", and the pool is "the total
   amount paid out for a time period, shared across the program's markets".
2. **What other people do.** On nearly every game somebody rests thousands
   of contracts at 1¢ and at 99¢. Such an order scores nothing. Its only use
   is to make that side of that book reach the programme's target size, so
   that the side is paid at all. Nobody would lock up money in a thousand
   games a day to do that if a few dollars were shared among all of them.
3. **How earnings are reported.** The exchange's API lists what an account
   earned by market and by date.

This is evidence, not proof. Only an account's own earnings record is proof.

## 2. What is on offer before games

Read from the public schedule on 11 November at 09:14 UTC
(`GET /v1/incentives`). These are the programmes on who wins a game
("moneyline") in which that market is the programme's only market in its
game, so that the pool is not shared with anything.

| Programme | Pool for the six hours before a game | Target size | Discount | Max spread | Games listed for 11 Nov |
|---|---:|---:|---:|---:|---:|
| Tennis, lower tours (ITF) | $12 | 7,500 | 0.35 | none | 239 |
| Tennis, UTR | $10 | 250 | 0.35 | 7¢ | 72 |
| Tennis, main tours | $40 | 19,000 | 0.30 | none | 38 |
| Tennis, doubles | $10 | 6,000 | 0.30 | none | 39 |
| E-sports | $10 | 15,000 | 0.35 | none | 50 |
| Darts | $5 | 2,500 | 0.50 | none | 25 |
| 3×3 basketball | $6 | 4,000 | 0.50 | none | 23 |
| Beach volleyball | $6 | 4,000 | 0.50 | none | 15 |
| NHL | $33 | 12,000 | 0.25 | none | 0 (7 on the 12th) |
| UFC, main card | $625 | 20,000 | 0.30 | none | 0 (5 on the 15th) |

For the games still listed for 11 November that is about $6,400 in pools
for the six hours before the start. The same games carry larger pools while
they are being played ($52 for an ITF match, $184 for a main-tour match).
Those are left alone here: resting orders during play need software far
faster than anything in this project.

Table tennis has a $5 pool, but it is shared by three markets of each match
(the winner and two totals), and how it is divided between them is not
published. E-football has $2 across three or more markets. Both are too
small or too uncertain to build on.

## 3. What the order books show

*Looked at once, on 11 November at 09:14 UTC: every sports market within
seven hours of its start or under way, 1,860 order books with their sizes.
This is a look, not a test. The figures below use the 207 games in the
programmes of section 2 that were in their six hours and more than ten
minutes from their start.*

**Who is there.** Typically one or two professional accounts. They rest a
few hundred contracts a cent or two apart at the real price, and far away,
at 1¢ and 99¢, the thousands that make the side reach its target.

| Programme | Games | Sides that would be paid | Median score on a side | Share of it an extra 100 contracts would hold |
|---|---:|---:|---:|---:|
| ITF | 101 | 87% and 96% | 577 | 14% |
| Darts | 25 | 48% and 56% | 13 | 25% |
| E-sports | 22 | 18% and 18% | 127 | 2% |
| Main tours | 16 | 56% and 62% | 2,239 | 2% |
| Doubles | 16 | 94% and 88% | 421 | 19% |
| UTR | 10 | 50% and 50% | 42 | 21% |
| Beach volleyball | 7 | 43% and 57% | 25 | 27% |

("Score" is the exchange's word: contracts resting, each discounted for
every tick it stands away from the best price. A side's pool is split in
proportion to it.)

**What a small order would be paid, by the formula.** If those books stayed
as they were for the whole six hours, 100 contracts resting on each side of
each of the 207 games would be paid $298 out of $2,549 in pools, on about
$17,800 of money resting. That is $1.44 a game on $86, or 1.7% in six
hours. By programme: ITF $1.62 a game, doubles $1.89, UTR $2.15, darts
$1.24, main tours $0.87, e-sports $0.23.

That number is the published formula applied to one moment. It is not money
anyone has been paid, and section 6 lists what could make it wrong.

**Almost nothing trades before a game.**

| Programme | Median contracts traded so far | Average | Markets with 100 or more |
|---|---:|---:|---:|
| ITF | 1 | 76 | 15% |
| UTR | 0 | 1 | 0% |
| Darts | 0 | 14 | 4% |
| Doubles | 2 | 624 | 6% |
| E-sports | 55 | 2,340 | 41% |
| Main tours | 1,466 | 4,937 | 88% |

In lower-tour tennis the exchange is paying $12 a match to have orders
resting, and in the median match one contract changes hands before it
starts. An order resting there is seldom traded against at all.

## 4. What a resting order risks

*Also a look, not a test: the 118,339 settled games of docs/06, section 10.*

An order that is traded against has bought just before the price fell, or
sold just before it rose. From the stored quotes: take a bid resting at the
best bid 60 minutes before the start, and call it run over if, 5 minutes
before the start, that side could be bought at or below that price.

| Family | Bids | Run over | What a run-over bid made, held to settlement | Cost for each contract quoted |
|---|---:|---:|---:|---:|
| All | 225,214 | 17.4% | −2.6¢ | 0.45¢ |
| Tennis, lower tours | 59,384 | 13.6% | −0.9¢ | 0.12¢ |
| Tennis, main tours | 30,266 | 19.9% | −2.0¢ | 0.39¢ |
| US leagues | 23,390 | 18.9% | −1.8¢ | 0.34¢ |
| E-sports | 18,486 | 25.9% | −3.2¢ | 0.83¢ |
| Table tennis | 81,660 | 16.7% | −3.9¢ | 0.65¢ |

Read against section 3: 100 contracts a side in a lower-tour tennis match
would lose about 100 × 2 × 0.12¢ = 24¢ in its last hour to being run over,
against a reward by the formula of $1.62. In e-sports and table tennis the
same sum comes out the other way round.

This is rough in three ways. It sees one hour, not six. It counts a bid as
run over only if the whole market moved through it, and misses a single
large seller. And it assumes the order is always filled when run over,
though the books say hardly anybody trades. The paper test below measures
this properly.

## 5. The paper test, fixed before its data exist

**R1.** A paper account rests small orders on both sides of every game in
the programmes of section 2, through the six hours before its start. It is
paid what the published formula says, and it is traded against whenever
the real order book says an order at its price could have been. It runs on
GitHub from 11 November and stops by itself on 18 November
(`.github/workflows/us-rewards.yml`, `kht us-rewards`,
`src/kht/trading/us_rewards.py`). It places no orders and uses no key.

The rules, which are also the code, and which do not change while it runs:

1. **Which games.** Every open two-way market on who wins a game (the
   exchange's product code `aec`) that the public schedule puts in an
   active "day-of" liquidity programme with "moneyline" or "ml" in its
   name. A game is followed from six hours before its recorded start, or
   from when the recorder first sees it, until ten minutes before the start.
2. **Readings.** Each game's order book is read about every two minutes,
   less often if that would take more than five requests a second. Two
   readings more than 15 minutes apart are not joined up, and that time
   counts for nothing.
3. **Where the orders rest.** On each side, at the first price, counting
   from the best, by which other people's orders add up to 20 contracts.
   (A tenth of a contract at the best price is common and is not a price
   anybody stands behind.) If that price is more than five ticks from the
   best on either side, or the two prices are more than 10¢ apart, nothing
   rests. The orders move to the new such prices at every reading.
4. **Size.** 100 contracts on each side is the size that is judged. 10, 25,
   50, 250, 500 and 1,000 are followed alongside as description.
5. **Reward.** By the published formula, with our order in the book. Each
   second, a side that reaches the target size (and, where the programme
   has a maximum spread, a book that passes it) is worth the pool ÷ 21,600
   seconds ÷ 2 sides, and we get our share of that side's score. The
   exchange says it pays nothing under $1 and reports earnings by market
   and date, so **a reward for one market on one US date that comes to less
   than $1 counts as nothing.**
6. **Being traded against.** The exchange publishes no trades, but each
   book carries the running totals of contracts and dollars traded, the
   last trade, and the day's lowest and highest trade. Between two
   readings: if contracts traded, and their average price, the last trade
   or a new low was at or below our bid, the bid is filled for as many
   contracts as traded, up to what is left of its 100. Likewise the offer,
   with the high. If the other side's orders now rest at our price or
   through it, we are filled for their size (for the larger of the two
   amounts where both happen). This puts us first in line
   and sends all of the trading through us, which is the unkind assumption
   if being traded against is bad news. A side is filled at most 100
   contracts in a game, and **a side that was filled whole earns no reward
   in that game.**
7. **What a fill is worth.** Held to settlement, with no fee, since a
   resting order pays none. A game that was called off (settled at a price
   strictly between 0 and 1) pays what it settled at and **earns no
   reward**, as the exchange's rules say.
8. **Whose pool.** Only programmes where the market on who wins is the
   programme's only market in its game are judged. Table tennis is
   recorded with its pool split in three, which is an assumption, and is
   reported apart.

**Two accounts are judged**, both named now so that neither can be chosen
later.

- **R1-all**: every programme that rule 8 allows.
- **R1-thin**: only the programmes in which, in the one look of section 3,
  100 contracts held a tenth or more of a side's score: ITF, UTR, doubles,
  darts and beach volleyball. In the main tennis tours and in e-sports the
  same order held a fiftieth, so there the reward is next to nothing while
  the trading against it is not.

**The judge.** A game is judged once it started more than 12 hours ago and
its settlement is on file. For each account, when at least 2,000 of its
games on at least 5 US dates have been judged:

> The account passes if the mean net result per game (reward after the $1
> minimum, plus fills at settlement) is above zero with z ≥ 3, where each
> combination of date and programme counts as one observation.

Reported whatever happens: the reward before the minimum; the fills valued
at the middle of the book just before the orders were pulled, which is
less noisy than the result of the game; every order size; every programme;
every date; and table tennis.

A 13-minute trial of the recorder ran on 11 November from 09:33 UTC to
check that it works. Its output was read for that purpose: the counts, the
layout of the files, and that each of its 18 recorded fills matched the
readings of the book around it. It is not part of the test. One thing was
decided after it had been seen, and is said here for that reason: the
second account, R1-thin. Its list of programmes comes from the shares in
section 3, but the trial had also shown eight of its 18 fills in e-sports
and three in the main tennis tours.

## 6. What the paper test cannot settle

- **Whether the exchange pays what its formula says.** Everything above
  takes the published rules at their word. The $1 minimum may apply to
  something other than a market and a date. A second may be divided between
  the two sides differently. Only an account's earnings record can say.
- **What others do when a new order appears.** The accounts already there
  may add size or step in front. The paper account's share assumes they
  carry on as they were.
- **The line.** A real order joins the back of the line at its price. The
  paper order is treated as first, which overstates how often it is
  filled. If fills are bad news that is the safe direction; if they are
  good news it is not.
- **Speed.** The paper account moves its orders every two minutes. A real
  one would follow the book within a second, and would need to.
- **How long this lasts.** These programmes are weeks old. The exchange
  changes pools, targets and spreads between periods, and other people will
  arrive.

## 7. What a pass would be worth, and what it would not

A pass would say: by the exchange's own published rules, and with fills
counted unkindly, small orders resting before these games come out ahead,
and by about this much a game. It would give a number to hold a real
account to.

It would not say that money has been made. The next step after a pass is
the owner's decision and needs their account: the same orders for real, in
a few dozen games for a few days, at a size of a few hundred dollars, and
then the earnings record set beside what this paper account says those
same games should have paid. No order has been placed and none will be
without instruction.

## 8. What the runs show so far

*Dated notes are added here as runs come in. The rules of section 5 are not
touched.*

**11 November, 09:49 UTC.** The first run started, after the rules above
and the code were committed (commit `c73d2a6`, 09:49 UTC; the workflow in
`5f23e6c`). Each run lasts five hours and starts the next. Nothing to
report yet: a game is judged only once it started more than 12 hours ago
and has settled.
