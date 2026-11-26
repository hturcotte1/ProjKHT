# Polymarket US recorder: 2026-11-26 12:56 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 8,671; showing any quote: 3,637
- order books recorded: 3,633, of which 2,471 have orders on both sides
- recorded markets with a twin on polymarket.com: 342; with a two-sided book there too: 319
- twins where the US price is the cheaper one by more than the US fee: 65 (40 on the "Yes" side, 25 on the "No" side)
- took 423 seconds; 0 errors

Taking every one of these at the best US price would cost $32,440, and the gaps add up to $304.64. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 97.0c | 8,827 | 2.1c / 2.2c | 0.5c | $42.36 | Fed Decision in December: 50+ bps Increase |
| No | 99.0c | 6,778 | 0.2c / 0.3c | 0.6c | $40.07 | Argentina Presidential Election Winner: Esteban Bullrich |
| Yes | 29.4c | 1,631 | 34.0c / 35.0c | 2.3c | $37.78 | 2028 Presidential Election: Iowa Winner: Democratic Party |
| Yes | 1.0c | 2,591 | 1.8c / 3.5c | 0.7c | $17.91 | TIME Person of the Year 2026: Shehbaz Sharif |
| Yes | 98.0c | 4,637 | 98.5c / 99.7c | 0.3c | $13.19 | "GTA VI" Metacritic Score?: 99+ |
| Yes | 1.0c | 6,757 | 1.3c / 2.0c | 0.2c | $12.91 | TIME Person of the Year 2026: Jerome Powell |
| Yes | 29.9c | 403 | 35.0c / 36.0c | 2.8c | $11.27 | 2028 Presidential Election: Wisconsin Winner: Republican Party |
| Yes | 7.2c | 514 | 10.0c / 11.0c | 2.1c | $10.61 | 2028 Presidential Election: Tennessee Winner: Democratic Party |
| No | 97.0c | 1,558 | 2.0c / 2.1c | 0.6c | $9.04 | Prime Minister of Israel After the Next Election: Avigdor Lieberman |
| No | 93.0c | 2,596 | 5.0c / 6.0c | 0.3c | $7.37 | TIME Person of the Year 2026: Pope Leo XIV |
| Yes | 1.0c | 1,430 | 1.6c / 2.0c | 0.5c | $7.02 | Best Chinese AI Company end of November?: Tencent |
| Yes | 12.0c | 463 | 14.3c / 14.4c | 1.1c | $5.27 | Argentina Presidential Election Winner: Sergio Massa |
| Yes | 9.0c | 471 | 11.0c / 12.0c | 1.1c | $5.18 | 2028 Presidential Election: Kentucky Winner: Democratic Party |
| No | 10.8c | 451 | 82.0c / 87.0c | 1.1c | $5.14 | 2028 Presidential Election: Utah Winner: Republican Party |
| Yes | 4.0c | 88 | 10.0c / 52.0c | 5.6c | $4.89 | 2027 Minnesota Senate Republican Nominee: Harry Niska |
| No | 8.8c | 182 | 87.0c / 88.0c | 2.3c | $4.21 | 2028 Presidential Election: New York Winner: Democratic Party |
| No | 99.0c | 596 | 0.1c / 0.2c | 0.7c | $4.12 | Argentina Presidential Election Winner: Facundo Manes |
| No | 96.0c | 5,221 | 3.4c / 3.5c | 0.1c | $4.05 | TIME Person of the Year 2026: Artificial Intelligence |
| No | 4.8c | 76 | 89.0c / 90.0c | 4.7c | $3.59 | 2028 Presidential Election: Idaho Winner: Republican Party |
| Yes | 31.6c | 839 | 34.4c / 34.5c | 0.4c | $3.54 | 2028 Presidential Election: Georgia Winner: Republican Party |
| No | 10.8c | 2,460 | 87.0c / 88.0c | 0.1c | $3.45 | 2028 Presidential Election: Alabama Winner: Republican Party |
| No | 99.0c | 435 | 0.1c / 0.2c | 0.7c | $3.01 | Argentina Presidential Election Winner: Juan Grabois |
| Yes | 3.0c | 426 | 4.0c / 7.0c | 0.7c | $2.90 | 2028 Presidential Election: Rhode Island Winner: Republican Party |
| Yes | 7.5c | 75 | 12.0c / 13.0c | 3.7c | $2.81 | 2028 Presidential Election: Louisiana Winner: Democratic Party |
| No | 3.8c | 97 | 92.0c / 93.0c | 2.8c | $2.71 | 2028 Presidential Election: Massachusetts Winner: Democratic Party |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 183 | 202 | 0 of 10 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 108 | 56 | 56 | 3 of 27 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 37 | 15 | 33 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 32 | 28 | 31 | 0 of 6 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 4 | 1 | 12 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 109 | 77 | 0 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 149 | 83 | 146 | 0 of 12 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 33 | 24 | 26 | 0 of 7 |
| finance_20261112 (daily_event) | $50 | 500 | none | 51 | 38 | 51 | 0 of 10 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 10 | 14 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 32 | 28 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 104 | 31 | 64 | 4 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 1,030 | 440 | 440 | 30 of 82 |
| energy_wti_up_down_1h_20261121 (daily_event) | $30 | 1,500 | 3c | 1 | 0 | 0 | 1 of 1 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 0 | 1 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 72 | 72 | 10 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 188 | 141 | 177 | 2 of 38 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 6 | 1 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 6 | 1 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 7 | 10 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 7 | 7 | 0 of 2 |
| energy_natgas_up_down_1h_20261121 (daily_event) | $15 | 750 | 3c | 1 | 0 | 0 | 1 of 1 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 1 | 1 | 6 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 16 | 16 | 9 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 122 | 30 | 70 | 3 of 13 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 10 | 10 | 10 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 3 | 1 | 1 | 1 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 6 | 1 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 6 | 1 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 6 | 1 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 6 | 1 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 6 | 1 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 8 | 6 | 0 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 6 | 1 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 6 | 1 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 6 | 1 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 6 | 6 | 1 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,226 | 0 | 0 | 283 of 283 |
