# Polymarket US recorder: 2026-11-24 06:11 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 8,879; showing any quote: 3,641
- order books recorded: 3,637, of which 2,565 have orders on both sides
- recorded markets with a twin on polymarket.com: 373; with a two-sided book there too: 345
- twins where the US price is the cheaper one by more than the US fee: 77 (35 on the "Yes" side, 42 on the "No" side)
- took 376 seconds; 0 errors

Taking every one of these at the best US price would cost $114,295, and the gaps add up to $676.19. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 99.0c | 12,782 | 0.1c / 0.2c | 0.7c | $90.24 | Argentina Presidential Election Winner: Juan Grabois |
| No | 99.0c | 16,778 | 0.2c / 0.4c | 0.5c | $84.89 | Argentina Presidential Election Winner: Victoria Villarruel |
| No | 99.0c | 11,673 | 0.1c / 0.3c | 0.6c | $70.74 | Argentina Presidential Election Winner: Juan Schiaretti |
| No | 99.0c | 9,192 | 0.1c / 0.2c | 0.7c | $64.89 | Argentina Presidential Election Winner: Facundo Manes |
| No | 96.0c | 22,337 | 3.2c / 3.4c | 0.2c | $52.54 | Fed Decision in December: No Change |
| No | 96.0c | 10,625 | 3.0c / 3.2c | 0.4c | $46.24 | Fed Decision in December: 50+ bps Increase |
| Yes | 24.0c | 2,860 | 27.1c / 27.7c | 1.4c | $39.10 | TIME Person of the Year 2026: James Talarico |
| Yes | 7.7c | 2,377 | 10.0c / 11.0c | 1.6c | $38.63 | 2028 Presidential Election: Tennessee Winner: Democratic Party |
| Yes | 95.0c | 13,858 | 95.7c / 96.3c | 0.2c | $34.47 | Another Fed Rate Hike in 2026?: Hike |
| No | 99.0c | 11,428 | 0.3c / 0.7c | 0.2c | $23.54 | Argentina Presidential Election Winner: Dante Gebel |
| No | 10.7c | 2,510 | 87.0c / 88.0c | 0.4c | $9.84 | 2028 Presidential Election: Alabama Winner: Republican Party |
| Yes | 11.0c | 395 | 14.3c / 14.4c | 2.4c | $9.37 | Argentina Presidential Election Winner: Sergio Massa |
| Yes | 4.9c | 129 | 10.2c / 10.5c | 4.9c | $6.24 | 2028 Presidential Election: Maryland Winner: Republican Party |
| No | 96.0c | 1,812 | 2.3c / 3.3c | 0.3c | $6.07 | TIME Person of the Year 2026: Jeremy Hansen |
| Yes | 5.1c | 249 | 8.0c / 9.0c | 2.4c | $6.06 | 2028 Presidential Election: Washington Winner: Republican Party |
| Yes | 1.0c | 1,466 | 1.5c / 1.8c | 0.4c | $5.95 | Best Chinese AI Company end of November?: Tencent |
| No | 5.7c | 146 | 89.0c / 90.0c | 3.8c | $5.53 | 2028 Presidential Election: Maryland Winner: Democratic Party |
| No | 5.4c | 255 | 91.0c / 92.0c | 2.1c | $5.40 | 2028 Presidential Election: Washington Winner: Democratic Party |
| Yes | 3.0c | 69 | 11.0c / 29.0c | 7.7c | $5.35 | 2027 Minnesota Senate Democratic Nominee: John Hoffman |
| No | 10.4c | 99 | 83.0c / 84.0c | 4.7c | $4.67 | 2028 Presidential Election: Louisiana Winner: Republican Party |
| No | 37.0c | 232 | 58.0c / 59.0c | 1.8c | $4.14 | 2027 Louisiana Governor Election Winner: Republican Party |
| No | 66.6c | 1,389 | 30.0c / 31.0c | 0.3c | $3.98 | 2028 Presidential Election: North Carolina Winner: Republican Party |
| Yes | 25.0c | 72 | 32.0c / 35.0c | 5.2c | $3.76 | Best Chinese AI Company end of November?: Alibaba |
| No | 43.0c | 110 | 51.0c / 52.0c | 2.7c | $2.93 | 2027 Mississippi Governor Election Winner: Republican Party |
| Yes | 5.0c | 80 | 9.0c / 68.0c | 3.5c | $2.83 | 2027 Minnesota Senate Republican Nominee: Brad Finstad |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| energy_wti_up_down_1d_20261121 (daily_event) | $500 | 2,500 | 3c | 1 | 1 | 1 | 0 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 202 | 185 | 202 | 0 of 10 |
| energy_natgas_up_down_1d_20261121 (daily_event) | $250 | 1,250 | 3c | 1 | 1 | 1 | 0 of 1 |
| kpic_20261116 (daily_event) | $250 | 500 | 6c | 55 | 18 | 18 | 6 of 16 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 15 | 15 | 15 | 0 of 3 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 37 | 23 | 35 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 32 | 22 | 23 | 1 of 6 |
| climate_20260924 (live) | $185 | 7,500 | none | 78 | 4 | 12 | 8 of 13 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 178 | 136 | 139 | 0 of 20 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 149 | 89 | 148 | 0 of 12 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 33 | 25 | 32 | 0 of 7 |
| finance_20261112 (daily_event) | $50 | 500 | none | 51 | 47 | 51 | 0 of 10 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 16 | 19 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 34 | 37 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 104 | 32 | 64 | 4 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 1,023 | 506 | 506 | 28 of 82 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 1 | 7 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 100 | 78 | 78 | 3 of 50 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 187 | 146 | 179 | 0 of 38 |
| mandeb_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 5 | 4 | 0 of 2 |
| mandeb_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 11 | 2 | 0 of 2 |
| hormuz_peak_day_20261116 (daily_event) | $17 | 2,500 | none | 12 | 9 | 8 | 0 of 2 |
| hormuz_weekly_20261116 (daily_event) | $17 | 2,500 | none | 12 | 4 | 7 | 0 of 2 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 107 | 32 | 32 | 2 of 6 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 22 | 22 | 5 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 108 | 45 | 77 | 1 of 12 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 10 | 10 | 10 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 3 | 3 | 2 | 0 of 2 |
| mandeb_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 9 | 0 of 2 |
| mandeb_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 7 | 8 | 0 of 2 |
| hormuz_7dma_monthend_20261116 (daily_event) | $8 | 1,500 | none | 12 | 10 | 6 | 0 of 2 |
| hormuz_7dma_high_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 9 | 0 of 2 |
| malacca_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 5 | 0 | 1 of 2 |
| panama_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 5 | 2 | 1 of 2 |
| suez_weekly_20261116 (daily_event) | $8 | 1,500 | none | 12 | 6 | 1 | 0 of 2 |
| mandeb_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| hormuz_zero_20261116 (daily_event) | $3 | 1,000 | none | 1 | 1 | 1 | 0 of 1 |
| malacca_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 11 | 7 | 0 of 2 |
| panama_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 10 | 6 | 0 of 2 |
| suez_7dma_monthend_20261116 (daily_event) | $3 | 1,000 | none | 12 | 12 | 8 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,370 | 0 | 0 | 301 of 301 |
