# Polymarket US recorder: 2026-11-26 03:18 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 8,671; showing any quote: 3,772
- order books recorded: 3,772, of which 2,652 have orders on both sides
- recorded markets with a twin on polymarket.com: 364; with a two-sided book there too: 336
- twins where the US price is the cheaper one by more than the US fee: 64 (39 on the "Yes" side, 25 on the "No" side)
- took 444 seconds; 0 errors

Taking every one of these at the best US price would cost $86,779, and the gaps add up to $616.97. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 99.0c | 17,350 | 0.1c / 0.2c | 0.7c | $119.91 | Argentina Presidential Election Winner: Juan Grabois |
| No | 99.0c | 17,140 | 0.1c / 0.2c | 0.7c | $118.45 | Argentina Presidential Election Winner: Facundo Manes |
| No | 99.0c | 16,301 | 0.2c / 0.3c | 0.6c | $96.35 | Argentina Presidential Election Winner: Victoria Villarruel |
| No | 99.0c | 20,619 | 0.2c / 0.5c | 0.4c | $80.64 | Argentina Presidential Election Winner: Dante Gebel |
| No | 97.0c | 9,029 | 2.1c / 2.2c | 0.5c | $43.33 | Fed Decision in December: 50+ bps Increase |
| No | 99.0c | 5,235 | 0.2c / 0.3c | 0.6c | $30.94 | Argentina Presidential Election Winner: Esteban Bullrich |
| Yes | 1.0c | 6,764 | 1.3c / 2.0c | 0.2c | $12.93 | TIME Person of the Year 2026: Jerome Powell |
| Yes | 29.9c | 409 | 35.0c / 36.0c | 2.8c | $11.42 | 2028 Presidential Election: Wisconsin Winner: Republican Party |
| Yes | 7.2c | 514 | 10.0c / 11.0c | 2.1c | $10.61 | 2028 Presidential Election: Tennessee Winner: Democratic Party |
| Yes | 29.4c | 443 | 34.0c / 35.0c | 2.3c | $10.26 | 2028 Presidential Election: Iowa Winner: Democratic Party |
| No | 10.8c | 4,422 | 87.0c / 88.0c | 0.1c | $6.20 | 2028 Presidential Election: Alabama Winner: Republican Party |
| No | 91.0c | 127 | 0.4c / 3.4c | 4.7c | $5.99 | 2027 Minnesota Senate Democratic Nominee: Jacob Frey |
| No | 10.8c | 461 | 86.0c / 87.0c | 1.1c | $5.25 | 2028 Presidential Election: Utah Winner: Republican Party |
| Yes | 12.0c | 457 | 14.3c / 14.4c | 1.1c | $5.20 | Argentina Presidential Election Winner: Sergio Massa |
| Yes | 4.0c | 93 | 10.0c / 55.0c | 5.6c | $5.17 | 2027 Minnesota Senate Republican Nominee: Harry Niska |
| No | 8.8c | 184 | 87.0c / 88.0c | 2.3c | $4.27 | 2028 Presidential Election: New York Winner: Democratic Party |
| No | 4.8c | 86 | 89.0c / 90.0c | 4.7c | $4.05 | 2028 Presidential Election: Idaho Winner: Republican Party |
| Yes | 31.6c | 876 | 34.4c / 34.5c | 0.4c | $3.70 | 2028 Presidential Election: Georgia Winner: Republican Party |
| Yes | 7.5c | 88 | 12.0c / 13.0c | 3.7c | $3.28 | 2028 Presidential Election: Louisiana Winner: Democratic Party |
| Yes | 3.0c | 460 | 4.0c / 7.0c | 0.7c | $3.13 | 2028 Presidential Election: Rhode Island Winner: Republican Party |
| No | 9.3c | 160 | 87.0c / 88.0c | 1.8c | $2.83 | 2028 Presidential Election: New Jersey Winner: Democratic Party |
| Yes | 5.2c | 67 | 9.0c / 10.0c | 3.3c | $2.19 | 2028 Presidential Election: Idaho Winner: Democratic Party |
| Yes | 4.8c | 127 | 7.0c / 9.0c | 1.7c | $2.15 | 2028 Presidential Election: Hawaii Winner: Republican Party |
| Yes | 8.8c | 49 | 14.0c / 15.0c | 4.3c | $2.14 | 2028 Presidential Election: Utah Winner: Democratic Party |
| Yes | 3.0c | 22 | 13.0c / 29.0c | 9.7c | $2.13 | 2027 Minnesota Senate Democratic Nominee: Will Stancil |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 184 | 202 | 0 of 10 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 108 | 57 | 57 | 5 of 27 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 37 | 16 | 35 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 32 | 29 | 31 | 0 of 6 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 1 | 21 | 10 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 131 | 160 | 0 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 149 | 80 | 145 | 0 of 12 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 33 | 24 | 32 | 0 of 7 |
| finance_20261112 (daily_event) | $50 | 500 | none | 51 | 37 | 51 | 0 of 10 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 16 | 17 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 33 | 36 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 104 | 32 | 64 | 4 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 1,030 | 451 | 451 | 32 of 82 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 1 | 7 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 91 | 91 | 0 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 188 | 150 | 181 | 1 of 38 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 11 | 9 | 0 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 8 | 6 | 0 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 10 | 10 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 7 | 9 | 0 of 2 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 33 | 33 | 3 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 29 | 29 | 5 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 122 | 45 | 97 | 0 of 13 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 10 | 10 | 10 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 3 | 1 | 2 | 1 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 9 | 10 | 0 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 12 | 0 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 8 | 10 | 0 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 10 | 0 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 10 | 0 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 9 | 9 | 0 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 8 | 7 | 0 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 7 | 8 | 0 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 6 | 1 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 10 | 9 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,226 | 0 | 0 | 283 of 283 |
