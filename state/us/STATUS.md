# Polymarket US recorder: 2026-11-12 03:15 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 9,286; showing any quote: 2,785
- order books recorded: 2,785, of which 2,313 have orders on both sides
- recorded markets with a twin on polymarket.com: 399; with a two-sided book there too: 347
- twins where the US price is the cheaper one by more than the US fee: 115 (40 on the "Yes" side, 75 on the "No" side)
- took 345 seconds; 0 errors

Taking every one of these at the best US price would cost $590,867, and the gaps add up to $10,157.11. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 91.0c | 480,359 | 5.2c / 6.3c | 1.9c | $9,232.27 | Prime Minister of Israel After the Next Election: Avigdor Lieberman |
| No | 95.0c | 30,724 | 3.2c / 3.3c | 1.2c | $383.67 | Prime Minister of Israel After the Next Election: Naftali Bennett |
| No | 95.0c | 18,333 | 0.4c / 3.3c | 1.2c | $228.94 | Next CEO of NVIDIA?: Lisa Su |
| No | 99.0c | 62,065 | 0.4c / 0.8c | 0.1c | $65.76 | Best Chinese AI Company end of November?: MiniMax |
| No | 95.0c | 1,136 | 0.2c / 1.0c | 3.5c | $40.32 | Next CEO of NVIDIA?: Bill Dally |
| No | 35.0c | 94,023 | 62.4c / 62.8c | 0.0c | $36.43 | Prime Minister of Israel After the Next Election: Gadi Eizenkot |
| Yes | 61.0c | 65 | 86.0c / 89.0c | 22.7c | $14.67 | 2027 Minnesota Senate Special Election Winner: Democratic Party |
| No | 94.0c | 257 | 0.5c / 0.6c | 4.9c | $12.52 | Best Chinese AI Company end of November?: DeepSeek |
| Yes | 23.0c | 79 | 39.0c / 41.0c | 14.3c | $11.29 | 2027 Louisiana Governor Election Winner: Democratic Party |
| No | 23.9c | 2,607 | 72.0c / 74.0c | 0.4c | $9.70 | 2028 Presidential Election: Alaska Winner: Republican Party |
| No | 16.0c | 56 | 65.0c / 67.0c | 15.7c | $8.79 | US Birth Rate in 2026? (Per 1000 Women): 52.0+ |
| No | 95.0c | 177 | 0.2c / 0.4c | 4.1c | $7.35 | Next CEO of NVIDIA?: Debora Shoquist |
| No | 81.0c | 161 | 11.0c / 13.0c | 4.5c | $7.29 | 2027 Minnesota Senate Special Election Winner: Republican Party |
| Yes | 80.0c | 405 | 83.1c / 85.4c | 1.6c | $6.40 | Avengers: Doomsday Rotten Tomatoes Score?: 70+ |
| Yes | 11.0c | 367 | 13.6c / 13.7c | 1.7c | $6.13 | Argentina Presidential Election Winner: Sergio Massa |
| Yes | 29.8c | 110 | 36.6c / 37.7c | 4.8c | $5.29 | 2028 Presidential Election: Georgia Winner: Republican Party |
| No | 99.0c | 848 | 0.1c / 0.3c | 0.6c | $5.14 | Argentina Presidential Election Winner: Esteban Bullrich |
| No | 99.0c | 596 | 0.1c / 0.2c | 0.7c | $4.21 | Argentina Presidential Election Winner: Facundo Manes |
| No | 66.0c | 137 | 26.0c / 29.0c | 2.9c | $3.93 | 2027 Mississippi Governor Election Winner: Democratic Party |
| No | 96.0c | 648 | 2.9c / 3.1c | 0.5c | $3.47 | Fed Decision in December: No Change |
| No | 99.0c | 459 | 0.1c / 0.2c | 0.7c | $3.24 | Argentina Presidential Election Winner: Juan Grabois |
| No | 71.1c | 155 | 24.0c / 25.0c | 1.9c | $3.01 | 2028 Presidential Election: New Hampshire Winner: Republican Party |
| No | 92.0c | 991 | 6.0c / 7.0c | 0.3c | $2.98 | TIME Person of the Year 2026: Pope Leo XIV |
| Yes | 61.0c | 61 | 68.0c / 69.0c | 4.7c | $2.88 | 2028 Presidential Election: Michigan Winner: Democratic Party |
| No | 2.0c | 60 | 92.2c / 94.0c | 3.8c | $2.28 | "GTA VI: The Album" First Week Sales?: 50k+ |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 177 | 161 | 177 | 0 of 9 |
| kpic_20261107 (daily) | $250 | 2,000 | 4c | 28 | 0 | 0 | 7 of 7 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 12 | 11 | 12 | 0 of 2 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 33 | 22 | 31 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 11 | 10 | 10 | 0 of 3 |
| finance_nvda_nextceo_20261112 (daily_event) | $200 | 1,000 | none | 7 | 7 | 7 | 0 of 1 |
| climate_20260924 (live) | $185 | 7,500 | none | 60 | 5 | 24 | 5 of 10 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 180 | 94 | 57 | 2 of 21 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 140 | 88 | 139 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 25 | 14 | 19 | 0 of 6 |
| finance_20261112 (daily_event) | $50 | 500 | none | 64 | 57 | 62 | 0 of 13 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 14 | 17 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 31 | 37 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 103 | 41 | 64 | 3 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 861 | 145 | 145 | 34 of 65 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 3 | 1 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 98 | 31 | 31 | 33 of 49 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 166 | 107 | 146 | 3 of 39 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 0 | 0 | 7 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 0 | 0 | 11 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 117 | 19 | 24 | 6 of 12 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 7 | 7 | 7 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 4 | 2 | 0 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,992 | 0 | 0 | 385 of 385 |
