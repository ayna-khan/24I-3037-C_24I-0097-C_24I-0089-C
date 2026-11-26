# B/F plot captions

All six figures use connected BFS prefixes of one sampled L network, not pooled
networks. Input construction/CSV loading is excluded. Times are medians of five
runs after one discarded warmup; error bars show half the IQR each side (not a
confidence interval). Memory is peak tracemalloc allocation in a separate run,
beyond the input. Counts sum comparisons, moves, edge tests, relaxations and
union-find parent traversals, including ordering for adjacency/output.

- B-time.png / B-operations.png / B-memory.png: positive-cost Dijkstra and
  Bellman-Ford solve the same problem; BFS is only the fewest-roads baseline.
- F-time.png / F-operations.png / F-memory.png: Kruskal and Prim solve the same
  minimum-forest problem. Forest equality across sampled waves is in quality-BF.csv.

Machine details: environmentBF.json. Edge density changes with prefix size, so
the fitted exponents describe this network family, not a universal bound.
