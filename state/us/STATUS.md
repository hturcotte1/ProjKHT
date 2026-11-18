# Polymarket US recorder: 2026-11-18 03:18 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 9,083; showing any quote: 3,151
- order books recorded: 3,140, of which 2,402 have orders on both sides
- recorded markets with a twin on polymarket.com: 397; with a two-sided book there too: 355
- twins where the US price is the cheaper one by more than the US fee: 120 (53 on the "Yes" side, 67 on the "No" side)
- took 339 seconds; 0 errors

Taking every one of these at the best US price would cost $131,802, and the gaps add up to $898.67. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| Yes | 3.0c | 41,700 | 4.1c / 4.3c | 0.8c | $343.42 | Next CEO of NVIDIA?: Tim Cook |
| Yes | 21.0c | 6,805 | 24.1c / 24.9c | 1.5c | $103.70 | Prime Minister of Israel After the Next Election: Benjamin Netanyahu |
| No | 98.0c | 23,921 | 1.1c / 1.4c | 0.4c | $98.99 | Next CEO of NVIDIA?: Lisa Su |
| No | 95.0c | 8,803 | 3.7c / 3.8c | 0.7c | $65.91 | Fed Decision in December: 50+ bps Increase |
| Yes | 92.0c | 16,351 | 93.0c / 94.0c | 0.3c | $49.18 | Fed Decision in December: 25 bps Increase |
| No | 61.7c | 770 | 29.0c / 31.0c | 5.1c | $38.90 | 2028 Presidential Election: North Carolina Winner: Republican Party |
| No | 96.0c | 5,283 | 1.9c / 2.9c | 0.7c | $38.84 | TIME Person of the Year 2026: Mojtaba Khamenei |
| Yes | 60.1c | 787 | 67.0c / 68.0c | 4.6c | $36.35 | 2028 Presidential Election: North Carolina Winner: Democratic Party |
| Yes | 5.0c | 9,098 | 5.6c / 5.7c | 0.1c | $13.53 | Next CEO of NVIDIA?: Nikesh Arora |
| No | 36.0c | 273 | 58.0c / 59.0c | 2.8c | $7.67 | 2027 Louisiana Governor Election Winner: Republican Party |
| Yes | 95.0c | 698 | 96.5c / 97.7c | 1.0c | $7.32 | "GTA VI: The Album" First Week Sales?: 50k+ |
| No | 6.3c | 99 | 86.0c / 87.0c | 6.1c | $6.08 | 2028 Presidential Election: New York Winner: Democratic Party |
| No | 99.0c | 845 | 0.2c / 0.3c | 0.6c | $5.12 | Argentina Presidential Election Winner: Esteban Bullrich |
| No | 10.1c | 99 | 83.0c / 84.0c | 5.0c | $4.99 | 2028 Presidential Election: Louisiana Winner: Republican Party |
| No | 99.0c | 809 | 0.1c / 0.3c | 0.6c | $4.90 | Argentina Presidential Election Winner: Juan Schiaretti |
| No | 22.6c | 85 | 68.0c / 70.0c | 5.7c | $4.89 | 2028 Presidential Election: Iowa Winner: Republican Party |
| No | 99.0c | 596 | 0.1c / 0.2c | 0.7c | $4.21 | Argentina Presidential Election Winner: Facundo Manes |
| No | 99.0c | 70,483 | 0.3c / 0.9c | 0.0c | $4.19 | Best Chinese AI Company end of November?: MiniMax |
| Yes | 10.0c | 83 | 15.6c / 15.7c | 4.7c | $3.96 | Argentina Presidential Election Winner: Sergio Massa |
| Yes | 24.0c | 73 | 31.0c / 32.0c | 5.3c | $3.83 | 2028 Presidential Election: Iowa Winner: Democratic Party |
| Yes | 61.1c | 65 | 69.0c / 70.0c | 5.6c | $3.66 | 2028 Presidential Election: Michigan Winner: Democratic Party |
| Yes | 2.0c | 400 | 3.1c / 3.8c | 0.9c | $3.65 | Best Chinese AI Company end of November?: Z.ai |
| No | 22.5c | 124 | 72.0c / 73.0c | 2.8c | $3.53 | 2028 Presidential Election: Alaska Winner: Republican Party |
| Yes | 31.0c | 56 | 39.0c / 41.0c | 6.0c | $3.34 | 2027 Louisiana Governor Election Winner: Democratic Party |
| No | 99.0c | 451 | 0.1c / 0.2c | 0.7c | $3.18 | Argentina Presidential Election Winner: Juan Grabois |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 189 | 202 | 0 of 10 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 27 | 16 | 16 | 1 of 9 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 30 | 11 | 18 | 2 of 5 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 36 | 27 | 33 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 9 | 9 | 9 | 0 of 3 |
| finance_nvda_nextceo_20261112 (daily_event) | $200 | 1,000 | none | 27 | 11 | 27 | 0 of 2 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 1 | 19 | 9 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 101 | 62 | 0 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 140 | 88 | 139 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 45 | 26 | 30 | 1 of 8 |
| finance_20261112 (daily_event) | $50 | 500 | none | 55 | 47 | 51 | 0 of 11 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 15 | 18 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 34 | 36 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 102 | 40 | 70 | 3 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 864 | 240 | 240 | 28 of 65 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 1 | 0 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 16 | 16 | 40 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 194 | 145 | 178 | 2 of 41 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 5 | 6 | 1 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 5 | 6 | 1 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 8 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 6 | 6 | 1 of 2 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 1 | 1 | 6 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 4 | 4 | 7 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 139 | 41 | 79 | 1 of 14 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 7 | 7 | 7 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 4 | 2 | 1 | 0 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 12 | 12 | 0 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 4 | 6 | 1 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 4 | 6 | 1 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 4 | 6 | 1 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 12 | 12 | 0 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 12 | 12 | 0 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 12 | 12 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,783 | 0 | 0 | 355 of 355 |
