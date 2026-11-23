# Polymarket US recorder: 2026-11-23 22:09 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 9,233; showing any quote: 3,701
- order books recorded: 3,701, of which 2,631 have orders on both sides
- recorded markets with a twin on polymarket.com: 394; with a two-sided book there too: 364
- twins where the US price is the cheaper one by more than the US fee: 76 (37 on the "Yes" side, 39 on the "No" side)
- took 361 seconds; 0 errors

Taking every one of these at the best US price would cost $19,917, and the gaps add up to $308.51. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| Yes | 8.9c | 2,454 | 12.1c / 12.2c | 2.4c | $59.62 | 2028 Presidential Election: Alabama Winner: Democratic Party |
| No | 99.0c | 6,121 | 0.1c / 0.2c | 0.7c | $43.21 | Argentina Presidential Election Winner: Facundo Manes |
| No | 99.0c | 5,948 | 0.2c / 0.4c | 0.5c | $30.09 | Argentina Presidential Election Winner: Victoria Villarruel |
| No | 99.0c | 3,620 | 0.1c / 0.2c | 0.7c | $25.55 | Argentina Presidential Election Winner: Juan Grabois |
| No | 10.7c | 2,491 | 87.0c / 88.0c | 0.4c | $9.77 | 2028 Presidential Election: Alabama Winner: Republican Party |
| Yes | 3.0c | 2,179 | 3.7c / 4.2c | 0.4c | $9.23 | TIME Person of the Year 2026: Marco Rubio |
| No | 5.2c | 270 | 90.0c / 91.0c | 3.3c | $9.00 | 2028 Presidential Election: Hawaii Winner: Democratic Party |
| Yes | 11.0c | 361 | 14.3c / 14.4c | 2.4c | $8.55 | Argentina Presidential Election Winner: Sergio Massa |
| No | 4.9c | 288 | 91.0c / 92.0c | 2.7c | $7.65 | 2028 Presidential Election: Delaware Winner: Democratic Party |
| Yes | 4.9c | 122 | 10.2c / 10.6c | 4.9c | $5.91 | 2028 Presidential Election: Maryland Winner: Republican Party |
| No | 5.7c | 147 | 89.0c / 90.0c | 3.8c | $5.56 | 2028 Presidential Election: Maryland Winner: Democratic Party |
| No | 5.4c | 260 | 91.0c / 92.0c | 2.1c | $5.51 | 2028 Presidential Election: Washington Winner: Democratic Party |
| Yes | 4.5c | 120 | 9.0c / 10.0c | 4.1c | $4.92 | 2028 Presidential Election: Idaho Winner: Democratic Party |
| No | 99.0c | 794 | 0.1c / 0.3c | 0.6c | $4.81 | Argentina Presidential Election Winner: Juan Schiaretti |
| No | 10.4c | 99 | 83.0c / 84.0c | 4.7c | $4.67 | 2028 Presidential Election: Louisiana Winner: Republican Party |
| No | 37.0c | 235 | 58.0c / 59.0c | 1.8c | $4.19 | 2027 Louisiana Governor Election Winner: Republican Party |
| Yes | 3.0c | 52 | 11.0c / 29.0c | 7.7c | $4.01 | 2027 Minnesota Senate Democratic Nominee: John Hoffman |
| No | 66.6c | 1,380 | 30.0c / 31.0c | 0.3c | $3.96 | 2028 Presidential Election: North Carolina Winner: Republican Party |
| Yes | 4.6c | 123 | 8.0c / 9.0c | 3.0c | $3.67 | 2028 Presidential Election: Hawaii Winner: Republican Party |
| No | 78.0c | 896 | 10.0c / 20.0c | 0.4c | $3.32 | US Birth Rate in 2026? (Per 1000 Women): 53.0+ |
| No | 5.4c | 284 | 92.0c / 93.0c | 1.1c | $3.16 | 2028 Presidential Election: Wyoming Winner: Republican Party |
| Yes | 4.1c | 120 | 7.0c / 8.0c | 2.5c | $3.03 | 2028 Presidential Election: Arkansas Winner: Democratic Party |
| Yes | 5.0c | 85 | 9.0c / 59.0c | 3.5c | $3.01 | 2027 Minnesota Senate Republican Nominee: Brad Finstad |
| No | 43.0c | 110 | 51.0c / 52.0c | 2.7c | $2.94 | 2027 Mississippi Governor Election Winner: Republican Party |
| No | 8.2c | 262 | 89.0c / 90.0c | 1.1c | $2.84 | 2028 Presidential Election: Idaho Winner: Republican Party |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 186 | 202 | 0 of 10 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 55 | 16 | 16 | 7 of 16 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 15 | 15 | 15 | 0 of 3 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 36 | 19 | 33 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 32 | 19 | 20 | 1 of 6 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 2 | 25 | 9 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 142 | 157 | 0 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 149 | 90 | 149 | 0 of 12 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 33 | 26 | 32 | 0 of 7 |
| finance_20261112 (daily_event) | $50 | 500 | none | 51 | 47 | 51 | 0 of 10 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 16 | 19 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 37 | 39 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 104 | 32 | 64 | 4 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 1,023 | 520 | 520 | 28 of 82 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 0 | 8 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 78 | 78 | 2 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 191 | 147 | 186 | 1 of 40 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 5 | 7 | 0 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 11 | 5 | 0 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 11 | 10 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 4 | 8 | 0 of 2 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 32 | 32 | 3 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 7 | 7 | 8 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 125 | 47 | 88 | 1 of 13 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 10 | 10 | 10 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 3 | 2 | 3 | 0 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 10 | 0 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 11 | 0 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 11 | 0 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 12 | 0 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 5 | 1 | 1 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 5 | 2 | 1 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 3 | 0 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 11 | 7 | 0 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 10 | 6 | 0 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 12 | 8 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,551 | 0 | 0 | 325 of 325 |
