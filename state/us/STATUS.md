# Polymarket US recorder: 2026-11-25 02:22 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 8,993; showing any quote: 3,686
- order books recorded: 3,686, of which 2,624 have orders on both sides
- recorded markets with a twin on polymarket.com: 372; with a two-sided book there too: 344
- twins where the US price is the cheaper one by more than the US fee: 71 (44 on the "Yes" side, 27 on the "No" side)
- took 390 seconds; 0 errors

Taking every one of these at the best US price would cost $245,713, and the gaps add up to $1,399.72. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 97.0c | 156,595 | 2.3c / 2.4c | 0.3c | $506.66 | Fed Decision in December: 50+ bps Increase |
| No | 99.0c | 20,434 | 0.1c / 0.2c | 0.7c | $144.25 | Argentina Presidential Election Winner: Facundo Manes |
| No | 99.0c | 18,068 | 0.2c / 0.3c | 0.6c | $109.48 | Argentina Presidential Election Winner: Victoria Villarruel |
| Yes | 7.2c | 4,377 | 10.0c / 11.0c | 2.2c | $94.77 | 2028 Presidential Election: Tennessee Winner: Democratic Party |
| Yes | 9.5c | 4,625 | 12.1c / 12.2c | 1.8c | $82.47 | 2028 Presidential Election: Alabama Winner: Democratic Party |
| No | 97.0c | 10,612 | 1.3c / 2.0c | 0.7c | $76.78 | "GTA VI: The Album" First Week Sales?: 200k+ |
| No | 99.0c | 8,769 | 0.1c / 0.2c | 0.7c | $61.91 | Argentina Presidential Election Winner: Juan Grabois |
| No | 9.9c | 4,464 | 87.0c / 88.0c | 1.3c | $55.92 | 2028 Presidential Election: Alabama Winner: Republican Party |
| No | 99.0c | 10,821 | 0.2c / 0.5c | 0.4c | $43.93 | Argentina Presidential Election Winner: Dante Gebel |
| No | 99.0c | 4,077 | 0.2c / 0.3c | 0.6c | $24.71 | Argentina Presidential Election Winner: Esteban Bullrich |
| No | 5.4c | 499 | 89.0c / 90.0c | 4.1c | $20.53 | 2028 Presidential Election: Idaho Winner: Republican Party |
| Yes | 29.4c | 754 | 34.0c / 35.0c | 2.6c | $19.83 | 2028 Presidential Election: Iowa Winner: Democratic Party |
| No | 96.0c | 5,293 | 2.5c / 3.3c | 0.3c | $17.74 | TIME Person of the Year 2026: Artificial Intelligence |
| No | 97.0c | 2,732 | 1.9c / 2.3c | 0.4c | $11.57 | Prime Minister of Israel After the Next Election: Avigdor Lieberman |
| No | 87.6c | 402 | 8.0c / 9.0c | 2.4c | $9.51 | 2028 Presidential Election: Washington Winner: Republican Party |
| No | 95.0c | 3,630 | 3.9c / 4.3c | 0.2c | $9.03 | Fed Decision in December: No Change |
| No | 9.4c | 174 | 84.0c / 85.0c | 4.8c | $8.33 | 2028 Presidential Election: Louisiana Winner: Republican Party |
| Yes | 10.0c | 4,754 | 11.0c / 12.0c | 0.1c | $6.89 | 2028 Presidential Election: Kentucky Winner: Democratic Party |
| Yes | 31.6c | 876 | 34.4c / 34.5c | 0.7c | $6.54 | 2028 Presidential Election: Georgia Winner: Republican Party |
| Yes | 6.1c | 186 | 10.0c / 10.5c | 3.4c | $6.24 | 2028 Presidential Election: Maryland Winner: Republican Party |
| Yes | 21.0c | 257 | 25.0c / 26.0c | 2.4c | $6.22 | Best Chinese AI Company end of November?: Alibaba |
| Yes | 5.2c | 185 | 9.0c / 10.0c | 3.3c | $6.17 | 2028 Presidential Election: Idaho Winner: Democratic Party |
| Yes | 12.0c | 424 | 14.3c / 14.4c | 1.3c | $5.50 | Argentina Presidential Election Winner: Sergio Massa |
| Yes | 1.0c | 4,939 | 1.2c / 1.5c | 0.1c | $5.23 | TIME Person of the Year 2026: Jerome Powell |
| Yes | 7.5c | 131 | 12.0c / 13.0c | 3.8c | $5.04 | 2028 Presidential Election: Louisiana Winner: Democratic Party |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| energy_wti_up_down_1d_20261121 (daily_event) | $500 | 2,500 | 3c | 1 | 1 | 1 | 0 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 185 | 201 | 0 of 10 |
| energy_natgas_up_down_1d_20261121 (daily_event) | $250 | 1,250 | 3c | 1 | 1 | 1 | 0 of 1 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 62 | 25 | 25 | 6 of 16 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 15 | 13 | 15 | 0 of 3 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 37 | 15 | 35 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 32 | 31 | 31 | 0 of 6 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 4 | 22 | 8 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 127 | 127 | 0 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 149 | 84 | 147 | 0 of 12 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 33 | 25 | 29 | 0 of 7 |
| finance_20261112 (daily_event) | $50 | 500 | none | 51 | 37 | 51 | 0 of 10 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 16 | 19 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 35 | 34 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 104 | 31 | 64 | 4 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 1,030 | 458 | 458 | 34 of 82 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 3 | 3 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 66 | 66 | 11 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 188 | 147 | 180 | 1 of 38 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 10 | 6 | 0 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 7 | 6 | 0 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 9 | 8 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 8 | 7 | 0 of 2 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 36 | 36 | 3 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 32 | 32 | 5 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 124 | 43 | 78 | 2 of 13 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 10 | 10 | 10 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 3 | 1 | 1 | 1 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 8 | 9 | 0 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 8 | 7 | 0 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 9 | 6 | 0 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 9 | 0 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 11 | 7 | 0 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 6 | 0 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 6 | 1 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 6 | 1 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 6 | 1 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 7 | 6 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,368 | 0 | 0 | 300 of 300 |
