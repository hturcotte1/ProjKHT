# Polymarket US recorder: 2026-11-25 11:34 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 8,897; showing any quote: 3,735
- order books recorded: 3,735, of which 2,653 have orders on both sides
- recorded markets with a twin on polymarket.com: 368; with a two-sided book there too: 342
- twins where the US price is the cheaper one by more than the US fee: 67 (41 on the "Yes" side, 26 on the "No" side)
- took 364 seconds; 0 errors

Taking every one of these at the best US price would cost $246,745, and the gaps add up to $1,448.36. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 97.0c | 162,449 | 2.2c / 2.4c | 0.3c | $525.60 | Fed Decision in December: 50+ bps Increase |
| Yes | 9.6c | 4,560 | 14.0c / 15.0c | 3.6c | $163.05 | 2028 Presidential Election: Utah Winner: Democratic Party |
| No | 99.0c | 17,780 | 0.1c / 0.2c | 0.7c | $125.52 | Argentina Presidential Election Winner: Juan Grabois |
| No | 99.0c | 16,547 | 0.1c / 0.2c | 0.7c | $116.81 | Argentina Presidential Election Winner: Facundo Manes |
| No | 99.0c | 19,102 | 0.2c / 0.3c | 0.6c | $115.75 | Argentina Presidential Election Winner: Victoria Villarruel |
| No | 99.0c | 19,147 | 0.2c / 0.5c | 0.4c | $77.73 | Argentina Presidential Election Winner: Dante Gebel |
| No | 10.0c | 4,412 | 87.0c / 88.0c | 1.1c | $50.52 | 2028 Presidential Election: Alabama Winner: Republican Party |
| No | 97.0c | 4,822 | 1.6c / 1.8c | 0.9c | $44.54 | Prime Minister of Israel After the Next Election: Avigdor Lieberman |
| Yes | 6.0c | 6,979 | 6.9c / 7.0c | 0.4c | $25.42 | TIME Person of the Year 2026: Benjamin Netanyahu |
| No | 99.0c | 4,077 | 0.2c / 0.3c | 0.6c | $24.71 | Argentina Presidential Election Winner: Esteban Bullrich |
| Yes | 29.4c | 714 | 34.0c / 35.0c | 2.6c | $18.76 | 2028 Presidential Election: Iowa Winner: Democratic Party |
| Yes | 7.5c | 423 | 12.0c / 13.0c | 3.8c | $16.25 | 2028 Presidential Election: Louisiana Winner: Democratic Party |
| Yes | 99.0c | 1,739 | 99.8c / 99.9c | 0.7c | $12.28 | "GTA VI" Metacritic Score?: 98+ |
| No | 97.0c | 2,550 | 1.3c / 2.3c | 0.4c | $10.80 | "GTA VI: The Album" First Week Sales?: 200k+ |
| No | 4.8c | 562 | 92.0c / 93.0c | 1.8c | $9.93 | 2028 Presidential Election: Hawaii Winner: Democratic Party |
| No | 9.2c | 332 | 87.0c / 88.0c | 2.0c | $6.65 | 2028 Presidential Election: New Jersey Winner: Democratic Party |
| Yes | 4.0c | 100 | 11.0c / 41.0c | 6.6c | $6.65 | 2027 Minnesota Senate Republican Nominee: Harry Niska |
| Yes | 31.6c | 878 | 34.4c / 34.5c | 0.7c | $6.56 | 2028 Presidential Election: Georgia Winner: Republican Party |
| Yes | 6.1c | 178 | 10.0c / 10.6c | 3.4c | $5.96 | 2028 Presidential Election: Maryland Winner: Republican Party |
| Yes | 12.1c | 203 | 16.0c / 17.0c | 2.9c | $5.88 | 2028 Presidential Election: Mississippi Winner: Democratic Party |
| Yes | 12.0c | 451 | 14.3c / 14.4c | 1.3c | $5.85 | Argentina Presidential Election Winner: Sergio Massa |
| No | 10.8c | 426 | 84.0c / 87.0c | 1.3c | $5.47 | 2028 Presidential Election: Utah Winner: Republican Party |
| No | 9.9c | 334 | 87.0c / 88.0c | 1.3c | $4.18 | 2028 Presidential Election: New York Winner: Democratic Party |
| Yes | 9.5c | 231 | 12.1c / 12.2c | 1.8c | $4.11 | 2028 Presidential Election: Alabama Winner: Democratic Party |
| No | 43.0c | 146 | 51.0c / 52.0c | 2.7c | $3.91 | 2027 Mississippi Governor Election Winner: Republican Party |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| energy_wti_up_down_1d_20261121 (daily_event) | $500 | 2,500 | 3c | 1 | 1 | 1 | 0 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 184 | 201 | 0 of 10 |
| energy_natgas_up_down_1d_20261121 (daily_event) | $250 | 1,250 | 3c | 1 | 1 | 1 | 0 of 1 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 67 | 31 | 31 | 4 of 17 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 37 | 14 | 35 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 32 | 31 | 31 | 0 of 6 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 7 | 6 | 10 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 130 | 164 | 0 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 149 | 84 | 148 | 0 of 12 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 33 | 25 | 32 | 0 of 7 |
| finance_20261112 (daily_event) | $50 | 500 | none | 51 | 37 | 51 | 0 of 10 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 16 | 19 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 35 | 38 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 104 | 32 | 64 | 4 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 1,030 | 477 | 477 | 28 of 82 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 3 | 8 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 94 | 94 | 0 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 188 | 147 | 182 | 1 of 38 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 11 | 9 | 0 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 7 | 6 | 0 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 8 | 10 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 8 | 8 | 0 of 2 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 36 | 36 | 2 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 32 | 32 | 5 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 125 | 56 | 92 | 0 of 13 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 10 | 10 | 10 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 3 | 1 | 2 | 1 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 9 | 10 | 0 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 11 | 0 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 8 | 8 | 0 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 10 | 0 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 10 | 0 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 9 | 0 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 9 | 7 | 0 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 7 | 8 | 0 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 6 | 1 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 9 | 9 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,368 | 0 | 0 | 300 of 300 |
