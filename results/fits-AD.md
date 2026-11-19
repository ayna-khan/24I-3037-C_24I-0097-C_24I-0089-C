| module | experiment | algorithm | quantity | model | sizes | slope or base | 95 % interval | R^2 | theory |
|---|---|---|---|---|---|---|---|---|---|
| A | A-scale-n | dp | time | log-log | 6 | 2.141 | +-0.128 | 0.9981 | n*W with W proportional to n: slope 2 |
| A | A-scale-n | dp | operations | log-log | 6 | 2.076 | +-0.117 | 0.9984 | n*W with W proportional to n: slope 2 |
| A | A-scale-n | greedy | time | log-log | 6 | 1.159 | +-0.272 | 0.9722 | n log n: slope slightly above 1 |
| A | A-scale-n | greedy | operations | log-log | 6 | 1.150 | +-0.016 | 0.9999 | n log n: slope slightly above 1 |
| A | A-scale-W | dp | time | log-log | 6 | 0.967 | +-0.175 | 0.9834 | n*W: slope 1 in W |
| A | A-scale-W | dp | operations | log-log | 6 | 1.005 | +-0.003 | 1.0000 | n*W: slope 1 in W |
| A | A-scale-W | greedy | time | log-log | 6 | 0.124 | +-0.176 | 0.4902 | independent of W: slope 0 |
| A | A-scale-W | greedy | operations | log-log | 6 | 0.000 | +-0.000 | 1.0000 | independent of W: slope 0 |
| A | A-small-n | brute | time | semi-log | 5 | 1.993 | 1.906 to 2.084 | 0.9988 | 2^n: base 2 per crate |
| A | A-small-n | brute | operations | semi-log | 5 | 2.000 | 2.000 to 2.000 | 1.0000 | 2^n: base 2 per crate |
| A | A-small-n | dp | time | log-log | 5 | 2.177 | +-0.708 | 0.9696 | n*W (W about 4 n): slope 2 |
| A | A-small-n | dp | operations | log-log | 5 | 2.063 | +-0.363 | 0.9909 | n*W (W about 4 n): slope 2 |
| A | A-small-n | greedy | time | log-log | 5 | 1.505 | +-0.497 | 0.9687 | n log n |
| A | A-small-n | greedy | operations | log-log | 5 | 1.657 | +-0.265 | 0.9925 | n log n |
| D | D-scale-m | heap | time | log-log | 9 | 1.179 | +-0.031 | 0.9991 | m log m: slope slightly above 1 |
| D | D-scale-m | heap | operations | log-log | 9 | 1.164 | +-0.028 | 0.9993 | m log m: slope slightly above 1 |
| D | D-scale-m | scan | time | log-log | 9 | 1.981 | +-0.059 | 0.9989 | m * backlog, backlog proportional to m: slope 2 |
| D | D-scale-m | scan | operations | log-log | 9 | 1.992 | +-0.004 | 1.0000 | m * backlog, backlog proportional to m: slope 2 |
| A | A-scale-n | dp | time against ops | log-log | 6 | 1.031 | +-0.064 | 0.9980 | time proportional to the counted operations: slope 1 |
| A | A-scale-W | dp | time against ops | log-log | 6 | 0.962 | +-0.172 | 0.9837 | time proportional to the counted operations: slope 1 |
| D | D-scale-m | scan | time against ops | log-log | 9 | 0.995 | +-0.027 | 0.9991 | time proportional to the counted operations: slope 1 |
| D | D-scale-m | heap | time against ops | log-log | 9 | 1.012 | +-0.038 | 0.9983 | time proportional to the counted operations: slope 1 |
| A | A-scale-n | greedy | time against ops | log-log | 6 | 1.009 | +-0.226 | 0.9746 | time proportional to the counted operations: slope 1 |
