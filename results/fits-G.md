| experiment | algorithm | quantity | model | sizes | slope or base | 95 % interval | R^2 | theory |
|---|---|---|---|---|---|---|---|---|
| G-chain-n | dp | time | log-log | 7 | 2.891 | +-0.154 | 0.9978 | n^3: slope slightly below 3 (quadratic parts at small n) |
| G-chain-n | dp | operations | log-log | 7 | 2.950 | +-0.027 | 0.9999 | n^3: slope slightly below 3 (quadratic parts at small n) |
| G-chain-n | memo | time | log-log | 7 | 2.924 | +-0.282 | 0.9930 | n^3: slope slightly below 3 |
| G-chain-n | memo | operations | log-log | 7 | 2.950 | +-0.027 | 0.9999 | n^3: slope slightly below 3 |
| G-drum-L | dp | time | log-log | 6 | 2.032 | +-0.096 | 0.9988 | L^2: slope slightly below 2 |
| G-drum-L | dp | operations | log-log | 6 | 1.988 | +-0.008 | 1.0000 | L^2: slope slightly below 2 |
| G-drum-L | memo | time | log-log | 6 | 2.025 | +-0.048 | 0.9997 | L^2: slope slightly below 2 |
| G-drum-L | memo | operations | log-log | 6 | 1.988 | +-0.008 | 1.0000 | L^2: slope slightly below 2 |
| G-drum-L | greedy | time | log-log | 6 | 1.157 | +-0.026 | 0.9997 | L log L: slope slightly above 1 |
| G-drum-L | greedy | operations | log-log | 6 | 1.186 | +-0.021 | 0.9998 | L log L: slope slightly above 1 |
| G-small-chain | brute | time | semi-log | 5 | 3.343 | 2.836 to 3.941 | 0.9945 | Catalan numbers: about 3.2 per extra matrix between 4 and 12 (tends to 4) |
| G-small-chain | brute | operations | semi-log | 5 | 3.237 | 3.031 to 3.458 | 0.9991 | Catalan numbers: about 3.2 per extra matrix between 4 and 12 (tends to 4) |
| G-small-drum | brute | time | semi-log | 5 | 2.039 | 1.974 to 2.105 | 0.9994 | 2^(L-1): base 2 per unit of length |
| G-small-drum | brute | operations | semi-log | 5 | 2.000 | 2.000 to 2.000 | 1.0000 | 2^(L-1): base 2 per unit of length |
| G-chain-n | dp | time against ops | log-log | 7 | 0.980 | +-0.047 | 0.9983 | time proportional to the counted operations: slope 1 |
| G-chain-n | memo | time against ops | log-log | 7 | 0.991 | +-0.100 | 0.9924 | time proportional to the counted operations: slope 1 |
| G-drum-L | dp | time against ops | log-log | 6 | 1.022 | +-0.045 | 0.9990 | time proportional to the counted operations: slope 1 |
| G-drum-L | memo | time against ops | log-log | 6 | 1.019 | +-0.022 | 0.9998 | time proportional to the counted operations: slope 1 |
| G-drum-L | greedy | time against ops | log-log | 6 | 0.976 | +-0.022 | 0.9997 | time proportional to the counted operations: slope 1 |
