# Polymarket US recorder: 2026-11-28 13:35 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 8,612; showing any quote: 3,842
- order books recorded: 3,842, of which 2,727 have orders on both sides
- recorded markets with a twin on polymarket.com: 393; with a two-sided book there too: 373
- twins where the US price is the cheaper one by more than the US fee: 64 (38 on the "Yes" side, 26 on the "No" side)
- took 392 seconds; 0 errors

Taking every one of these at the best US price would cost $198,453, and the gaps add up to $1,479.94. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 97.0c | 69,409 | 1.7c / 1.8c | 0.9c | $610.73 | Fed Decision in December: 50+ bps Increase |
| No | 99.0c | 34,638 | 0.1c / 0.2c | 0.7c | $239.38 | Argentina Presidential Election Winner: Facundo Manes |
| No | 99.0c | 28,980 | 0.1c / 0.2c | 0.7c | $200.28 | Argentina Presidential Election Winner: Juan Grabois |
| No | 99.0c | 29,261 | 0.2c / 0.4c | 0.5c | $143.70 | Argentina Presidential Election Winner: Victoria Villarruel |
| No | 99.0c | 25,773 | 0.1c / 0.4c | 0.5c | $126.57 | Argentina Presidential Election Winner: Esteban Bullrich |
| Yes | 1.0c | 2,687 | 1.7c / 2.1c | 0.6c | $15.88 | TIME Person of the Year 2026: Shehbaz Sharif |
| Yes | 3.0c | 887 | 5.0c / 7.0c | 1.7c | $14.90 | 2028 Presidential Election: Rhode Island Winner: Republican Party |
| No | 10.8c | 683 | 84.0c / 86.0c | 2.1c | $14.61 | 2028 Presidential Election: Utah Winner: Republican Party |
| No | 10.7c | 4,497 | 87.0c / 88.0c | 0.2c | $11.20 | 2028 Presidential Election: Kentucky Winner: Republican Party |
| Yes | 95.0c | 4,741 | 95.7c / 95.8c | 0.2c | $8.42 | Another Fed Rate Hike in 2026?: Hike |
| Yes | 4.0c | 433 | 6.0c / 8.0c | 1.6c | $6.83 | 2028 Presidential Election: Wyoming Winner: Democratic Party |
| No | 10.8c | 4,641 | 87.0c / 88.0c | 0.1c | $6.51 | 2028 Presidential Election: Alabama Winner: Republican Party |
| Yes | 1.0c | 6,741 | 1.2c / 1.4c | 0.1c | $6.14 | TIME Person of the Year 2026: Jerome Powell |
| Yes | 92.1c | 5,331 | 93.0c / 94.0c | 0.1c | $5.31 | 2028 Presidential Election: Illinois Winner: Democratic Party |
| Yes | 8.8c | 154 | 13.0c / 15.0c | 3.3c | $5.12 | 2028 Presidential Election: Utah Winner: Democratic Party |
| Yes | 7.5c | 120 | 12.0c / 13.0c | 3.7c | $4.48 | 2028 Presidential Election: Louisiana Winner: Democratic Party |
| Yes | 31.6c | 896 | 34.4c / 34.5c | 0.4c | $3.78 | 2028 Presidential Election: Georgia Winner: Republican Party |
| Yes | 6.8c | 98 | 11.0c / 13.0c | 3.5c | $3.43 | 2028 Presidential Election: West Virginia Winner: Democratic Party |
| Yes | 7.2c | 164 | 10.0c / 11.0c | 2.1c | $3.39 | 2028 Presidential Election: Tennessee Winner: Democratic Party |
| Yes | 5.2c | 101 | 9.0c / 10.0c | 3.3c | $3.29 | 2028 Presidential Election: Idaho Winner: Democratic Party |
| Yes | 3.0c | 38 | 11.0c / 28.0c | 7.7c | $2.88 | 2027 Minnesota Senate Democratic Nominee: Will Stancil |
| Yes | 4.8c | 163 | 7.0c / 8.0c | 1.7c | $2.76 | 2028 Presidential Election: California Winner: Republican Party |
| Yes | 4.0c | 101 | 7.0c / 84.0c | 2.6c | $2.62 | 2027 Minnesota Senate Republican Nominee: Michelle Fischbach |
| No | 8.9c | 109 | 87.0c / 88.0c | 2.2c | $2.40 | 2028 Presidential Election: New York Winner: Democratic Party |
| Yes | 8.7c | 525 | 10.0c / 11.0c | 0.4c | $2.24 | 2028 Presidential Election: Missouri Winner: Democratic Party |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 186 | 202 | 0 of 10 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 114 | 48 | 48 | 8 of 28 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 37 | 19 | 35 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 32 | 27 | 30 | 0 of 6 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 3 | 4 | 12 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 138 | 164 | 0 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 146 | 80 | 144 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 33 | 22 | 33 | 0 of 7 |
| finance_20261112 (daily_event) | $50 | 500 | none | 51 | 37 | 51 | 0 of 10 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 17 | 18 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 36 | 39 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 114 | 36 | 73 | 4 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 1,026 | 468 | 468 | 31 of 82 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 0 | 0 | 1 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 95 | 95 | 0 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 190 | 152 | 185 | 1 of 39 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 11 | 7 | 0 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 10 | 7 | 0 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 10 | 11 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 8 | 7 | 0 of 2 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 34 | 34 | 4 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 30 | 30 | 5 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 120 | 46 | 101 | 0 of 13 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 10 | 10 | 10 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 3 | 1 | 2 | 1 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 8 | 10 | 0 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 10 | 0 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 7 | 9 | 0 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 10 | 0 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 10 | 0 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 11 | 11 | 0 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 11 | 0 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 7 | 8 | 0 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 7 | 0 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 9 | 9 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,200 | 0 | 0 | 279 of 279 |
