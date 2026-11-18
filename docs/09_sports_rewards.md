# 09 — Rewards in sports games, and a paper test fixed in advance

*11 November 2026. A lead with a test attached. Nothing here has been
tested with money, and nobody has been paid anything. Sections 1 to 4 are
what was looked at; section 5 fixes a test before any of its data exist;
results will be added from section 8 on.*

**Read section 9 first.** The exchange has filed amended rules that take
effect on 18 November 2026. Under them it may cap a reward at a share of
what the account itself trades. Where it does, resting orders that are not
traded against earn nothing, and this lead ends.

## 1. What this adds to docs/08

`docs/08_rewards.md` found that Polymarket US pays people for leaving
orders resting, looked at the programmes outside sports, and could not tell
whether a pool was for a whole programme or for each event in it. That one
question decided whether the idea was worth cents or dollars.

In sports it has an answer. Seven-eighths of the exchange is sports, nearly
all of the reward money is there, and in sports a pool can only belong to
one game, because its periods are counted from that game's start:

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
And it is evidence about sports only: for the daily programmes outside
sports the question is still open (`docs/08_rewards.md`, section 10).

There is also a check that does not depend on the wording. If each game
has its own pool, the accounts already resting orders should be risking
about as much as the pool is worth, no more. Before a lower-tour tennis
match they rest several hundred contracts a side for a $12 pool, and
section 4 puts what being run over costs at that size at a few dollars. Those are the
same order of size. If the $12 were shared by every match in the
programme, nobody would rest that much for it.

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

### The same over all six hours, fixed before its data are read

*Written on 11 November at 09:55 UTC, before the download below was
started.* The paper test will take a week to see a few thousand games. The
exchange's stored prices can show the costly kind of fill on tens of
thousands of past games now, so that is measured too
(`scripts/rest_history.py`).

- **Games.** Every settled market on who wins in the leagues of the five
  programmes that section 5 calls thin: ITF (four league codes), UTR,
  doubles, darts (the Modus league) and beach volleyball. 52,103 games.
- **Data.** The stored best price on each side, minute by minute, for the
  six hours before the recorded start. There are no sizes and no trades in
  it.
- **The orders.** As the paper account's, as far as this data allows: 100
  contracts at the best bid and 100 at the best offer, moved every two
  minutes, from six hours to ten minutes before the start. They rest only
  in a book with real prices on both sides (the filter of docs/06,
  section 7) that is at most 10¢ wide.
- **A fill.** If, at the next reading, the offer side has come down to our
  bid or below it, the bid is filled at its price. Likewise the offer. Each
  side is filled once at most in a game. If the next reading is not a real
  two-sided book, nothing is counted for that step, and how often that
  happens is reported.
- **Worth.** Held to settlement, no fee.

What is reported: for each programme, the share of games with a fill and
the average result of the fills per game, in dollars, with a z by day; the
same valued at the middle of the book when the orders were pulled; by
month; and when in the six hours the fills came.

What it is for: the one look of section 3 put the reward by the formula at
$1.62 a game in ITF, $2.15 in UTR, $1.89 in doubles, $1.24 in darts.
**If being run over costs more than that per game, the lead is dead in
that programme whatever the paper test finds. If it costs under a dollar a
game in ITF, the lead stands for now.** My expectation, from the one-hour
look, is well under a dollar.

What it cannot show: fills from a single large order that did not move the
whole market, which the paper test does see; and the good fills, where
somebody simply takes the price and the market stays where it was.

### A second guess, from what is already resting

*Written at 10:04 UTC, while the download was running and before anything
from it had been read.* The accounts already resting orders before these
matches have every reason to size them well, and their sizes say what they
think resting costs.

Take two accounts sharing one side's half of a $12 pool, $6. Each gains
less from every contract it adds, because its share grows more slowly the
more it already has, while each contract costs the same to rest. Each stops
adding where the two meet. For two alike accounts that point is a combined
size of $6 ÷ (2 × the cost of resting one contract). The median score on a
side was 577. That puts the cost of resting one contract on one side for
the six hours at about half a cent. With three accounts the same sum gives
0.7¢.

So this guess says 100 contracts a side cost $1.00 to $1.40 a game to rest
in ITF, and that a newcomer's 100 contracts, paid $1.62 by the formula,
would clear something between nothing and 50¢ a game. The one-hour look
above says the cost is well under a dollar. They cannot both be right, and
the six-hour measure can contradict either.

### What the six-hour measure found

*Run on 11 November at 10:58 UTC, on all 52,103 games, as fixed above
(`reports/research/rest_history_output.txt`, `rh_by_programme.csv`,
`rh_by_month.csv`).*

Of the 52,103 games, 49,592 had stored prices and 34,125 had a book that
could be rested in at some reading. In those the orders rested for 3.2
hours a game on average, not six: for the rest of the time the stored
prices do not show a real two-sided book 10¢ wide or less.

| Programme | Games rested in | Hours rested, a game | Games with a fill | What the fills made, a game | z by day | The same at the last middle price | Reward by the formula, a game (section 3) |
|---|---:|---:|---:|---:|---:|---:|---:|
| ITF | 29,647 | 3.3 | 15.5% | −$0.58 | −6.1 | −$0.68 | $1.62 |
| UTR | 2,393 | 3.2 | 11.8% | −$0.69 | −2.9 | −$0.52 | $2.15 |
| Doubles | 915 | 3.2 | 20.7% | −$2.48 | −4.2 | −$1.50 | $1.89 |
| Darts | 1,063 | 3.2 | 25.5% | −$1.21 | −2.5 | −$1.76 | $1.24 |
| Beach volleyball | 107 | 1.6 | 1.9% | −$1.32 | −1.4 | −$0.46 | $1.63 |

**By the bars fixed beforehand:**

- **ITF: the lead stands.** Being run over cost 58¢ a game, under the
  dollar that was the bar.
- **UTR: stands.** 69¢ a game against $2.15.
- **Doubles: dead.** $2.48 a game against a reward of $1.89.
- **Darts: dead in practice.** By the letter it survives by three cents
  ($1.21 against $1.24). On the steadier measure, the last middle price,
  it costs $1.76. I treat it as dead.
- **Beach volleyball: cannot be said.** Two fills in 107 games.

**The fair comparison is by the hour, and it is tighter than the table
looks.** The reward in the last column is for six hours of resting. The
cost is for the 3.2 hours that could be measured. Per hour of 100 contracts
resting on each side:

| Programme | Being run over costs, an hour | The formula pays, an hour |
|---|---:|---:|
| ITF | 18¢ held to settlement, 21¢ at the last middle | 27¢ |
| ITF, since its programme began on 18 October (4,863 games) | 10¢ and 18¢ | 27¢ |
| UTR | 22¢ and 16¢ | 36¢, when the book passes its maximum spread, which half do |
| Doubles | 77¢ and 47¢ | 32¢ |
| Darts | 38¢ and 55¢ | 21¢ |

So in lower-tour tennis the formula pays about one and a half times what
being run over costs. That is a margin, and a thin one: about 6¢ to 9¢ an
hour for each game, or 35¢ to 50¢ over a whole six hours, for 100 contracts
a side. It is not the 1.7% in six hours that section 3's one look seemed
to offer before any cost was counted.

**Which guess was right.** Both, in a way that is worth seeing. The first
said "well under a dollar a game", and 58¢ is. But only because the orders
could rest for half of the six hours. At 18¢ to 21¢ an hour, a full six
hours would cost $1.05 to $1.22, which is what the second guess said
($1.00 to $1.40), and the second guess came only from the sizes other
people rest. That agreement matters more than either number. It says the
accounts already there size their orders as if each game's pool were
really theirs to share, and as if being run over cost what this measure
says it costs. The reading of the rules in section 1 and the measure of
the risk here were made separately and they fit.

**Also seen, and not part of the measure.** A fill cost about the same
whenever it came, $3 to $4.50 for 100 contracts at the last middle price.
But a third of the fills came in the last hour before the start. Pulling
the orders an hour before the game, not ten minutes, would have saved about
a third of the cost and given up a seventh of the time. The paper test's rules
are fixed and are not changed for this.

**What changes.**

- The settings of the order system (`config/us_quoter.json`, the rehearsal
  of `docs/10_us_quoter.md`) now name ITF and UTR only. Doubles, darts and
  beach volleyball are out.
- The paper test is not touched: R1-all and R1-thin are judged as they were
  named. A third account is named now, at 11:00 UTC on 11 November, before
  any reading of the paper test has been looked at (its first run has not
  ended): **R1-core, ITF and UTR only**, with the same judge. It is what
  this history says the test should have been.

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

**Three accounts are judged**, each named before any reading of the test
had been looked at, so that none can be chosen later.

- **R1-all**: every programme that rule 8 allows.
- **R1-thin**: only the programmes in which, in the one look of section 3,
  100 contracts held a tenth or more of a side's score: ITF, UTR, doubles,
  darts and beach volleyball. In the main tennis tours and in e-sports the
  same order held a fiftieth, so there the reward is next to nothing while
  the trading against it is not.
- **R1-core**, added at 11:00 UTC on 11 November, after the history of
  section 4 had been read and before any reading of this test had been:
  ITF and UTR only. Section 4 found that in doubles and darts being run
  over costs more than the formula pays.

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

**11 November, 14:48 UTC.** The first run ended as it should: 299 minutes,
150 rounds of readings, 49,788 order books read, no errors. It followed 594
games, 518 of which had a price to rest at, and found 564 moments in 213
games at which a resting order would have been traded against. No game is
old enough to judge, and five hours say nothing. The second run started by
itself at 14:48 UTC, and with it the rehearsal of the order system
(`docs/10_us_quoter.md`). The scoring script was run on the real output for
the first time and works.

**11 November, 18:33 UTC.** Nothing new to judge. The second run is still
going and commits what it recorded when it ends, at about 19:50 UTC, so
the scoring script still sees only the first five hours, and no game in
them started 12 hours ago. The next run is already queued behind it. The
reward schedule carries no new field: no cap and no minimum volume has
been published. From its next run the same job also records the last
minutes of crypto markets for another test (`docs/11_crypto_us.md`),
beside this one and without touching it. To keep that recording whole, a
run that would have ended between 21:35 and 22:03 UTC now ends at 21:33.
That changes when a run of this test ends and nothing it measures.

**11 November, 23:02 UTC. Two hours of recording were lost.** The second
run ended as it should at 19:47 UTC: 298 minutes, 448 games followed, 545
moments at which a resting order would have been traded against. The run
after it lost its machine at 21:40 UTC. GitHub ended the job in the middle
of a step and nothing it had recorded was saved, because a run saved only
at its end. It also could not start its successor, so nothing was
recording from 21:40 until I started a run by hand at 22:28. The test has
a hole from 19:47 to 22:35 UTC. Games whose six hours fall partly in it
were watched for less time than they should have been, so they are
counted with less reward and with fewer fills than a whole watch would
give. Which way that tilts the result is not known. When the games are
judged, the result will also be given without the games that touch the
hole.

Three things were changed so that this costs an hour at most next time:
the job saves what it has recorded once an hour
(`scripts/ci_save_state.sh`); a second job, `us-rewards-watchdog`, is
set to look every quarter of an hour and starts a run if none is going
(by 23:19 UTC GitHub had started it only when asked by hand, not yet on
its schedule); and the crypto recorder beside this test writes to disk as
soon as its markets have ended. From 23:21 UTC a run that ends badly
after more than ten minutes also starts its successor at once, from a
fresh machine, without waiting for a schedule. On the way I pushed a version of the job file that did not
parse, and for about a minute GitHub would not start it. The run of 22:28
was stopped on purpose at 22:35, before it had written anything, so that
the next one would use the new file. That one is going. Rules 1 to 8 of
section 5 and the program that applies them are untouched.

From the next run the job carries one more recorder for the crypto tests
(`docs/11_crypto_us.md`, section 12). It reads other markets and shares
only the machine with this test.

**12 November, 09:04 UTC. The first games are old enough to count, and
one day is not a test.** Four runs are in: 19.9 hours of recording, 1,166
games followed. Since the restart at 22:35 UTC the job has not missed:
two full runs of 298 minutes with no errors, a save every hour, and the
next run going since 08:33. The watchdog was started by GitHub's schedule
once, at 03:18 UTC, nearly five hours after it was added. It asks to be
started every quarter of an hour.

383 games started more than 12 hours ago and have settled, all on one US
date, 11 November. The judge asks for 2,000 games on five dates, so
nothing is judged. For orders of 100 contracts a side:

| Account | Games | Reward by the formula, after the $1 minimum | What the fills made, held to the result | Net | A game |
|---|---:|---:|---:|---:|---:|
| R1-all | 383 | $204.62 | −$540.27 | −$335.65 | −$0.88 |
| R1-thin | 272 | $180.32 | −$412.89 | −$232.56 | −$0.86 |
| R1-core | 207 | $145.70 | −$369.26 | −$223.56 | −$1.08 |

So on the first day all three are behind. Half the games had an order
traded against (192 of 383 in R1-all, 14,872 contracts). Two figures
describe what that cost, and they are far apart. Valued where the price
stood just before the start, the fills of R1-all cost $120, which is less
than the reward and about what the history of section 4 led one to
expect. Held to the result they cost $540. The difference is the results
of 192 matches going one way more than the other, and a day cannot say
whether that is luck or the thing the test is looking for. The rule
judges by the result, and it needs the five dates. Lower-tour tennis,
the programme the lead rests on, was the worst of the day: 162 games,
$77 of reward, $355 lost on fills.

The rehearsal of the order system ran 17.7 hours with no errors: 81
markets rested in, $39 of reward after the minimum, 97 fills, 22
positions settled for −$269, 13 still open. It tells the same story with
fewer games.

No reward cap and no minimum volume has been published.

**13 November, 09:09 UTC. Two dates, and both behind.** Eight runs are in,
39.8 hours of recording, 1,968 games followed. The job has not missed
since the restart: every run its full 298 minutes, no errors, a save
every hour. 909 games are old enough to count and settled, on two US
dates. The judge asks for 2,000 on five, so nothing is judged.

| Account | Games | Reward by the formula, after the $1 minimum | What the fills made, held to the result | Net | A game |
|---|---:|---:|---:|---:|---:|
| R1-all | 909 | $546.71 | −$1,314.02 | −$767.30 | −$0.84 |
| R1-thin | 639 | $471.99 | −$1,028.05 | −$556.05 | −$0.87 |
| R1-core | 505 | $364.67 | −$709.99 | −$345.32 | −$0.68 |

Both days are behind taken alone: 11 November by $641 on 495 games,
12 November by $126 on 414. Valued at the price just before the start,
the fills of R1-all cost $351, less than the reward. Held to the result
they cost $1,314. That gap was put down to one day's luck yesterday. It
has now come twice and in the same direction, and most of it is in one
programme, the ITF tennis tour: 377 games, $194 of reward, $116 lost on
fills at the price before the start and $722 at the result. An order there
that gets filled seems to be filled by somebody who knows more about the
match than the last price shows. Two days do not prove that, and the
rule waits for five. But if it holds, the history of section 4 measured
the wrong cost, since it could only see prices before the start.

The rehearsal of the order system, which chooses 20 games at a time by
its own limits, is the other way round so far: 41.6 hours, 207 markets,
$96 of reward after the minimum, 228 fills, 65 positions settled for
−$46, 14 still open. No errors.

No reward cap and no minimum volume has been published.

**14 November, 09:08 UTC. Three dates, all three behind.** Thirteen runs
are in, 64.7 hours of recording with no gap since the restart, 2,626
games followed. 1,340 games are old enough to count and settled, on three
US dates. The judge asks for 2,000 on five, so nothing is judged.

| Account | Games | Reward by the formula, after the $1 minimum | What the fills made, held to the result | The same at the price before the start | Net | A game |
|---|---:|---:|---:|---:|---:|---:|
| R1-all | 1,340 | $768.06 | −$1,795.00 | −$432.50 | −$1,026.94 | −$0.77 |
| R1-thin | 924 | $647.99 | −$1,394.97 | −$302.88 | −$746.98 | −$0.81 |
| R1-core | 718 | $499.12 | −$1,067.88 | −$229.63 | −$568.76 | −$0.79 |

By date, R1-all: 11 November −$641 on 495 games, 12 November −$130 on
522, 13 November −$256 on 323. The ITF tour alone: 499 games, $231 of
reward, $156 lost on fills at the price before the start and $1,053 at
the result. The other lower-tour programme, UTR, is ahead by $252 on 219
games.

So the gap between the two ways of valuing a fill has now come on three
dates running, and it is the ITF tour each time. That is no longer one
day's luck. The orders that get filled there lose about seven times what
the price before the start says they should. The judge still wants its
five dates and 2,000 games, and will have them in about two days. To pass
it would need the days still to come to undo these three.

The rehearsal of the order system: 65.5 hours, 299 markets, $123 of
reward after the minimum, 342 fills, 98 positions settled for −$140, 11
still open. Net −$16. No errors.

No reward cap and no minimum volume has been published.

**16 November, 09:22 UTC. The first account is judged, and it fails.**
23 runs are in, 114.4 hours of recording with no gap since the restart,
4,645 games followed. 2,295 games of R1-all are old enough to count and
settled, on five US dates. That is what the judge asked for.

| Account | Games | Reward by the formula, after the $1 minimum | What the fills made, held to the result | The same at the price before the start | Net | A game | z |
|---|---:|---:|---:|---:|---:|---:|---:|
| R1-all | 2,295 | $1,711.24 | −$3,482.96 | −$811.79 | −$1,771.72 | −$0.77 | −1.47 |
| R1-thin | 1,629 | $1,530.34 | −$3,577.39 | −$599.58 | −$2,047.05 | −$1.26 | −2.25 |
| R1-core | 1,315 | $1,313.19 | −$3,217.89 | −$505.93 | −$1,904.70 | −$1.45 | −2.23 |

The rule asks for a mean above zero with z of 3 or more. R1-all's mean is
below zero, so **R1-all fails**. R1-thin and R1-core have fewer than the
2,000 games they need and are not judged. Both are further behind than
R1-all. R1-thin should have its 2,000 by the last check-in on
18 November; R1-core probably will not.

By date, R1-all: 11 November −$641 on 495 games, 12 November −$130 on
523, 13 November −$248 on 370, 14 November +$445 on 348, 15 November
−$1,198 on 559. One date ahead and four behind. The worst is the last:
15 November paid the most reward of any date, $677, and its fills lost
$1,875.

The ITF tour alone: 984 games, $937 of reward, $408 lost on fills at the
price before the start and $3,020 at the result. Net −$2,083, which is
more than the whole loss: every other programme together is ahead by
$311. UTR is ahead by $178 on 331 games. The main tennis tours are ahead
by $455 on 210 games, but their reward was $4. The rest is how 210
results fell.

What the five dates say:

- **The reward is there, by the formula.** $1,711 on 2,295 games, about
  75¢ a game. Nobody was paid it, and only a real account can show
  whether the exchange pays what its formula says.
- **The cost is not the one section 4 measured.** Valued at the price
  before the start, the fills cost $812, about half the reward, which is
  what the history said. Held to the result they cost $3,483. The $2,671
  between the two is fills that went on losing after the start, and
  $2,612 of it is the ITF tour. In a fair market that difference averages
  nothing. Here it has had the same sign on four dates of five.
- **How sure is that?** For R1-all, z is −1.47: a loss, but not one so
  far below zero that luck is ruled out. For the two accounts that are
  mostly ITF it is about −2.2. The test was built to show a profit beyond
  doubt, and it shows a loss.
- **Closing each fill before the start would not rescue it.** With every
  fill closed at the middle of the book, at no cost at all, R1-all would
  be $899 ahead. Closing costs something: at half a cent a contract the
  112,049 contracts cost $560, and at a cent $1,120. This was not tested,
  and it is no reason to hope.

Without the games that touch the hole of 11 November (217 games whose six
hours before the start overlap 19:47 to 22:35 UTC that day), as promised
in the note of 11 November: R1-all has 2,155 games and −$1,588.59, a
game −$0.74, z −1.30. R1-thin 1,523 games and −$1,902.98. R1-core 1,224
games and −$1,870.46. The verdict does not turn on the hole.

Under a cap on rewards, described only: the same orders would have been
paid $769 with a cap of 100% of what they traded, $672 at 50% and $405 at
10%, against $1,711 with none.

The rehearsal of the order system: 113.4 hours, 533 markets, $369 of
reward after the minimum, 490 fills (10,413 contracts), 151 positions
settled for −$505, 9 still open. Net −$137. It was level two days ago and
has gone the way of the test.

No reward cap and no minimum volume has been published, as far as the
public schedule shows. Read at 09:19 UTC today it has 72,386 time periods
on 45,113 markets, with the same ten fields as on 11 November, and none
of them is a cap or a volume requirement. The filed rules ask for 48
hours' notice, and 18 November begins at 05:00 UTC, so that notice would
be due by now. I could not read the exchange's own rewards page today.

The two runs of 14 November with 1,137 and 2,007 fills, against about 350
to 950 in every other full run, are not a fault. It was a Saturday with a UFC
card (1,171 of the second run's fills), a full evening of ice hockey and
the final of the League of Legends world championship.

*Still to check, once a run has spanned it:* the exchange restarts each
market's running totals of trading once a day, at 17:00 Eastern (22:00
UTC). Rule 6 reads fills off those totals. If the restart itself shows up
as a burst of fills at that minute, they are not real fills, and that would
be a fault in the measuring to be fixed and dated here. The first run
ended before that hour. *12 November, 09:04 UTC:* still open. The run that
would have spanned 22:00 UTC on 11 November was the one lost with its
machine. Tonight's is the first that will.

*16 November, 09:22 UTC: checked. The premise was wrong, and something
else was found.* The totals are not restarted each day. Public books read
today carry totals and first, lowest and highest trade times that go back
days: a tennis market that opened on 12 November showed 23,682 contracts
traded and an opening trade of 12 November. So there is no daily restart
for rule 6 to trip over.

What the fills do show is a limit of the measuring. On each of the four
evenings recorded so far (12 to 15 November), from about 22:08 to 22:30
UTC, the public book stands still. Almost no fill is recorded in those
minutes: 18 by a trade over the four evenings, where the 68 minutes
before them have 882. The first reading after 22:30 UTC then
shows everything that traded meanwhile at once: 154 fills out of 4.4
million contracts of trading. Three quarters of them carry no trade time
later than the reading before, against 7% at other hours, which is what
catching up looks like. So trading goes on and the public book does not
show it, and the paper orders rest blind through that stretch at the
prices of the last reading before it. A real order would rest through it
too, but whoever placed it would presumably see the market by another
route.

The judged account barely feels it. 81 of its 4,064 fills, 2,405 of its
112,049 contracts, come from readings between 22:08 and 22:33 UTC, and
they made $86 at the result. With every fill recorded in those minutes
left out, R1-all's net goes from −$1,771.72 to −$1,695.95 and its z from
−1.47 to −1.39; R1-thin from −$2,047.05 to −$1,997.79; R1-core from
−$1,904.70 to −$1,846.82. No verdict changes. The judged figures stay as
the rule makes them, and this stands beside them.

25 of those fills are of one or two contracts at a price far from the
book, for example one contract at 98.5¢ where the offer stood at 81¢.
17 of them are on the next day's ITF games on 14 November. I do not know
what they are. They weigh nothing in the account.

**18 November, 09:14 UTC. The test is over. All three accounts are judged,
and all three fail.** The recorder stopped by itself at 04:10 UTC today,
as built. It made 32 runs and 159.2 hours of recording, with no gap after
the restart of 11 November and no errors, and followed 6,291 games. 3,532
games of R1-all are old enough to count and settled, on seven US dates,
11 to 17 November. Another 261 from the last evening started less than
twelve hours before this was scored, and 57 have no settlement on file.
They cannot change a verdict: their reward so far comes to $222.

| Account | Games | Reward by the formula, after the $1 minimum | What the fills made, held to the result | The same at the price before the start | Net | A game | z | By the rule |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| R1-all | 3,532 | $3,008.51 | −$5,183.57 | −$1,334.62 | −$2,175.05 | −$0.62 | −1.37 | fails |
| R1-thin | 2,493 | $2,714.09 | −$4,616.40 | −$964.56 | −$1,902.31 | −$0.76 | −1.33 | fails |
| R1-core | 2,112 | $2,450.27 | −$4,120.98 | −$814.00 | −$1,670.71 | −$0.79 | −1.16 | fails |

The rule asked for a mean above zero with z of 3 or more, on at least
2,000 games and five dates. All three accounts have the games and the
dates, and all three means are below zero.

By date, R1-all:

| US date | Games | Reward after the minimum | Fills, held to the result | Net |
|---|---:|---:|---:|---:|
| 11 November | 495 | $259.44 | −$900.55 | −$641.11 |
| 12 November | 523 | $340.62 | −$470.59 | −$129.97 |
| 13 November | 370 | $181.27 | −$429.24 | −$247.97 |
| 14 November | 348 | $252.81 | +$192.07 | +$444.88 |
| 15 November | 691 | $798.11 | −$2,344.93 | −$1,546.82 |
| 16 November | 685 | $810.70 | −$763.14 | +$47.57 |
| 17 November | 420 | $365.58 | −$467.20 | −$101.62 |

Five dates behind and two ahead. (15 November had 559 games in the note
of 16 November. The rest of its games have settled since.)

By programme, R1-all:

| Programme | Games | Reward after the minimum | Fills, held to the result | The same at the price before the start | Net |
|---|---:|---:|---:|---:|---:|
| ITF tennis | 1,626 | $1,864.83 | −$3,893.99 | −$639.47 | −$2,029.16 |
| UTR tennis | 486 | $585.44 | −$226.99 | −$174.54 | +$358.45 |
| ATP and WTA | 370 | $13.92 | +$203.71 | +$45.85 | +$217.62 |
| E-sports | 361 | $214.22 | −$430.44 | −$433.22 | −$216.21 |
| Darts | 154 | $81.16 | −$161.01 | −$53.62 | −$79.86 |
| Table tennis | 146 | $63.74 | −$288.23 | −$7.01 | −$224.49 |
| Tennis doubles | 124 | $94.91 | −$254.92 | −$41.53 | −$160.01 |
| 3x3 basketball | 108 | $2.55 | −$103.41 | −$26.88 | −$100.86 |
| Astra cup, women | 103 | $87.76 | −$79.50 | −$55.40 | +$8.26 |
| Ice hockey, UFC, League of Legends | 54 | $0.00 | +$51.19 | +$51.19 | +$51.19 |

What the week says:

- **The reward is there, by the formula.** $3,009 on 3,532 games, 85¢ a
  game. 1,438 of the games reached the $1 minimum.
- **The orders are traded against in most games.** 2,245 of the 3,532,
  for 178,001 contracts.
- **Valued before the start, the fills cost less than half the reward.**
  $1,335, which is what the history of section 4 led me to expect. Held
  to the result, as the rule fixed, they cost $5,184.
- **The difference is the ITF tour.** Of the $3,849 between the two
  valuations, $3,255 is ITF. There a filled order goes on to lose after
  the start, six times what the last price before the start says it
  should. ITF alone is −$2,029 of the −$2,175. All the other programmes
  together are $146 behind.
- **It is a loss, not a proven one.** With z between −1.2 and −1.4, luck
  is not ruled out. The test was built to show a profit beyond doubt. It
  shows none.

The same result three other ways, none of which changes a verdict:

| | R1-all | R1-thin | R1-core |
|---|---:|---:|---:|
| As judged | −$2,175.05 | −$1,902.31 | −$1,670.71 |
| Without the 217 games that touch the hole of 11 November, 19:47 to 22:35 UTC | −$1,991.92 on 3,392 games | −$1,758.24 on 2,387 | −$1,636.47 on 2,021 |
| Without the 256 fills recorded between 22:08 and 22:33 UTC, when the public book stands still | −$1,972.35 | −$1,762.67 | −$1,522.45 |
| Without both | −$1,789.22 | −$1,618.60 | −$1,488.21 |

Closing each fill before the start instead of holding it was never
tested, and the figures do not invite it. At the middle of the book and
at no cost R1-all would be $1,674 ahead. Closing 178,001 contracts at
half a cent each costs $890, and at a cent $1,780.

One programme did what the lead said it would: UTR, $585 of reward
against $227 lost on fills, $358 ahead on 486 games. It was named in
advance only as half of R1-core, not alone. Picking it out now is
choosing after the result, so it is a description and nothing more.

The rehearsal of the order system, which rests in at most 20 games at a
time and chooses them by its own limits: 157.3 hours, 759 markets, $570
of reward after the minimum, 663 fills (14,735 contracts), 208 positions
settled for −$485, 15 still open. Net +$85 so far. It was −$137 two days
ago. A week of it settles nothing either way.

**A cap.** Under a cap on rewards, described only, the same orders would
have been paid $1,394 with a cap of 100% of what they traded, $1,212 at
50% and $737 at 10%, against $3,009 with none. The amended rules are in
force from today. Read at 09:12 UTC, the public schedule has 85,245 time
periods on 51,530 markets with the same ten fields as on 11 November.
None is a cap or a minimum volume. So none has been published there. I
could not read the exchange's own rewards page.

**What this test does not show.**

- **No reward was paid to anyone.** The formula is taken at its word,
  with my reading of how a pool is split and of the $1 minimum. Only a
  real account's earnings record can check that.
- **No order was placed.** A fill is inferred from the book's running
  totals, read every two minutes, with our order put first in line. That
  is unkind where being filled is bad news. It is kind in a busy market,
  where it fills both sides and books the spread: the last row of the
  table above is that and nothing else.
- **The public book stands still for about twenty minutes each evening**
  (the note of 16 November above). The paper orders rest blind through it.
- **One week.** Seven dates, the last week before the rules changed.

**What I conclude.** Resting 100 contracts on each side of every game and
collecting the reward does not pay on paper, and I would not try it with
money. The reward is as large as the formula says. The cost is larger,
because in the one programme with the most games and the most reward,
somebody on the other side knows more about the match than the price
does.

*18 November, 15:30 UTC. A second reading.* The week's recordings were
gone through again the same afternoon (`docs/13_round_six.md`, section 2).
Three things there belong beside the result above. In ITF the trading
before a match says who wins, by about 4¢ a contract beyond the last
price. In a quarter of ITF games the listed start time was wrong, so that
orders meant to rest before the match rested through it, and those games
lost about 12¢ on every contract filled. And UTR taken alone was ahead on
six dates of seven, which a new test, R2, now asks again of new games.

## 9. The rules as filed, and a change on 18 November

*Found on 11 November at about 11:05 UTC, after everything above. It
matters more than anything above.*

The exchange files the terms of its programmes with its regulator, the
CFTC, and the filings are public. The one for this programme is the
"Amended Market Liquidity Incentive Program" (PMX-2026-70,
`cftc.gov/filings/orgrules/rules11032642173.pdf`), filed on 3 November
2026. It takes effect ten business days later, which is **18 November
2026**, and says itself that it then runs to 18 November 2027. Everything
above was built from the exchange's help pages. This is the rule text.

### What it confirms

- The scoring: snapshots once a second, the walk to the target size, the
  discount for each tick from the best price, each side normalised, the
  maximum-spread test on the book as a whole. As modelled.
- The $1 threshold: a reward under $1 for one participant, one contract and
  one time period is not paid. The paper test's rule (one market, one US
  date) is the same or stricter.
- Anyone in good standing is in, automatically.
- It names what the exchange will treat as gaming, and "placing quotes with
  no bona fide intent to trade" is on the list. The orders of thousands at
  1¢ and 99¢ are that. Orders at the market's own price are not.

### What it corrects in my reading

I had each second worth a fixed slice of the pool, lost if a side did not
qualify. The rule divides the pool differently: a participant's share is
its score summed over the whole period, divided by everybody's score
summed over the whole period. So where a programme has no maximum spread,
the whole pool is paid out among the seconds that do qualify. Where it has
one, the pool is first scaled by the share of seconds that pass.

Where both sides of a book always qualify the two readings are the same.
Where they do not, mine pays less. So the paper test's accounting errs on
the low side, by about a tenth in ITF. The scoring script now reports the
rule's own version beside the judged figure, and does not judge by it.

### What changes on 18 November

Two new parameters, each optional, set by the exchange for a contract and
a time period and published with the others:

> **Reward Cap Percentage**: "limits a Participant's reward for a Contract
> and Time Period to that percentage of the Participant's Executed Notional
> Volume in that Contract during that Time Period."

> **Minimum Volume Requirement**: a participant is paid only if its
> executed volume in the contract in that period is at least 0.01% of the
> contract's.

Rewards withheld under either are not passed to anyone else.

**Where the exchange sets a cap, an order that rests and is never traded
against earns nothing.** That is the whole of the idea in this document.
With a cap, the paper account would be paid only in the games where it was
filled, about 15% of them on the history of section 4. That is about 25¢ a
game of reward against 58¢ of cost from those same fills. It loses.

The filing's own illustration shows caps of between 10% and 100% of
executed volume on five example contracts, and no cap on the sixth.

### What is not known

Whether the exchange will set a cap on the tennis programmes, and at what
percentage. It must publish each contract's parameters at least 48 hours
before a time period, on its rewards page. On 11 November neither that
page nor the public schedule carried any such field: the schedule's time
periods have eleven fields, and none is a cap.

Why file it at all? Presumably because a great deal of what rests in these
books today is there to be paid and not to trade. The exchange has given
itself the tool to stop paying for that, and I expect it to use it.

### What was done about it

- **The recorder watches for it.** Every cycle `kht us-record` writes down
  every field the schedule carries (`state/us/schedule_fields.csv`) and
  says so at the foot of `state/us/STATUS.md` when one appears that was not
  there on 11 November.
- **The order system refuses it.** `kht us-quote` leaves alone any market
  whose time period carries a field that speaks of a cap or of volume.
- **The paper test runs to its end as fixed.** Its last games are on
  17 November, under the rules as they are now. What it measures stays
  true of those rules. Whether it says anything about the week after
  depends on what the exchange publishes.
- **The scoring also answers the question the new rules ask.** The paper
  account's fills are recorded, so what it traded in each game is known.
  Beside the judged figures the scoring now reports what the same orders
  would have been paid under a cap of 100%, 50% and 10% of that. These are
  described, not judged.

### What might still be paid under a cap, and why I would not build on it

Under a cap an account is paid, at most, in proportion to what it trades.
So an account that rests orders could also buy a few contracts in each
game to have something executed. With a cap of 100%, about $1.60 of
trading would release $1.60 of reward, and taking that much costs about a
dime in spread and fee. With a cap of 10% it would take $16 of trading and
cost about a dollar, which is the whole margin.

I would not build on this. The filing lists what the exchange will treat
as gaming, ends the list with "any other conduct that undermines market
integrity or the Program's objectives", and reserves to itself, finally,
whether a reward is paid at all. Trading for no reason but to release a
reward is what that sentence is for.

### What this does to the lead

It puts a date on it. Until 18 November the formula pays for resting
alone, and section 4 says that in lower-tour tennis it has paid about one
and a half times what resting costs. From 18 November that holds only
where no cap is set. A real test begun now would test the old rules and be
paid, if it is paid, about a week later. That is the owner's decision, and
it is a smaller decision than it looked this morning.
