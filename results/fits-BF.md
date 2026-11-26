# B/F growth fits

Source: master_release_v1, case 10-40; connected BFS prefixes; no networks pooled.
Fits include changing edge density and validation/output construction. They describe this input family only.

| Module | Method | Metric | Exponent | 95% half-width | R² | Sizes |
|---|---|---|---:|---:|---:|---:|
| B | dijkstra | time_s | 1.042 | 0.021 | 0.9997 | 7 |
| B | dijkstra | ops | 1.124 | 0.017 | 0.9998 | 7 |
| B | dijkstra | mem_bytes | 0.920 | 0.035 | 0.9989 | 7 |
| B | bellman | time_s | 1.111 | 0.038 | 0.9991 | 7 |
| B | bellman | ops | 1.197 | 0.015 | 0.9999 | 7 |
| B | bellman | mem_bytes | 0.920 | 0.036 | 0.9989 | 7 |
| B | bfs | time_s | 1.050 | 0.025 | 0.9996 | 7 |
| B | bfs | ops | 1.210 | 0.037 | 0.9993 | 7 |
| B | bfs | mem_bytes | 0.911 | 0.038 | 0.9987 | 7 |
| F | kruskal | time_s | 1.154 | 0.021 | 0.9998 | 7 |
| F | kruskal | ops | 1.187 | 0.030 | 0.9995 | 7 |
| F | kruskal | mem_bytes | 0.858 | 0.075 | 0.9942 | 7 |
| F | prim | time_s | 1.086 | 0.024 | 0.9996 | 7 |
| F | prim | ops | 1.158 | 0.044 | 0.9989 | 7 |
| F | prim | mem_bytes | 0.881 | 0.044 | 0.9982 | 7 |

Round 2: preprocessing is separate from core counts. Point predictions are informed by round 1.

| Method | Metric | Predicted exponent | Observed | Relative error |
|---|---|---:|---:|---:|
| dijkstra | time_s | 1.10 | 1.042 | 5.570% |
| dijkstra | ops | 1.10 | 1.124 | 2.120% |
| dijkstra | mem_bytes | 1.00 | 0.920 | 8.644% |
| bellman | time_s | 1.10 | 1.111 | 1.025% |
| bellman | ops | 1.10 | 1.197 | 8.120% |
| bellman | mem_bytes | 1.00 | 0.920 | 8.702% |
| bfs | time_s | 1.00 | 1.050 | 4.777% |
| bfs | ops | 1.00 | 1.210 | 17.388% |
| bfs | mem_bytes | 1.00 | 0.911 | 9.768% |
| kruskal | time_s | 1.20 | 1.154 | 3.988% |
| kruskal | ops | 1.20 | 1.187 | 1.122% |
| kruskal | mem_bytes | 1.00 | 0.858 | 16.613% |
| prim | time_s | 1.20 | 1.086 | 10.489% |
| prim | ops | 1.20 | 1.158 | 3.601% |
| prim | mem_bytes | 1.00 | 0.881 | 13.539% |
