# Polymarket US recorder: 2026-11-27 04:22 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 8,587; showing any quote: 3,848
- order books recorded: 3,848, of which 2,689 have orders on both sides
- recorded markets with a twin on polymarket.com: 370; with a two-sided book there too: 348
- twins where the US price is the cheaper one by more than the US fee: 59 (36 on the "Yes" side, 23 on the "No" side)
- took 396 seconds; 0 errors

Taking every one of these at the best US price would cost $133,791, and the gaps add up to $1,058.07. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 99.0c | 34,639 | 0.1c / 0.2c | 0.7c | $239.39 | Argentina Presidential Election Winner: Facundo Manes |
| No | 99.0c | 28,980 | 0.1c / 0.2c | 0.7c | $200.28 | Argentina Presidential Election Winner: Juan Grabois |
| No | 99.0c | 29,261 | 0.2c / 0.3c | 0.6c | $172.96 | Argentina Presidential Election Winner: Victoria Villarruel |
| No | 99.0c | 26,205 | 0.2c / 0.3c | 0.6c | $154.90 | Argentina Presidential Election Winner: Esteban Bullrich |
| No | 95.0c | 12,107 | 3.6c / 3.7c | 0.8c | $94.13 | Fed Decision in December: No Change |
| Yes | 29.4c | 1,637 | 34.0c / 35.0c | 2.3c | $37.93 | 2028 Presidential Election: Iowa Winner: Democratic Party |
| Yes | 1.0c | 2,574 | 1.7c / 1.9c | 0.6c | $15.21 | TIME Person of the Year 2026: Shehbaz Sharif |
| Yes | 3.0c | 887 | 5.0c / 7.0c | 1.7c | $14.90 | 2028 Presidential Election: Rhode Island Winner: Republican Party |
| Yes | 29.9c | 416 | 35.0c / 36.0c | 2.8c | $11.62 | 2028 Presidential Election: Wisconsin Winner: Republican Party |
| Yes | 7.2c | 513 | 10.0c / 11.0c | 2.1c | $10.60 | 2028 Presidential Election: Tennessee Winner: Democratic Party |
| Yes | 12.0c | 431 | 15.4c / 15.5c | 2.2c | $9.64 | Argentina Presidential Election Winner: Sergio Massa |
| Yes | 1.0c | 2,430 | 1.5c / 1.9c | 0.4c | $9.50 | Best Chinese AI Company end of November?: Tencent |
| Yes | 4.0c | 466 | 6.0c / 8.0c | 1.6c | $7.36 | 2028 Presidential Election: Wyoming Winner: Democratic Party |
| Yes | 90.8c | 503 | 93.0c / 94.0c | 1.3c | $6.44 | 2028 Presidential Election: Illinois Winner: Democratic Party |
| No | 10.8c | 4,515 | 87.0c / 88.0c | 0.1c | $6.34 | 2028 Presidential Election: Alabama Winner: Republican Party |
| Yes | 1.0c | 6,739 | 1.2c / 1.9c | 0.1c | $6.14 | TIME Person of the Year 2026: Jerome Powell |
| No | 10.8c | 451 | 83.0c / 87.0c | 1.1c | $5.14 | 2028 Presidential Election: Utah Winner: Republican Party |
| No | 4.8c | 82 | 89.0c / 90.0c | 4.7c | $3.87 | 2028 Presidential Election: Idaho Winner: Republican Party |
| Yes | 31.6c | 893 | 34.4c / 34.5c | 0.4c | $3.77 | 2028 Presidential Election: Georgia Winner: Republican Party |
| No | 9.5c | 620 | 88.0c / 89.0c | 0.6c | $3.44 | 2028 Presidential Election: Louisiana Winner: Republican Party |
| Yes | 7.5c | 89 | 12.0c / 13.0c | 3.7c | $3.31 | 2028 Presidential Election: Louisiana Winner: Democratic Party |
| Yes | 6.8c | 77 | 11.0c / 13.0c | 3.5c | $2.68 | 2028 Presidential Election: West Virginia Winner: Democratic Party |
| No | 9.3c | 149 | 87.0c / 88.0c | 1.8c | $2.65 | 2028 Presidential Election: New Jersey Winner: Democratic Party |
| No | 93.0c | 274 | 0.4c / 5.4c | 0.9c | $2.43 | 2027 Minnesota Senate Democratic Nominee: Erin Maye Quade |
| Yes | 3.0c | 26 | 12.0c / 28.0c | 8.7c | $2.25 | 2027 Minnesota Senate Democratic Nominee: Will Stancil |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 185 | 202 | 0 of 10 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 108 | 66 | 66 | 3 of 27 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 37 | 16 | 36 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 32 | 28 | 31 | 0 of 6 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 2 | 21 | 10 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 131 | 163 | 0 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 146 | 81 | 144 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 33 | 23 | 33 | 0 of 7 |
| finance_20261112 (daily_event) | $50 | 500 | none | 51 | 38 | 51 | 0 of 10 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 16 | 19 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 34 | 39 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 104 | 29 | 64 | 4 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 1,030 | 465 | 465 | 29 of 82 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 1 | 2 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 92 | 92 | 0 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 188 | 150 | 181 | 1 of 38 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 10 | 7 | 0 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 9 | 7 | 0 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 12 | 11 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 8 | 8 | 0 of 2 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 38 | 38 | 1 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 30 | 30 | 5 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 120 | 47 | 93 | 0 of 13 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 10 | 10 | 10 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 3 | 2 | 2 | 1 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 9 | 9 | 0 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 6 | 1 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 7 | 8 | 0 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 10 | 0 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 10 | 0 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 10 | 0 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 9 | 7 | 0 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 7 | 8 | 0 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 6 | 1 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 9 | 8 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,180 | 0 | 0 | 277 of 277 |
