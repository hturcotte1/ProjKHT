# Polymarket US recorder: 2026-11-13 00:26 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 9,238; showing any quote: 2,808
- order books recorded: 2,781, of which 2,239 have orders on both sides
- recorded markets with a twin on polymarket.com: 360; with a two-sided book there too: 328
- twins where the US price is the cheaper one by more than the US fee: 131 (44 on the "Yes" side, 87 on the "No" side)
- took 326 seconds; 0 errors

Taking every one of these at the best US price would cost $1,133,847, and the gaps add up to $30,222.52. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 91.0c | 526,610 | 4.1c / 4.6c | 3.6c | $19,073.56 | Prime Minister of Israel After the Next Election: Avigdor Lieberman |
| No | 94.0c | 513,782 | 3.3c / 3.4c | 2.1c | $10,605.49 | Prime Minister of Israel After the Next Election: Naftali Bennett |
| No | 99.0c | 20,685 | 0.1c / 0.5c | 0.4c | $83.97 | Next CEO of NVIDIA?: Pat Gelsinger |
| No | 99.0c | 20,979 | 0.2c / 0.6c | 0.3c | $64.18 | Next CEO of NVIDIA?: Jonah Alben |
| No | 99.0c | 20,688 | 0.1c / 0.6c | 0.3c | $63.29 | Next CEO of NVIDIA?: Matt Garman |
| No | 99.0c | 20,293 | 0.2c / 0.6c | 0.3c | $62.09 | Next CEO of NVIDIA?: Spencer Huang |
| No | 99.0c | 20,292 | 0.1c / 0.6c | 0.3c | $62.08 | Next CEO of NVIDIA?: Hock Tan |
| No | 99.0c | 53,068 | 0.4c / 0.8c | 0.1c | $56.23 | Best Chinese AI Company end of November?: MiniMax |
| No | 55.0c | 37 | 0.1c / 1.5c | 41.1c | $15.23 | AL-07 House Election Margin of Victory: Democrat 30-35% |
| No | 94.0c | 263 | 0.5c / 0.6c | 4.9c | $12.79 | Best Chinese AI Company end of November?: DeepSeek |
| No | 95.0c | 2,516 | 2.0c / 4.1c | 0.4c | $11.29 | TIME Person of the Year 2026: Jeremy Hansen |
| No | 23.9c | 2,596 | 73.0c / 74.0c | 0.4c | $9.66 | 2028 Presidential Election: Alaska Winner: Republican Party |
| No | 99.0c | 1,589 | 0.3c / 0.5c | 0.4c | $6.45 | Dancing With The Stars S35 Winner: Maura Higgins |
| Yes | 11.0c | 372 | 13.6c / 13.7c | 1.7c | $6.21 | Argentina Presidential Election Winner: Sergio Massa |
| No | 92.0c | 2,830 | 6.9c / 7.1c | 0.2c | $5.68 | TIME Person of the Year 2026: Benjamin Netanyahu |
| Yes | 29.8c | 120 | 36.3c / 36.4c | 4.5c | $5.39 | 2028 Presidential Election: Georgia Winner: Republican Party |
| No | 99.0c | 841 | 0.1c / 0.3c | 0.6c | $5.09 | Argentina Presidential Election Winner: Esteban Bullrich |
| No | 16.0c | 30 | 65.0c / 67.0c | 15.7c | $4.77 | US Birth Rate in 2026? (Per 1000 Women): 52.0+ |
| No | 99.0c | 596 | 0.1c / 0.2c | 0.7c | $4.21 | Argentina Presidential Election Winner: Facundo Manes |
| No | 81.0c | 85 | 11.0c / 13.0c | 4.5c | $3.88 | 2027 Minnesota Senate Special Election Winner: Republican Party |
| Yes | 60.5c | 1,632 | 63.0c / 64.0c | 0.2c | $3.75 | 2028 Presidential Election: Arizona Winner: Democratic Party |
| No | 99.0c | 451 | 0.1c / 0.2c | 0.7c | $3.18 | Argentina Presidential Election Winner: Juan Grabois |
| No | 96.0c | 478 | 2.0c / 3.0c | 0.6c | $3.04 | Best Chinese AI Company end of November?: Tencent |
| No | 66.0c | 285 | 28.0c / 31.0c | 0.9c | $2.48 | 2027 Mississippi Governor Election Winner: Democratic Party |
| Yes | 61.0c | 41 | 69.0c / 71.0c | 5.7c | $2.35 | 2028 Presidential Election: Michigan Winner: Democratic Party |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 177 | 163 | 177 | 0 of 9 |
| kpic_20261107 (daily) | $250 | 2,000 | 4c | 20 | 0 | 0 | 5 of 5 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 30 | 18 | 20 | 0 of 5 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 33 | 23 | 31 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 9 | 8 | 8 | 0 of 3 |
| finance_nvda_nextceo_20261112 (daily_event) | $200 | 1,000 | none | 23 | 23 | 23 | 0 of 1 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 3 | 23 | 10 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 180 | 90 | 63 | 1 of 21 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 140 | 87 | 139 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 45 | 27 | 31 | 0 of 8 |
| finance_20261112 (daily_event) | $50 | 500 | none | 64 | 54 | 63 | 0 of 13 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 15 | 18 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 32 | 37 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 103 | 43 | 70 | 3 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 861 | 133 | 133 | 38 of 65 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 2 | 1 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 98 | 31 | 31 | 33 of 49 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 151 | 103 | 133 | 4 of 36 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 2 | 2 | 6 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 0 | 0 | 11 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 135 | 25 | 30 | 5 of 14 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 7 | 7 | 7 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 4 | 2 | 1 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,992 | 0 | 0 | 385 of 385 |
