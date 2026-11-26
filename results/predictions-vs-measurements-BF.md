# B/F predictions against measurements

Predictions were saved in a local commit before running; no absolute-time calibration was used.

| ID | Result | Evidence |
|---|---|---|
| BF1 | HIT | 867 route comparisons agree |
| BF2 | HIT | 289 forest comparisons agree |
| BF3 | HIT | min BFS/opt = 1.000 |
| BF4 | HIT | max BFS/opt = 20.000 |
| BF5 | HIT | Dijkstra operation exponent = 1.124 |
| BF6 | HIT | Kruskal operation exponent = 1.187 |
| BF7 | HIT | largest Bellman/Dijkstra time ratio = 1.417 |
| BF8 | HIT | 35 completed growth configurations |

8 of 8 predictions met the stated tolerance.
A miss remains a miss; the pre-run prediction was not rewritten.

## Round 2 (informed by round 1)

Historical round-1 outcomes remain in prediction_log.md and Git history. These are the new pre-run point predictions.

| Method | Metric | Prediction | Observed | Tolerance | Relative error | Result |
|---|---|---:|---:|---:|---:|---|
| dijkstra | time_s | 1.10 | 1.042 | +/- 0.35 | 5.570% | HIT |
| dijkstra | ops | 1.10 | 1.124 | +/- 0.35 | 2.120% | HIT |
| dijkstra | mem_bytes | 1.00 | 0.920 | +/- 0.35 | 8.644% | HIT |
| bellman | time_s | 1.10 | 1.111 | +/- 0.35 | 1.025% | HIT |
| bellman | ops | 1.10 | 1.197 | +/- 0.35 | 8.120% | HIT |
| bellman | mem_bytes | 1.00 | 0.920 | +/- 0.35 | 8.702% | HIT |
| bfs | time_s | 1.00 | 1.050 | +/- 0.35 | 4.777% | HIT |
| bfs | ops | 1.00 | 1.210 | +/- 0.35 | 17.388% | HIT |
| bfs | mem_bytes | 1.00 | 0.911 | +/- 0.35 | 9.768% | HIT |
| kruskal | time_s | 1.20 | 1.154 | +/- 0.35 | 3.988% | HIT |
| kruskal | ops | 1.20 | 1.187 | +/- 0.35 | 1.122% | HIT |
| kruskal | mem_bytes | 1.00 | 0.858 | +/- 0.35 | 16.613% | HIT |
| prim | time_s | 1.20 | 1.086 | +/- 0.35 | 10.489% | HIT |
| prim | ops | 1.20 | 1.158 | +/- 0.35 | 3.601% | HIT |
| prim | mem_bytes | 1.00 | 0.881 | +/- 0.35 | 13.539% | HIT |
