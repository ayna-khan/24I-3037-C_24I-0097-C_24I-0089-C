# B/F growth fits

Source: master_release_v1, case 10-40; connected BFS prefixes; no networks pooled.
Fits include changing edge density and validation/output construction. They describe this input family only.

| Module | Method | Metric | Exponent | 95% half-width | R² | Sizes |
|---|---|---|---:|---:|---:|---:|
| B | dijkstra | time_s | 1.037 | 0.021 | 0.9997 | 7 |
| B | dijkstra | ops | 1.099 | 0.015 | 0.9999 | 7 |
| B | dijkstra | mem_bytes | 0.923 | 0.033 | 0.9990 | 7 |
| B | bellman | time_s | 1.107 | 0.041 | 0.9990 | 7 |
| B | bellman | ops | 1.167 | 0.012 | 0.9999 | 7 |
| B | bellman | mem_bytes | 0.923 | 0.034 | 0.9990 | 7 |
| B | bfs | time_s | 1.049 | 0.023 | 0.9996 | 7 |
| B | bfs | ops | 1.150 | 0.024 | 0.9997 | 7 |
| B | bfs | mem_bytes | 0.914 | 0.037 | 0.9988 | 7 |
| F | kruskal | time_s | 1.151 | 0.023 | 0.9997 | 7 |
| F | kruskal | ops | 1.187 | 0.030 | 0.9995 | 7 |
| F | kruskal | mem_bytes | 0.864 | 0.073 | 0.9947 | 7 |
| F | prim | time_s | 1.078 | 0.014 | 0.9999 | 7 |
| F | prim | ops | 1.142 | 0.039 | 0.9991 | 7 |
| F | prim | mem_bytes | 0.883 | 0.043 | 0.9982 | 7 |
