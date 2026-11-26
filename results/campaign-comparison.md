# Official seven-day campaign results

Source: Project Statement, section 7.4, page 7. Master: master_release_v1; seed 41.
Five cases from the prescribed every-seventh tier samples, including L and traps 47/48.

| Case | Tier | Policy | Delivered value | Outbound travel cost | Unreachable days | Rescue value | Urgent mean wait |
|---|---|---|---:|---:|---:|---:|---:|
| 1-06 | S | optimized | 4631 | 388 | 2 | 2401 | 0.125 |
| 1-06 | S | baseline | 4574 | 388 | 2 | 2401 | 0.125 |
| 1-06 | S | simple | 4574 | 411 | 2 | 1988 | 2.375 |
| 1-26 | M | optimized | 13239 | 591 | 1 | 14880 | 0.172 |
| 1-26 | M | baseline | 13207 | 591 | 1 | 14880 | 0.172 |
| 1-26 | M | simple | 13207 | 888 | 1 | 12089 | 110.082 |
| 2-40 | L | optimized | 16871 | 13339 | 6 | 25008 | 0.075 |
| 2-40 | L | baseline | 16865 | 13339 | 6 | 25008 | 0.075 |
| 2-40 | L | simple | 16865 | 13339 | 6 | 19607 | 366.062 |
| 2-48 | X | optimized | 82113 | 61 | 2 | 27289 | 0.111 |
| 2-48 | X | baseline | 82090 | 61 | 2 | 27289 | 0.111 |
| 2-48 | X | simple | 82090 | 211 | 2 | 20951 | 375.993 |
| 4-47 | X | optimized | 1200 | 2490 | 1 | 13876 | 0.072 |
| 4-47 | X | baseline | 712 | 2490 | 1 | 13876 | 0.072 |
| 4-47 | X | simple | 712 | 2490 | 1 | 9108 | 387.299 |

## Deliberately difficult scenarios

Trap 47 (4-47), normal day: exact loading delivers 198; ratio greedy delivers 113 (57.071% of optimum). The DP handles the hostile weight/value combination, but its capacity-dependent memory/time remain a limitation.

Trap 48 (2-48), normal day: the cheapest route costs 12; the fewest-roads policy costs 64 (5.333 times as much). Dijkstra uses destination penalties and travel minutes, avoiding the hop-count trap. It cannot create a route when the flood disconnects the destination; those days explicitly skip the trip.

## Daily evidence and invariants

105 daily policy records: every recorded invariant passed. Exact Bellman-Ford distances, quadratic rescue totals, urgency-scan releases, Prim tree costs and memoized G results agree with the shipped methods on the same inputs. Greedy loading is a nonoptimal algorithm baseline; BFS/FIFO/value-greedy are additional simple policies.

Each case JSON under results/campaign/ contains the complete immutable base input once, the official calendar and all three runs. Each day includes the resolved target/waves, changed minutes/penalties, eligible crate/window ids, extra alarms, method choices, decisions and verified constraints. The base input plus these explicit changes reconstruct the full daily input. campaign-daily.csv provides the compact daily outcomes.

Assumptions made explicit: all daily changes apply afresh to base data; days 2–5 close only the listed wave, days 6–7 close their union. Zero-based wave positions are resolved in ascending stored wave-label order to support both 0-based and 1-based master groups. Daily stock resets; the statement specifies no consumption or expiry cutoff. Travel cost records the prescribed outbound route; no extra return leg is invented. Day 7 is counted as travel even though no load is permitted.

F/G run in the day-7 planning review; A/B/C/D interact daily. No aggregate score combines delivered value, travel cost, rescue value or urgency: they are separate objectives. These are deterministic correctness/quality runs, not timing experiments.

## Report artifacts

- campaign-daily.csv, campaign-summary.csv and campaign/*.json: tables and daily evidence.
- sample-outputs/campaign-official.txt: readable output from the program.
- plots/campaign-values.png, campaign-urgent-wait.png, campaign-difficult.png and captions-campaign.md.
- test-summary-BF.txt and fault-injection-BF.txt: automated evidence.
- The figures and tables are used in `report.pdf`; the frontend reads the same results through the backend API.
