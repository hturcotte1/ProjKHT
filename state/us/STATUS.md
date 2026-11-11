# Polymarket US recorder: 2026-11-11 22:22 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 9,512; showing any quote: 2,804
- order books recorded: 2,804, of which 2,266 have orders on both sides
- recorded markets with a twin on polymarket.com: 358; with a two-sided book there too: 290
- twins where the US price is the cheaper one by more than the US fee: 73 (14 on the "Yes" side, 59 on the "No" side)
- took 320 seconds; 0 errors

Taking every one of these at the best US price would cost $233,160, and the gaps add up to $2,154.13. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 91.0c | 79,746 | 5.2c / 6.3c | 1.9c | $1,532.67 | Prime Minister of Israel After the Next Election: Avigdor Lieberman |
| No | 99.0c | 62,076 | 0.4c / 0.5c | 0.4c | $252.00 | Best Chinese AI Company end of November?: Baidu |
| No | 99.0c | 25,973 | 0.3c / 0.4c | 0.5c | $131.41 | Fed Decision in December: 25 bps Decrease |
| No | 99.0c | 62,065 | 0.4c / 0.8c | 0.1c | $65.76 | Best Chinese AI Company end of November?: MiniMax |
| Yes | 23.0c | 112 | 39.0c / 41.0c | 14.3c | $16.08 | 2027 Louisiana Governor Election Winner: Democratic Party |
| Yes | 80.0c | 918 | 83.1c / 85.4c | 1.6c | $14.51 | Avengers: Doomsday Rotten Tomatoes Score?: 70+ |
| No | 91.0c | 1,038 | 6.0c / 7.0c | 1.2c | $12.68 | TIME Person of the Year 2026: Pope Leo XIV |
| No | 74.0c | 1,056 | 22.0c / 23.0c | 1.2c | $12.37 | TIME Person of the Year 2026: Zohran Mamdani |
| No | 94.0c | 251 | 0.5c / 0.6c | 4.9c | $12.20 | Best Chinese AI Company end of November?: DeepSeek |
| No | 81.0c | 247 | 11.0c / 13.0c | 4.5c | $11.19 | 2027 Minnesota Senate Special Election Winner: Republican Party |
| Yes | 61.0c | 45 | 86.0c / 89.0c | 22.7c | $10.28 | 2027 Minnesota Senate Special Election Winner: Democratic Party |
| No | 16.0c | 53 | 65.0c / 67.0c | 15.7c | $8.38 | US Birth Rate in 2026? (Per 1000 Women): 52.0+ |
| No | 23.9c | 2,152 | 73.0c / 74.0c | 0.4c | $8.01 | 2028 Presidential Election: Alaska Winner: Republican Party |
| Yes | 11.0c | 373 | 13.6c / 14.0c | 1.7c | $6.23 | Argentina Presidential Election Winner: Sergio Massa |
| Yes | 38.0c | 97 | 46.6c / 51.2c | 6.4c | $6.14 | Best Chinese AI Company end of November?: Xiaomi |
| No | 99.0c | 1,480 | 0.2c / 0.5c | 0.4c | $6.01 | Dancing With The Stars S35 Winner: Maura Higgins |
| Yes | 29.8c | 110 | 36.6c / 37.8c | 4.8c | $5.29 | 2028 Presidential Election: Georgia Winner: Republican Party |
| No | 99.0c | 848 | 0.1c / 0.3c | 0.6c | $5.14 | Argentina Presidential Election Winner: Esteban Bullrich |
| No | 99.0c | 596 | 0.1c / 0.2c | 0.7c | $4.21 | Argentina Presidential Election Winner: Facundo Manes |
| No | 71.1c | 155 | 24.0c / 25.0c | 1.9c | $3.01 | 2028 Presidential Election: New Hampshire Winner: Republican Party |
| No | 99.0c | 459 | 0.1c / 0.3c | 0.6c | $2.78 | Argentina Presidential Election Winner: Juan Grabois |
| No | 51.0c | 5.00 | 0.1c / 1.3c | 45.3c | $2.27 | OH-11 House Election Margin of Victory: Democrat 70-75% |
| No | 59.5c | 175 | 29.0c / 37.0c | 1.2c | $2.12 | 2028 Presidential Election: Wisconsin Winner: Republican Party |
| No | 99.0c | 343 | 0.1c / 0.3c | 0.6c | $2.08 | Argentina Presidential Election Winner: Juan Schiaretti |
| No | 2.0c | 54 | 92.2c / 94.2c | 3.6c | $1.94 | "GTA VI: The Album" First Week Sales?: 50k+ |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 177 | 161 | 177 | 0 of 9 |
| kpic_20261107 (daily) | $250 | 2,000 | 4c | 28 | 1 | 1 | 6 of 7 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 30 | 18 | 19 | 1 of 5 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 33 | 22 | 31 | 0 of 2 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 4 | 19 | 10 of 15 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 180 | 81 | 54 | 3 of 21 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 140 | 88 | 139 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 45 | 19 | 21 | 1 of 8 |
| finance_20261109 (daily_event) | $50 | 500 | none | 65 | 58 | 63 | 0 of 14 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 14 | 18 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 29 | 37 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 103 | 41 | 65 | 3 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 857 | 159 | 159 | 32 of 65 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 3 | 1 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 98 | 31 | 31 | 33 of 49 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 170 | 108 | 148 | 3 of 41 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 0 | 0 | 7 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 0 | 0 | 11 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 137 | 23 | 27 | 6 of 14 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 7 | 7 | 7 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 4 | 2 | 0 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 3,112 | 0 | 0 | 400 of 400 |
