| experiment | algorithm | quantity | model | sizes | slope or base | 95 % interval | R^2 | theory |
|---|---|---|---|---|---|---|---|---|
| C-scale-n | greedy | time | log-log | 7 | 1.073 | +-0.283 | 0.9500 | n log n: slope slightly above 1 |
| C-scale-n | greedy | operations | log-log | 7 | 1.165 | +-0.025 | 0.9997 | n log n: slope slightly above 1 |
| C-scale-n | dp | time | log-log | 7 | 1.257 | +-0.096 | 0.9956 | n log n: slope slightly above 1 |
| C-scale-n | dp | operations | log-log | 7 | 1.171 | +-0.025 | 0.9997 | n log n: slope slightly above 1 |
| C-scale-n | dpquad | time | log-log | 7 | 1.853 | +-0.207 | 0.9906 | n^2: slope 2 once the quadratic term dominates |
| C-scale-n | dpquad | operations | log-log | 7 | 1.916 | +-0.036 | 0.9997 | n^2: slope 2 once the quadratic term dominates |
| C-small-n | brute | time | semi-log | 5 | 1.949 | 1.919 to 1.979 | 0.9998 | 2^n: base 2 per window |
| C-small-n | brute | operations | semi-log | 5 | 1.996 | 1.989 to 2.002 | 1.0000 | 2^n: base 2 per window |
| C-scale-n | greedy | time against ops | log-log | 7 | 0.918 | +-0.259 | 0.9433 | time proportional to the counted operations: slope 1 |
| C-scale-n | dp | time against ops | log-log | 7 | 1.071 | +-0.104 | 0.9929 | time proportional to the counted operations: slope 1 |
| C-scale-n | dpquad | time against ops | log-log | 7 | 0.969 | +-0.090 | 0.9935 | time proportional to the counted operations: slope 1 |
