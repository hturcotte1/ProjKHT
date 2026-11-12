# Polymarket US recorder: 2026-11-12 09:01 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 9,194; showing any quote: 2,454
- order books recorded: 2,454, of which 2,081 have orders on both sides
- recorded markets with a twin on polymarket.com: 319; with a two-sided book there too: 288
- twins where the US price is the cheaper one by more than the US fee: 112 (43 on the "Yes" side, 69 on the "No" side)
- took 339 seconds; 0 errors

Taking every one of these at the best US price would cost $1,694,183, and the gaps add up to $33,039.57. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 91.0c | 838,959 | 4.7c / 5.4c | 2.8c | $23,675.00 | Prime Minister of Israel After the Next Election: Avigdor Lieberman |
| No | 95.0c | 828,800 | 3.4c / 3.5c | 1.0c | $8,692.04 | Prime Minister of Israel After the Next Election: Naftali Bennett |
| No | 35.0c | 131,922 | 62.5c / 62.6c | 0.2c | $314.96 | Prime Minister of Israel After the Next Election: Gadi Eizenkot |
| No | 99.0c | 19,921 | 0.2c / 0.4c | 0.5c | $100.79 | Next CEO of NVIDIA?: Bill Dally |
| No | 99.0c | 62,066 | 0.4c / 0.8c | 0.1c | $65.76 | Best Chinese AI Company end of November?: MiniMax |
| No | 66.0c | 557 | 27.0c / 29.0c | 2.9c | $15.98 | 2027 Mississippi Governor Election Winner: Democratic Party |
| Yes | 23.0c | 99 | 39.0c / 42.0c | 14.3c | $14.12 | 2027 Louisiana Governor Election Winner: Democratic Party |
| Yes | 38.0c | 112 | 51.3c / 56.1c | 11.1c | $12.37 | Best Chinese AI Company end of November?: Xiaomi |
| No | 23.9c | 2,614 | 72.0c / 74.0c | 0.4c | $9.73 | 2028 Presidential Election: Alaska Winner: Republican Party |
| No | 16.0c | 61 | 65.0c / 67.0c | 15.7c | $9.64 | US Birth Rate in 2026? (Per 1000 Women): 52.0+ |
| No | 88.0c | 583 | 9.4c / 9.5c | 1.5c | $8.72 | Fed Decision in December: 50+ bps Increase |
| No | 94.0c | 172 | 0.5c / 0.6c | 4.9c | $8.38 | Best Chinese AI Company end of November?: DeepSeek |
| Yes | 80.0c | 405 | 83.1c / 85.4c | 1.6c | $6.40 | Avengers: Doomsday Rotten Tomatoes Score?: 70+ |
| No | 31.0c | 15 | 24.0c / 25.0c | 42.0c | $6.36 | Next CEO of NVIDIA?: Ian Buck |
| Yes | 11.0c | 372 | 13.6c / 13.7c | 1.7c | $6.21 | Argentina Presidential Election Winner: Sergio Massa |
| Yes | 82.0c | 233 | 86.0c / 89.0c | 2.6c | $6.04 | 2027 Minnesota Senate Special Election Winner: Democratic Party |
| Yes | 29.8c | 114 | 36.3c / 37.7c | 4.5c | $5.16 | 2028 Presidential Election: Georgia Winner: Republican Party |
| No | 99.0c | 848 | 0.1c / 0.3c | 0.6c | $5.14 | Argentina Presidential Election Winner: Esteban Bullrich |
| No | 92.0c | 1,443 | 6.0c / 7.0c | 0.3c | $4.34 | TIME Person of the Year 2026: Pope Leo XIV |
| No | 99.0c | 596 | 0.1c / 0.2c | 0.7c | $4.21 | Argentina Presidential Election Winner: Facundo Manes |
| No | 31.6c | 162 | 61.0c / 64.0c | 2.3c | $3.80 | 2028 Presidential Election: Ohio Winner: Republican Party |
| Yes | 60.5c | 1,631 | 63.0c / 65.0c | 0.2c | $3.75 | 2028 Presidential Election: Arizona Winner: Democratic Party |
| No | 81.0c | 75 | 11.0c / 13.0c | 4.5c | $3.42 | 2027 Minnesota Senate Special Election Winner: Republican Party |
| No | 99.0c | 459 | 0.1c / 0.2c | 0.7c | $3.24 | Argentina Presidential Election Winner: Juan Grabois |
| Yes | 61.0c | 67 | 68.0c / 69.0c | 4.7c | $3.17 | 2028 Presidential Election: Michigan Winner: Democratic Party |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 177 | 161 | 177 | 0 of 9 |
| kpic_20261107 (daily) | $250 | 2,000 | 4c | 28 | 0 | 0 | 7 of 7 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 30 | 16 | 19 | 1 of 5 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 33 | 22 | 31 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 11 | 10 | 10 | 0 of 3 |
| finance_nvda_nextceo_20261112 (daily_event) | $200 | 1,000 | none | 7 | 7 | 7 | 0 of 1 |
| climate_20260924 (live) | $185 | 7,500 | none | 60 | 1 | 3 | 8 of 10 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 180 | 89 | 58 | 1 of 21 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 140 | 88 | 138 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 45 | 19 | 20 | 0 of 8 |
| finance_20261112 (daily_event) | $50 | 500 | none | 64 | 57 | 62 | 0 of 13 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 15 | 18 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 32 | 37 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 103 | 42 | 69 | 3 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 861 | 88 | 88 | 39 of 65 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 3 | 1 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 98 | 32 | 32 | 32 of 49 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 166 | 107 | 144 | 3 of 39 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 107 | 0 | 0 | 6 of 6 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 1 | 1 | 10 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 120 | 19 | 18 | 7 of 13 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 7 | 7 | 7 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 4 | 2 | 0 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,992 | 0 | 0 | 385 of 385 |
