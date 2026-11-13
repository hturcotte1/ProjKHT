# Polymarket US recorder: 2026-11-13 21:38 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 9,376; showing any quote: 2,693
- order books recorded: 2,693, of which 2,203 have orders on both sides
- recorded markets with a twin on polymarket.com: 363; with a two-sided book there too: 303
- twins where the US price is the cheaper one by more than the US fee: 128 (49 on the "Yes" side, 79 on the "No" side)
- took 370 seconds; 0 errors

Taking every one of these at the best US price would cost $67,749, and the gaps add up to $578.81. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 99.0c | 21,540 | 0.1c / 0.2c | 0.7c | $152.06 | Next CEO of NVIDIA?: Matt Garman |
| No | 99.0c | 20,324 | 0.1c / 0.2c | 0.7c | $143.47 | Next CEO of NVIDIA?: Nick Parker |
| No | 99.0c | 10,889 | 0.1c / 0.4c | 0.5c | $55.09 | Next CEO of NVIDIA?: Pat Gelsinger |
| No | 31.6c | 2,146 | 61.0c / 64.0c | 2.3c | $50.36 | 2028 Presidential Election: Ohio Winner: Republican Party |
| No | 91.0c | 1,704 | 6.7c / 6.9c | 1.3c | $22.53 | TIME Person of the Year 2026: Benjamin Netanyahu |
| No | 95.0c | 3,860 | 1.1c / 4.1c | 0.4c | $17.32 | TIME Person of the Year 2026: Jeremy Hansen |
| No | 23.9c | 2,921 | 73.0c / 74.0c | 0.4c | $10.87 | 2028 Presidential Election: Alaska Winner: Republican Party |
| Yes | 3.0c | 1,304 | 4.0c / 5.0c | 0.7c | $9.44 | Next CEO of NVIDIA?: Tim Cook |
| No | 99.0c | 2,661 | 0.4c / 0.6c | 0.3c | $8.14 | Dancing With The Stars S35 Winner: Maura Higgins |
| Yes | 4.0c | 102 | 11.0c / 14.0c | 6.6c | $6.78 | 2027 Minnesota Senate Special Election Winner: Republican Party |
| No | 95.0c | 148 | 0.4c / 0.5c | 4.0c | $6.00 | Best Chinese AI Company end of November?: DeepSeek |
| No | 99.0c | 845 | 0.2c / 0.3c | 0.6c | $5.12 | Argentina Presidential Election Winner: Esteban Bullrich |
| Yes | 29.8c | 109 | 36.3c / 36.4c | 4.5c | $4.90 | 2028 Presidential Election: Georgia Winner: Republican Party |
| No | 66.0c | 544 | 28.0c / 31.0c | 0.9c | $4.72 | 2027 Mississippi Governor Election Winner: Democratic Party |
| No | 16.0c | 27 | 65.0c / 67.0c | 15.7c | $4.32 | US Birth Rate in 2026? (Per 1000 Women): 52.0+ |
| No | 99.0c | 596 | 0.1c / 0.2c | 0.7c | $4.21 | Argentina Presidential Election Winner: Facundo Manes |
| Yes | 60.5c | 1,632 | 63.0c / 64.0c | 0.2c | $3.75 | 2028 Presidential Election: Arizona Winner: Democratic Party |
| No | 99.0c | 451 | 0.1c / 0.2c | 0.7c | $3.18 | Argentina Presidential Election Winner: Juan Grabois |
| Yes | 82.1c | 519 | 84.0c / 85.0c | 0.5c | $2.61 | 2028 Presidential Election: Minnesota Winner: Democratic Party |
| Yes | 55.1c | 69 | 61.0c / 67.0c | 3.5c | $2.44 | 2028 Presidential Election: Texas Winner: Republican Party |
| Yes | 61.0c | 42 | 69.0c / 70.0c | 5.7c | $2.39 | 2028 Presidential Election: Michigan Winner: Democratic Party |
| Yes | 23.0c | 23 | 35.0c / 39.0c | 10.3c | $2.33 | 2027 Louisiana Governor Election Winner: Democratic Party |
| No | 56.0c | 75 | 20.0c / 39.0c | 2.7c | $2.00 | US Birth Rate in 2026? (Per 1000 Women): 52.5+ |
| No | 50.0c | 52 | 43.0c / 44.0c | 3.6c | $1.90 | Argentina Presidential Election Winner: Javier Milei |
| No | 2.0c | 58 | 92.0c / 94.6c | 3.2c | $1.88 | "GTA VI: The Album" First Week Sales?: 50k+ |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 181 | 165 | 180 | 0 of 9 |
| kpic_20261107 (daily) | $250 | 2,000 | 4c | 20 | 0 | 0 | 5 of 5 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 30 | 19 | 22 | 0 of 5 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 33 | 4 | 30 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 9 | 9 | 9 | 0 of 3 |
| finance_nvda_nextceo_20261112 (daily_event) | $200 | 1,000 | none | 26 | 19 | 26 | 0 of 2 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 1 | 17 | 10 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 180 | 92 | 59 | 1 of 21 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 140 | 88 | 138 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 45 | 23 | 27 | 0 of 8 |
| finance_20261112 (daily_event) | $50 | 500 | none | 64 | 55 | 62 | 0 of 13 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 15 | 17 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 33 | 37 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 103 | 45 | 71 | 3 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 849 | 149 | 149 | 35 of 63 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 0 | 0 | 1 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 31 | 31 | 34 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 151 | 101 | 134 | 4 of 36 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 1 | 1 | 6 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 0 | 0 | 11 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 132 | 21 | 31 | 5 of 14 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 7 | 7 | 7 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 4 | 2 | 0 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,982 | 0 | 0 | 384 of 384 |
