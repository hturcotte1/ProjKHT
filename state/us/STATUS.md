# Polymarket US recorder: 2026-11-13 07:17 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 9,140; showing any quote: 2,644
- order books recorded: 2,644, of which 2,182 have orders on both sides
- recorded markets with a twin on polymarket.com: 370; with a two-sided book there too: 315
- twins where the US price is the cheaper one by more than the US fee: 124 (43 on the "Yes" side, 81 on the "No" side)
- took 325 seconds; 0 errors

Taking every one of these at the best US price would cost $197,140, and the gaps add up to $788.77. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 99.0c | 27,769 | 0.2c / 0.3c | 0.6c | $168.26 | Next CEO of NVIDIA?: Nick Parker |
| No | 99.0c | 27,746 | 0.1c / 0.4c | 0.5c | $140.38 | Next CEO of NVIDIA?: Hock Tan |
| No | 99.0c | 27,774 | 0.3c / 0.6c | 0.3c | $84.97 | Next CEO of NVIDIA?: Matt Garman |
| No | 99.0c | 27,757 | 0.2c / 0.6c | 0.3c | $84.92 | Next CEO of NVIDIA?: Thomas Kurian |
| No | 99.0c | 62,072 | 0.4c / 0.8c | 0.1c | $65.77 | Best Chinese AI Company end of November?: MiniMax |
| No | 95.0c | 6,123 | 1.8c / 4.1c | 0.4c | $27.48 | TIME Person of the Year 2026: Jeremy Hansen |
| No | 99.0c | 4,330 | 0.2c / 0.5c | 0.4c | $17.58 | Next CEO of NVIDIA?: Spencer Huang |
| No | 13.0c | 126 | 70.0c / 75.0c | 10.9c | $13.81 | "GTA VI: The Album" First Week Sales?: 100k+ |
| No | 94.0c | 265 | 0.5c / 0.6c | 4.9c | $12.90 | Best Chinese AI Company end of November?: DeepSeek |
| Yes | 3.0c | 706 | 5.0c / 6.0c | 1.7c | $12.16 | Next CEO of NVIDIA?: Tim Cook |
| No | 99.0c | 2,709 | 0.2c / 0.5c | 0.4c | $11.00 | Next CEO of NVIDIA?: Pat Gelsinger |
| No | 99.0c | 2,662 | 0.3c / 0.5c | 0.4c | $10.81 | Dancing With The Stars S35 Winner: Maura Higgins |
| No | 90.0c | 528 | 7.0c / 7.1c | 2.0c | $10.79 | TIME Person of the Year 2026: Benjamin Netanyahu |
| No | 23.9c | 2,722 | 73.0c / 74.0c | 0.4c | $10.13 | 2028 Presidential Election: Alaska Winner: Republican Party |
| No | 31.6c | 2,145 | 65.0c / 66.0c | 0.3c | $7.43 | 2028 Presidential Election: Ohio Winner: Republican Party |
| No | 36.0c | 224 | 58.0c / 59.0c | 2.8c | $6.29 | 2027 Louisiana Governor Election Winner: Republican Party |
| No | 16.0c | 39 | 65.0c / 67.0c | 15.7c | $6.11 | US Birth Rate in 2026? (Per 1000 Women): 52.0+ |
| No | 99.0c | 845 | 0.1c / 0.2c | 0.7c | $5.96 | Argentina Presidential Election Winner: Esteban Bullrich |
| Yes | 29.8c | 107 | 36.3c / 36.4c | 4.5c | $4.84 | 2028 Presidential Election: Georgia Winner: Republican Party |
| Yes | 11.0c | 372 | 13.2c / 13.5c | 1.3c | $4.73 | Argentina Presidential Election Winner: Sergio Massa |
| No | 99.0c | 596 | 0.1c / 0.2c | 0.7c | $4.21 | Argentina Presidential Election Winner: Facundo Manes |
| Yes | 2.0c | 685 | 2.8c / 2.9c | 0.6c | $4.21 | Next CEO of NVIDIA?: Jay Puri |
| Yes | 60.5c | 1,631 | 63.0c / 64.0c | 0.2c | $3.75 | 2028 Presidential Election: Arizona Winner: Democratic Party |
| Yes | 61.0c | 60 | 69.0c / 71.0c | 5.7c | $3.45 | 2028 Presidential Election: Michigan Winner: Democratic Party |
| No | 66.0c | 367 | 28.0c / 31.0c | 0.9c | $3.19 | 2027 Mississippi Governor Election Winner: Democratic Party |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 177 | 164 | 177 | 0 of 9 |
| kpic_20261107 (daily) | $250 | 2,000 | 4c | 20 | 0 | 0 | 5 of 5 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 30 | 18 | 20 | 0 of 5 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 33 | 24 | 31 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 9 | 9 | 9 | 0 of 3 |
| finance_nvda_nextceo_20261112 (daily_event) | $200 | 1,000 | none | 23 | 23 | 23 | 0 of 1 |
| climate_20260924 (live) | $185 | 7,500 | none | 72 | 1 | 13 | 8 of 12 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 180 | 86 | 64 | 1 of 21 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 140 | 88 | 139 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 45 | 24 | 35 | 0 of 8 |
| finance_20261112 (daily_event) | $50 | 500 | none | 64 | 56 | 62 | 0 of 13 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 15 | 18 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 34 | 37 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 103 | 44 | 70 | 3 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 861 | 152 | 152 | 37 of 65 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 1 | 1 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 98 | 31 | 31 | 33 of 49 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 151 | 102 | 135 | 4 of 36 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 107 | 2 | 2 | 4 of 6 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 0 | 0 | 11 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 118 | 24 | 20 | 5 of 13 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 7 | 7 | 7 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 4 | 2 | 0 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,992 | 0 | 0 | 385 of 385 |
