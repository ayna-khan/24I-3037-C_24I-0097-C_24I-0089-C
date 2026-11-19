| module | experiment | algorithm | quantity | model | sizes | slope or base | 95 % interval | R^2 | theory |
|---|---|---|---|---|---|---|---|---|---|
| A | A-scale-n | dp | time | log-log | 6 | 2.215 | +-0.284 | 0.9915 | n*W with W proportional to n: slope 2 |
| A | A-scale-n | dp | operations | log-log | 6 | 2.076 | +-0.117 | 0.9984 | n*W with W proportional to n: slope 2 |
| A | A-scale-n | greedy | time | log-log | 6 | 1.219 | +-0.284 | 0.9726 | n log n: slope slightly above 1 |
| A | A-scale-n | greedy | operations | log-log | 6 | 1.150 | +-0.016 | 0.9999 | n log n: slope slightly above 1 |
| A | A-scale-W | dp | time | log-log | 6 | 0.858 | +-0.267 | 0.9523 | n*W: slope 1 in W |
| A | A-scale-W | dp | operations | log-log | 6 | 1.005 | +-0.003 | 1.0000 | n*W: slope 1 in W |
| A | A-scale-W | greedy | time | log-log | 6 | -0.083 | +-0.426 | 0.0686 | independent of W: slope 0 |
| A | A-scale-W | greedy | operations | log-log | 6 | 0.000 | +-0.000 | 1.0000 | independent of W: slope 0 |
| A | A-small-n | brute | time | semi-log | 5 | 2.024 | 1.940 to 2.112 | 0.9989 | 2^n: base 2 per crate |
| A | A-small-n | brute | operations | semi-log | 5 | 2.000 | 2.000 to 2.000 | 1.0000 | 2^n: base 2 per crate |
| A | A-small-n | dp | time | log-log | 5 | 2.138 | +-0.592 | 0.9778 | n*W (W about 4 n): slope 2 |
| A | A-small-n | dp | operations | log-log | 5 | 2.063 | +-0.363 | 0.9909 | n*W (W about 4 n): slope 2 |
| A | A-small-n | greedy | time | log-log | 5 | 1.628 | +-0.383 | 0.9839 | n log n |
| A | A-small-n | greedy | operations | log-log | 5 | 1.657 | +-0.265 | 0.9925 | n log n |
| D | D-scale-m | heap | time | log-log | 9 | 1.124 | +-0.112 | 0.9878 | m log m: slope slightly above 1 |
| D | D-scale-m | heap | operations | log-log | 9 | 1.164 | +-0.028 | 0.9993 | m log m: slope slightly above 1 |
| D | D-scale-m | scan | time | log-log | 9 | 1.961 | +-0.054 | 0.9991 | m * backlog, backlog proportional to m: slope 2 |
| D | D-scale-m | scan | operations | log-log | 9 | 1.992 | +-0.004 | 1.0000 | m * backlog, backlog proportional to m: slope 2 |
| A | A-scale-n | dp | time against ops | log-log | 6 | 1.066 | +-0.143 | 0.9908 | time proportional to the counted operations: slope 1 |
| A | A-scale-W | dp | time against ops | log-log | 6 | 0.854 | +-0.268 | 0.9514 | time proportional to the counted operations: slope 1 |
| D | D-scale-m | scan | time against ops | log-log | 9 | 0.985 | +-0.025 | 0.9992 | time proportional to the counted operations: slope 1 |
| D | D-scale-m | heap | time against ops | log-log | 9 | 0.966 | +-0.088 | 0.9897 | time proportional to the counted operations: slope 1 |
| A | A-scale-n | greedy | time against ops | log-log | 6 | 1.059 | +-0.252 | 0.9715 | time proportional to the counted operations: slope 1 |
