# Polymarket US recorder: 2026-11-24 18:00 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 8,939; showing any quote: 3,641
- order books recorded: 3,641, of which 2,601 have orders on both sides
- recorded markets with a twin on polymarket.com: 370; with a two-sided book there too: 344
- twins where the US price is the cheaper one by more than the US fee: 72 (43 on the "Yes" side, 29 on the "No" side)
- took 395 seconds; 0 errors

Taking every one of these at the best US price would cost $215,417, and the gaps add up to $1,144.17. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 97.0c | 154,094 | 2.2c / 2.3c | 0.4c | $652.66 | Fed Decision in December: 50+ bps Increase |
| No | 99.0c | 19,665 | 0.1c / 0.2c | 0.7c | $138.82 | Argentina Presidential Election Winner: Facundo Manes |
| No | 99.0c | 18,218 | 0.2c / 0.3c | 0.6c | $110.39 | Argentina Presidential Election Winner: Victoria Villarruel |
| No | 99.0c | 11,022 | 0.1c / 0.2c | 0.7c | $77.81 | Argentina Presidential Election Winner: Juan Grabois |
| Yes | 7.2c | 2,365 | 10.0c / 11.0c | 2.2c | $51.20 | 2028 Presidential Election: Tennessee Winner: Democratic Party |
| No | 99.0c | 10,192 | 0.3c / 0.6c | 0.3c | $31.18 | Argentina Presidential Election Winner: Dante Gebel |
| No | 99.0c | 5,034 | 0.2c / 0.3c | 0.6c | $30.50 | Argentina Presidential Election Winner: Esteban Bullrich |
| Yes | 12.0c | 460 | 14.3c / 14.4c | 1.3c | $5.96 | Argentina Presidential Election Winner: Sergio Massa |
| Yes | 6.1c | 136 | 10.0c / 10.6c | 3.4c | $4.55 | 2028 Presidential Election: Maryland Winner: Republican Party |
| Yes | 5.2c | 128 | 9.0c / 10.0c | 3.3c | $4.25 | 2028 Presidential Election: Idaho Winner: Democratic Party |
| Yes | 60.5c | 91 | 67.0c / 68.0c | 4.2c | $3.84 | 2028 Presidential Election: Nevada Winner: Democratic Party |
| Yes | 10.0c | 2,519 | 11.0c / 12.0c | 0.1c | $3.65 | 2028 Presidential Election: Kentucky Winner: Democratic Party |
| No | 43.0c | 101 | 51.0c / 52.0c | 2.7c | $2.71 | 2027 Mississippi Governor Election Winner: Republican Party |
| Yes | 5.1c | 100 | 8.0c / 9.0c | 2.4c | $2.44 | 2028 Presidential Election: Illinois Winner: Republican Party |
| No | 9.9c | 186 | 87.0c / 88.0c | 1.3c | $2.33 | 2028 Presidential Election: New York Winner: Democratic Party |
| Yes | 7.0c | 63 | 11.0c / 60.0c | 3.4c | $2.14 | 2027 Minnesota Senate Republican Nominee: Brad Finstad |
| Yes | 29.4c | 78 | 34.0c / 35.0c | 2.6c | $2.05 | 2028 Presidential Election: Iowa Winner: Democratic Party |
| Yes | 29.9c | 48 | 35.0c / 36.0c | 3.1c | $1.50 | 2028 Presidential Election: Wisconsin Winner: Republican Party |
| No | 98.0c | 697 | 1.5c / 1.6c | 0.2c | $1.49 | #1 Searched Person on Google 2026?: Donald Trump |
| Yes | 9.5c | 73 | 12.1c / 12.2c | 1.8c | $1.30 | 2028 Presidential Election: Alabama Winner: Democratic Party |
| Yes | 31.6c | 159 | 34.4c / 34.5c | 0.7c | $1.19 | 2028 Presidential Election: Georgia Winner: Republican Party |
| No | 95.0c | 466 | 4.0c / 4.3c | 0.2c | $1.16 | Fed Decision in December: No Change |
| Yes | 14.5c | 301 | 16.0c / 17.0c | 0.3c | $0.97 | 2028 Presidential Election: Mississippi Winner: Democratic Party |
| No | 9.3c | 50 | 87.0c / 88.0c | 1.9c | $0.95 | 2028 Presidential Election: New Jersey Winner: Democratic Party |
| No | 92.0c | 308 | 6.0c / 7.0c | 0.3c | $0.93 | TIME Person of the Year 2026: Pope Leo XIV |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| energy_wti_up_down_1d_20261121 (daily_event) | $500 | 2,500 | 3c | 1 | 1 | 1 | 0 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 182 | 199 | 0 of 10 |
| energy_natgas_up_down_1d_20261121 (daily_event) | $250 | 1,250 | 3c | 1 | 1 | 1 | 0 of 1 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 55 | 29 | 29 | 1 of 16 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 15 | 14 | 15 | 0 of 3 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 37 | 14 | 31 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 32 | 30 | 30 | 0 of 6 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 0 | 3 | 12 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 114 | 61 | 1 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 149 | 84 | 147 | 0 of 12 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 33 | 26 | 26 | 0 of 7 |
| finance_20261112 (daily_event) | $50 | 500 | none | 51 | 36 | 51 | 0 of 10 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 11 | 17 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 33 | 30 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 104 | 31 | 64 | 4 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 983 | 453 | 453 | 28 of 79 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 2 | 1 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 61 | 61 | 11 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 187 | 142 | 179 | 2 of 38 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 6 | 1 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 6 | 1 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 8 | 10 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 6 | 1 of 2 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 36 | 36 | 2 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 33 | 33 | 5 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 124 | 42 | 65 | 2 of 13 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 10 | 10 | 10 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 3 | 1 | 1 | 1 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 7 | 0 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 8 | 6 | 0 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 7 | 6 | 0 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 7 | 0 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 8 | 6 | 0 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 7 | 8 | 0 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 8 | 6 | 0 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 6 | 1 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 6 | 1 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 6 | 1 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,370 | 0 | 0 | 301 of 301 |
