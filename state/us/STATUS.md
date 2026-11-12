# Polymarket US recorder: 2026-11-12 19:08 UTC

Read-only. No orders are placed and no key is used. What this is for: docs/06_polymarket_us.md, section 8.

- open markets outside sports and crypto: 9,269; showing any quote: 2,601
- order books recorded: 2,601, of which 2,192 have orders on both sides
- recorded markets with a twin on polymarket.com: 336; with a two-sided book there too: 301
- twins where the US price is the cheaper one by more than the US fee: 115 (42 on the "Yes" side, 73 on the "No" side)
- took 313 seconds; 0 errors

Taking every one of these at the best US price would cost $1,317,723, and the gaps add up to $28,386.65. A gap is not a profit. On the history that exists, taking gaps like these lost money (docs/07_two_venues.md, section 4); they are recorded for the forward test fixed there.

The 25 largest by what the gap is worth at the size on offer:

| Buy on US | at | contracts there | polymarket.com bid / ask | gap after fee | gap x size | market |
|---|---:|---:|---:|---:|---:|---|
| No | 91.0c | 666,807 | 4.6c / 5.2c | 3.0c | $20,150.56 | Prime Minister of Israel After the Next Election: Avigdor Lieberman |
| No | 94.0c | 687,167 | 3.8c / 4.3c | 1.2c | $8,000.00 | Prime Minister of Israel After the Next Election: Naftali Bennett |
| No | 99.0c | 53,068 | 0.4c / 0.8c | 0.1c | $56.23 | Best Chinese AI Company end of November?: MiniMax |
| No | 1.0c | 31,025 | 98.1c / 98.8c | 0.1c | $32.87 | AK-AL House Election Winner: Republican Party |
| No | 81.0c | 269 | 11.0c / 13.0c | 4.5c | $12.19 | 2027 Minnesota Senate Special Election Winner: Republican Party |
| No | 66.0c | 378 | 28.0c / 29.0c | 2.9c | $10.85 | 2027 Mississippi Governor Election Winner: Democratic Party |
| No | 23.9c | 2,594 | 72.0c / 74.0c | 0.4c | $9.65 | 2028 Presidential Election: Alaska Winner: Republican Party |
| No | 94.0c | 198 | 0.5c / 0.6c | 4.9c | $9.62 | Best Chinese AI Company end of November?: DeepSeek |
| Yes | 11.0c | 372 | 13.6c / 13.7c | 1.7c | $6.21 | Argentina Presidential Election Winner: Sergio Massa |
| No | 99.0c | 1,394 | 0.3c / 0.5c | 0.4c | $5.66 | Dancing With The Stars S35 Winner: Maura Higgins |
| Yes | 29.8c | 123 | 36.3c / 36.4c | 4.5c | $5.55 | 2028 Presidential Election: Georgia Winner: Republican Party |
| No | 99.0c | 848 | 0.1c / 0.3c | 0.6c | $5.14 | Argentina Presidential Election Winner: Esteban Bullrich |
| No | 16.0c | 31 | 65.0c / 67.0c | 15.7c | $4.84 | US Birth Rate in 2026? (Per 1000 Women): 52.0+ |
| No | 81.6c | 229 | 14.0c / 15.0c | 2.0c | $4.52 | 2028 Presidential Election: Minnesota Winner: Republican Party |
| No | 99.0c | 596 | 0.1c / 0.2c | 0.7c | $4.21 | Argentina Presidential Election Winner: Facundo Manes |
| Yes | 60.5c | 1,631 | 63.0c / 64.0c | 0.2c | $3.75 | 2028 Presidential Election: Arizona Winner: Democratic Party |
| No | 98.0c | 1,150 | 1.4c / 1.5c | 0.3c | $3.61 | Fed Decision in December: No Change |
| No | 99.0c | 459 | 0.1c / 0.2c | 0.7c | $3.24 | Argentina Presidential Election Winner: Juan Grabois |
| No | 13.0c | 73 | 75.0c / 82.0c | 3.9c | $2.88 | "GTA VI: The Album" First Week Sales?: 100k+ |
| No | 36.0c | 140 | 58.0c / 60.0c | 1.8c | $2.53 | 2027 Louisiana Governor Election Winner: Republican Party |
| Yes | 61.0c | 42 | 69.0c / 71.0c | 5.7c | $2.43 | 2028 Presidential Election: Michigan Winner: Democratic Party |
| Yes | 82.2c | 568 | 84.0c / 86.0c | 0.4c | $2.33 | 2028 Presidential Election: Minnesota Winner: Democratic Party |
| No | 2.0c | 66 | 92.5c / 94.3c | 3.5c | $2.32 | "GTA VI: The Album" First Week Sales?: 50k+ |
| No | 99.0c | 343 | 0.1c / 0.3c | 0.6c | $2.08 | Argentina Presidential Election Winner: Juan Schiaretti |
| Yes | 82.0c | 76 | 86.0c / 89.0c | 2.6c | $1.98 | 2027 Minnesota Senate Special Election Winner: Democratic Party |

## Rewards for resting orders

Polymarket US pays people to leave orders near the best price (docs/08_rewards.md). A programme's pool is shared across all its markets. A side of a book is paid only while it holds the target size, and in programmes with a maximum spread only while both sides do, close together. This is how many would have been paid at the moment of this cycle.

| Programme | Pool | Target size | Max spread | Markets | Bid sides paid | Ask sides paid | Events with nobody paid |
|---|---:|---:|---:|---:|---:|---:|---:|
| metals_gold_updown_1d_20261110 (daily_event) | $1,000 | 5,000 | 3c | 1 | 1 | 1 | 0 of 1 |
| metals_silver_updown_1d_20261110 (daily_event) | $750 | 3,000 | 3c | 1 | 0 | 0 | 1 of 1 |
| presidential_election_20261028 (daily_event) | $500 | 20,000 | none | 177 | 164 | 177 | 0 of 9 |
| kpic_20261107 (daily) | $250 | 2,000 | 4c | 28 | 0 | 0 | 7 of 7 |
| dancing_with_the_stars_20260924 (live) | $250 | 500 | none | 30 | 18 | 20 | 1 of 5 |
| politics_high_20261031 (daily_event) | $225 | 10,000 | none | 33 | 24 | 31 | 0 of 2 |
| finance_nvda_jenhua_20261112 (daily_event) | $200 | 2,500 | none | 9 | 9 | 9 | 0 of 3 |
| finance_nvda_nextceo_20261112 (daily_event) | $200 | 1,000 | none | 23 | 8 | 8 | 0 of 1 |
| climate_20260924 (live) | $185 | 7,500 | none | 90 | 1 | 15 | 11 of 15 |
| finance_nvda_kimpow_20261112 (daily_event) | $100 | 500 | none | 2 | 2 | 2 | 0 of 1 |
| politics_mid_20261109 (daily_event) | $75 | 5,000 | none | 180 | 64 | 51 | 1 of 21 |
| culture_high_20260924 (daily_event) | $75 | 500 | none | 140 | 88 | 138 | 0 of 11 |
| macro_high_20260924 (daily_event) | $75 | 5,000 | none | 45 | 24 | 24 | 0 of 8 |
| finance_20261112 (daily_event) | $50 | 500 | none | 64 | 58 | 62 | 0 of 13 |
| climate_politics_science_strategic_20261013 (daily_event) | $50 | 3,000 | none | 19 | 15 | 17 | 0 of 5 |
| macro_strategic_20261012 (daily_event) | $50 | 3,000 | none | 39 | 31 | 38 | 0 of 11 |
| technology_20260924 (daily_event) | $50 | 1,000 | none | 103 | 43 | 68 | 3 of 13 |
| culture_low_20260924_v2 (daily_event) | $40 | 500 | 6c | 861 | 134 | 134 | 35 of 65 |
| politics_trump_approval_weekly_20261019 (daily_event) | $30 | 2,000 | none | 8 | 2 | 1 | 0 of 1 |
| presidential_2028_state_winners_20261028 (daily_event) | $25 | 2,000 | 5c | 98 | 31 | 31 | 33 of 49 |
| politics_low_20261031 (daily_event) | $20 | 2,000 | none | 152 | 105 | 135 | 3 of 37 |
| diesel_day_week_month_20261110 (daily_event) | $15 | 500 | 6c | 128 | 0 | 0 | 7 of 7 |
| gas_state_20261110 (daily_event) | $15 | 500 | 6c | 98 | 0 | 0 | 11 of 11 |
| macro_low_20260924 (daily_event) | $15 | 5,000 | none | 135 | 24 | 25 | 5 of 14 |
| geopolitics_20260924 (daily_event) | $15 | 2,000 | none | 7 | 7 | 7 | 0 of 2 |
| science_20260924 (daily_event) | $10 | 10,000 | none | 4 | 2 | 0 | 0 of 2 |
| politics_t4_coverage_20261103 (daily_event) | $2 | 2,000 | 6c | 2,992 | 0 | 0 | 385 of 385 |
