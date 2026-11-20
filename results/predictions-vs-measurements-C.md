| id | what | predicted (range) | measured | result | rel. error |
|---|---|---|---|---|---|
| C1.1 | greedy: log-log slope of time against n | 1.1 (0.95 to 1.3) | 1.073 | HIT | 2 % |
| C1.2 | dp: log-log slope of time against n | 1.1 (0.95 to 1.3) | 1.257 | HIT | 12 % |
| C1.3 | dpquad: log-log slope of time against n | 1.75 (1.5 to 2.05) | 1.853 | HIT | 6 % |
| C1.4 | dpquad: ops at n = 3000 | 4.57e+06 (4.55e+06 to 4.6e+06) | 4.567e+06 | HIT | 0 % |
| C1.5 | greedy: ops at n = 3000 | 69900 (64000 to 76000) | 6.824e+04 | HIT | 2 % |
| C1.6 | dp: ops at n = 3000 | 104700 (96000 to 115000) | 1.017e+05 | HIT | 3 % |
| C1.7 | greedy: time at n = 3000 (s) | 0.016 (0.008 to 0.035) | 0.03122 | HIT | 49 % |
| C1.8 | dp: time at n = 3000 (s) | 0.022 (0.011 to 0.045) | 0.04646 | MISS | 53 % |
| C1.9 | dpquad: time at n = 3000 (s) | 0.3 (0.15 to 0.7) | 0.5955 | HIT | 50 % |
| C1.10 | dpquad time / dp time at n = 3000 | 14 (6 to 40) | 12.82 | HIT | 9 % |
| C1.11 | dpquad: log-log slope of time against ops | 0.95 (0.85 to 1.1) | 0.9686 | HIT | 2 % |
| C1.12 | dp and dpquad return the same total (share of sizes) | 1 (1 to 1) | 1 | HIT | 0 % |
| C1.13 | dp time / greedy time at n = 3000 | 1.35 (1.1 to 2) | 1.488 | HIT | 9 % |
| C1.14 | greedy: windows chosen at n = 3000 | 80 (40 to 160) | 184 | MISS | 57 % |
| C1.15 | dp: peak memory per window at n = 3000 (bytes) | 230 (110 to 450) | 172.3 | HIT | 34 % |
| C1.16 | smallest n at which dpquad is more than twice as slow as dp | 188 (94 to 375) | 375 | HIT | 50 % |
| C2.1 | tier S: share of cases where the greedy count equals the claim | 1 (1 to 1) | 1 | HIT | 0 % |
| C2.2 | tier S: share of cases where the dp value equals the claim | 1 (1 to 1) | 1 | HIT | 0 % |
| C2.3 | all sampled cases: share where greedy count equals dp count | 1 (1 to 1) | 1 | HIT | 0 % |
| C2.4 | tier S: share of cases where the greedy value is not optimal | 0.85 (0.6 to 1) | 0.8 | HIT | 6 % |
| C2.5 | tier S: mean greedy value / dp value | 0.7 (0.58 to 0.82) | 0.843 | MISS | 17 % |
| C2.6 | tier M: mean greedy value / dp value | 0.62 (0.48 to 0.76) | 0.7728 | MISS | 20 % |
| C2.7 | tier L: mean greedy value / dp value | 0.58 (0.42 to 0.72) | 0.7425 | MISS | 22 % |
| C2.8 | tier X: mean greedy value / dp value | 0.58 (0.42 to 0.72) | 0.7211 | MISS | 20 % |
| C2.9 | worst greedy value / dp value over all sampled cases | 0.4 (0.2 to 0.55) | 0.269 | HIT | 49 % |
| C2.10 | tiers M and L: mean (windows of the value-optimal plan) / (greedy count) | 0.75 (0.5 to 0.95) | 0.9154 | HIT | 18 % |
| C3.1 | brute: growth base per extra window (semi-log fit) | 2 (1.85 to 2.15) | 1.949 | HIT | 3 % |
| C3.2 | brute: subsets at n = 20 | 1.04858e+06 (1.04858e+06 to 1.04858e+06) | 1.049e+06 | HIT | 0 % |
| C3.3 | brute: time at n = 20 (s) | 0.5 (0.25 to 1.1) | 0.6339 | HIT | 21 % |
| C3.4 | smallest n at which dp is faster than brute | 8 (8 to 11) | 8 | HIT | 0 % |
| C3.5 | brute time / dp time at n = 20 | 5000 (1500 to 15000) | 3901 | HIT | 28 % |
| C3.6 | dp time / greedy time, mean over the five sizes | 1.3 (1 to 1.9) | 1.312 | HIT | 1 % |
| C3.7 | brute, dp and dpquad return the same total (share of sizes) | 1 (1 to 1) | 1 | HIT | 0 % |
| C3.8 | dpquad time / dp time, mean over the five sizes | 1.15 (0.85 to 1.6) | 1.001 | HIT | 15 % |
| C4.1 | dpquad at the DNF size: status (1 = DNF, 0 = finished) | 1 (1 to 1) | 1 | HIT | 0 % |
| C4.2 | dpquad at n = 200 000: time extrapolated from the fit on n <= 3000 (s) | 600 (250 to 1500) | 1065 | HIT | 44 % |
| C4.3 | dp at n = 200 000: time (s) | 2.5 (1.2 to 7) | 4.365 | HIT | 43 % |

37 predictions: 31 hit, 6 miss, 0 not evaluated (round not run yet).
