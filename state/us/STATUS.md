# Polymarket US recorder: 2026-11-17 21:51 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 9,018; showing any quote: 3,143
- order books recorded: 3,143, of which 2,441 have orders on both sides
- recorded markets with a twin on polymarket.com: 378; with a two-sided book there too: 341
- twins where the US price is the cheaper one by more than the US fee: 126 (59 on the "Yes" side, 67 on the "No" side)
- took 328 seconds; 0 errors

Taking every one of these at the best US price would cost $164,410, and the gaps add up to $903.03. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 96.0c | 39,807 | 2.9c / 3.1c | 0.5c | $213.05 | Fed Decision in December: No Change |
| No | 98.0c | 15,179 | 1.0c / 1.1c | 0.7c | $108.35 | Next CEO of NVIDIA?: Lisa Su |
| Yes | 3.0c | 43,053 | 3.5c / 3.8c | 0.2c | $96.24 | Next CEO of NVIDIA?: Tim Cook |
| Yes | 21.0c | 7,595 | 23.8c / 25.0c | 1.2c | $92.95 | Prime Minister of Israel After the Next Election: Benjamin Netanyahu |
| No | 95.0c | 14,893 | 4.0c / 4.1c | 0.4c | $66.83 | Fed Decision in December: 50+ bps Increase |
| No | 99.0c | 60,483 | 0.2c / 0.8c | 0.1c | $64.08 | Best Chinese AI Company end of November?: MiniMax |
| Yes | 92.0c | 16,076 | 93.0c / 94.0c | 0.3c | $48.36 | Fed Decision in December: 25 bps Increase |
| No | 61.7c | 844 | 29.0c / 31.0c | 5.1c | $42.65 | 2028 Presidential Election: North Carolina Winner: Republican Party |
| No | 97.0c | 7,323 | 1.1c / 2.2c | 0.5c | $38.34 | TIME Person of the Year 2026: Mohammad-Bagher Ghalibaf |
| No | 96.0c | 4,876 | 2.7c / 2.9c | 0.7c | $35.85 | TIME Person of the Year 2026: Mojtaba Khamenei |
| Yes | 95.0c | 604 | 96.5c / 97.7c | 1.0c | $6.33 | "GTA VI: The Album" First Week Sales?: 50k+ |
| No | 6.3c | 100 | 86.0c / 88.0c | 5.1c | $5.14 | 2028 Presidential Election: New York Winner: Democratic Party |
| No | 99.0c | 845 | 0.2c / 0.3c | 0.6c | $5.12 | Argentina Presidential Election Winner: Esteban Bullrich |
| No | 99.0c | 809 | 0.1c / 0.3c | 0.6c | $4.90 | Argentina Presidential Election Winner: Juan Schiaretti |
| No | 36.0c | 172 | 58.0c / 59.0c | 2.8c | $4.84 | 2027 Louisiana Governor Election Winner: Republican Party |
| No | 10.3c | 100 | 83.0c / 84.0c | 4.8c | $4.82 | 2028 Presidential Election: Louisiana Winner: Republican Party |
| No | 99.0c | 596 | 0.1c / 0.2c | 0.7c | $4.21 | Argentina Presidential Election Winner: Facundo Manes |
| Yes | 10.0c | 82 | 15.7c / 17.4c | 4.8c | $3.99 | Argentina Presidential Election Winner: Sergio Massa |
| No | 22.5c | 130 | 72.0c / 73.0c | 2.8c | $3.70 | 2028 Presidential Election: Alaska Winner: Republican Party |
| No | 99.0c | 706 | 0.2c / 0.4c | 0.5c | $3.57 | Dancing With The Stars S35 Winner: Maura Higgins |
| No | 99.0c | 451 | 0.1c / 0.2c | 0.7c | $3.18 | Argentina Presidential Election Winner: Juan Grabois |
| No | 6.4c | 100 | 88.0c / 90.0c | 3.0c | $3.03 | 2028 Presidential Election: North Dakota Winner: Republican Party |
| Yes | 82.0c | 1,005 | 83.7c / 85.1c | 0.3c | $2.99 | Avengers: Doomsday Rotten Tomatoes Score?: 70+ |
| No | 6.5c | 101 | 89.0c / 90.0c | 2.9c | $2.95 | 2028 Presidential Election: Delaware Winner: Democratic Party |
| No | 7.5c | 101 | 86.0c / 89.0c | 2.8c | $2.87 | 2028 Presidential Election: Illinois Winner: Democratic Party |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 188 | 202 | 0 of 10 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 38 | 15 | 15 | 3 of 12 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 30 | 20 | 22 | 0 of 5 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 36 | 28 | 33 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 9 | 9 | 9 | 0 of 3 |
| finance_nvda_nextceo_20261112 (daily_event) | $200 | 1,000 | none | 27 | 11 | 27 | 0 of 2 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 1 | 14 | 9 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 107 | 65 | 0 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 140 | 87 | 139 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 45 | 31 | 33 | 1 of 8 |
| finance_20261112 (daily_event) | $50 | 500 | none | 55 | 47 | 51 | 0 of 11 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 17 | 18 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 34 | 36 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 102 | 40 | 70 | 3 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 796 | 243 | 243 | 20 of 59 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 1 | 0 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 16 | 16 | 39 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 194 | 146 | 182 | 1 of 41 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 5 | 6 | 1 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 5 | 6 | 1 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 8 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 6 | 1 of 2 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 2 | 2 | 6 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 5 | 5 | 7 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 139 | 49 | 82 | 3 of 14 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 7 | 7 | 7 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 4 | 2 | 1 | 0 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 4 | 6 | 1 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 7 | 6 | 0 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 5 | 6 | 0 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 12 | 12 | 0 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 12 | 12 | 0 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 12 | 12 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,785 | 0 | 0 | 356 of 356 |
