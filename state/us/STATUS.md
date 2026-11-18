# Polymarket US recorder: 2026-11-18 17:58 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 8,927; showing any quote: 3,259
- order books recorded: 3,255, of which 2,432 have orders on both sides
- recorded markets with a twin on polymarket.com: 403; with a two-sided book there too: 352
- twins where the US price is the cheaper one by more than the US fee: 118 (52 on the "Yes" side, 66 on the "No" side)
- took 366 seconds; 0 errors

Taking every one of these at the best US price would cost $169,869, and the gaps add up to $1,214.39. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| Yes | 3.0c | 30,777 | 4.8c / 5.1c | 1.5c | $468.91 | Next CEO of NVIDIA?: Tim Cook |
| No | 99.0c | 71,606 | 0.3c / 0.5c | 0.4c | $290.68 | Best Chinese AI Company end of November?: Moonshot |
| No | 99.0c | 70,483 | 0.3c / 0.6c | 0.3c | $215.64 | Best Chinese AI Company end of November?: MiniMax |
| No | 99.0c | 14,610 | 0.5c / 0.6c | 0.3c | $44.70 | Best Chinese AI Company end of November?: Baidu |
| No | 96.0c | 5,001 | 2.7c / 3.0c | 0.6c | $31.76 | TIME Person of the Year 2026: Mojtaba Khamenei |
| No | 61.7c | 596 | 30.0c / 31.0c | 5.1c | $30.10 | 2028 Presidential Election: North Carolina Winner: Republican Party |
| Yes | 60.3c | 344 | 67.0c / 69.0c | 4.4c | $15.21 | 2028 Presidential Election: North Carolina Winner: Democratic Party |
| Yes | 5.0c | 8,598 | 5.6c / 5.7c | 0.1c | $12.79 | Next CEO of NVIDIA?: Nikesh Arora |
| No | 97.0c | 2,121 | 0.7c / 2.2c | 0.5c | $11.10 | TIME Person of the Year 2026: Mohammad-Bagher Ghalibaf |
| No | 36.0c | 228 | 58.0c / 59.0c | 2.8c | $6.42 | 2027 Louisiana Governor Election Winner: Republican Party |
| No | 62.0c | 819 | 10.0c / 35.0c | 0.8c | $6.24 | US Birth Rate in 2026? (Per 1000 Women): 53.0+ |
| No | 6.3c | 99 | 85.0c / 87.0c | 6.1c | $6.08 | 2028 Presidential Election: New York Winner: Democratic Party |
| No | 99.0c | 845 | 0.2c / 0.3c | 0.6c | $5.12 | Argentina Presidential Election Winner: Esteban Bullrich |
| No | 99.0c | 794 | 0.2c / 0.3c | 0.6c | $4.81 | Argentina Presidential Election Winner: Juan Schiaretti |
| No | 61.6c | 217 | 33.0c / 34.0c | 2.2c | $4.67 | 2028 Presidential Election: Arizona Winner: Republican Party |
| No | 10.5c | 99 | 83.0c / 84.0c | 4.6c | $4.56 | 2028 Presidential Election: Louisiana Winner: Republican Party |
| Yes | 5.0c | 1,814 | 5.7c / 5.8c | 0.2c | $4.51 | TIME Person of the Year 2026: Donald Trump |
| No | 99.0c | 596 | 0.1c / 0.2c | 0.7c | $4.21 | Argentina Presidential Election Winner: Facundo Manes |
| No | 6.3c | 101 | 88.0c / 89.0c | 4.1c | $4.17 | 2028 Presidential Election: Oklahoma Winner: Republican Party |
| No | 99.0c | 451 | 0.1c / 0.2c | 0.7c | $3.18 | Argentina Presidential Election Winner: Juan Grabois |
| No | 6.3c | 101 | 88.0c / 90.0c | 3.1c | $3.17 | 2028 Presidential Election: Idaho Winner: Republican Party |
| No | 6.4c | 99 | 88.0c / 90.0c | 3.0c | $3.00 | 2028 Presidential Election: North Dakota Winner: Republican Party |
| Yes | 10.0c | 84 | 14.4c / 15.5c | 3.5c | $2.97 | Argentina Presidential Election Winner: Sergio Massa |
| No | 41.0c | 61 | 50.0c / 52.0c | 4.7c | $2.86 | 2027 Mississippi Governor Election Winner: Republican Party |
| Yes | 31.0c | 38 | 39.0c / 41.0c | 6.0c | $2.24 | 2027 Louisiana Governor Election Winner: Democratic Party |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 189 | 202 | 0 of 10 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 22 | 20 | 20 | 0 of 7 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 15 | 15 | 15 | 0 of 3 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 36 | 26 | 36 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 9 | 9 | 9 | 0 of 3 |
| finance_nvda_nextceo_20261112 (daily_event) | $200 | 1,000 | none | 27 | 11 | 27 | 0 of 2 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 0 | 14 | 10 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 105 | 68 | 0 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 140 | 88 | 138 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 45 | 30 | 32 | 1 of 8 |
| metals_gold_updown_1h_20261110 (daily_event) | $60 | 3,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| finance_20261112 (daily_event) | $50 | 500 | none | 55 | 47 | 51 | 0 of 11 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 18 | 19 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 37 | 36 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 102 | 40 | 72 | 3 of 13 |
| metals_silver_updown_1h_20261110 (daily_event) | $40 | 2,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 864 | 258 | 258 | 26 of 65 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 2 | 1 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 15 | 15 | 40 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 192 | 136 | 180 | 0 of 40 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 6 | 1 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 6 | 1 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 8 | 9 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 6 | 1 of 2 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 5 | 5 | 6 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 5 | 5 | 8 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 137 | 48 | 81 | 2 of 14 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 7 | 7 | 7 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 4 | 3 | 1 | 0 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 3 | 6 | 1 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 6 | 0 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 7 | 6 | 0 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 12 | 12 | 0 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 12 | 12 | 0 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 12 | 12 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,783 | 0 | 0 | 355 of 355 |
