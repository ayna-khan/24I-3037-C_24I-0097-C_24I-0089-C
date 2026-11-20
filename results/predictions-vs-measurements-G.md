| id | what | predicted (range) | measured | result | rel. error |
|---|---|---|---|---|---|
| G1.1 | chain dp: log-log slope of time against n | 2.85 (2.6 to 3.1) | 2.89076 | HIT | 1 % |
| G1.2 | chain memo: log-log slope of time against n | 2.85 (2.6 to 3.1) | 2.92448 | HIT | 3 % |
| G1.3 | chain dp: ops at n = 320 | 5.51232e+06 (5.51232e+06 to 5.51232e+06) | 5.51232e+06 | HIT | 0 % |
| G1.4 | chain memo: recursive calls at n = 320 | 1.09226e+07 (1.09226e+07 to 1.09226e+07) | 1.09226e+07 | HIT | 0 % |
| G1.5 | chain dp: time at n = 640 (s) | 14 (8 to 28) | 13.4079 | HIT | 4 % |
| G1.6 | chain memo: time at n = 640 (s) | 65 (30 to 140) | 48.7327 | HIT | 33 % |
| G1.7 | chain memo time / dp time at n = 640 | 4.5 (2.5 to 7.5) | 3.63463 | HIT | 24 % |
| G1.8 | chain dp and memo return the same cost and bracketing (share of sizes) | 1 (1 to 1) | 1 | HIT | 0 % |
| G1.9 | chain dp: peak memory per n^2 at n = 160 (bytes) | 40 (25 to 70) | 42.4271 | HIT | 6 % |
| G1.10 | chain memo peak memory / dp peak memory at n = 160 | 0.8 (0.5 to 1.1) | 0.797815 | HIT | 0 % |
| G1.11 | chain dp: time at n = 160 (s) | 0.23 (0.12 to 0.5) | 0.184916 | HIT | 24 % |
| G1.12 | chain dp: time at n = 640 / time at n = 320 | 8 (6.5 to 10) | 9.02088 | HIT | 11 % |
| G1.13 | chain dp: log-log slope of the counted operations against n | 2.95 (2.9 to 3) | 2.9498 | HIT | 0 % |
| G2.1 | drum dp: log-log slope of time against L | 1.95 (1.8 to 2.1) | 2.03154 | HIT | 4 % |
| G2.2 | drum memo: log-log slope of time against L | 1.95 (1.8 to 2.1) | 2.02472 | HIT | 4 % |
| G2.3 | drum greedy: log-log slope of time against L | 1.1 (0.9 to 1.3) | 1.15696 | HIT | 5 % |
| G2.4 | drum dp: ops at L = 2000 | 2.003e+06 (2.003e+06 to 2.003e+06) | 2.003e+06 | HIT | 0 % |
| G2.5 | drum memo: recursive calls at L = 2000 | 2.001e+06 (2.001e+06 to 2.001e+06) | 2.001e+06 | HIT | 0 % |
| G2.6 | drum dp: time at L = 2000 (s) | 0.4 (0.2 to 0.9) | 0.348078 | HIT | 15 % |
| G2.7 | drum memo: time at L = 2000 (s) | 1.7 (0.8 to 4) | 1.16844 | HIT | 45 % |
| G2.8 | drum greedy: time at L = 2000 (s) | 0.007 (0.003 to 0.02) | 0.0137919 | HIT | 49 % |
| G2.9 | drum memo time / dp time at L = 2000 | 4 (2 to 7) | 3.35682 | HIT | 19 % |
| G2.10 | drum dp time / greedy time at L = 2000 | 55 (15 to 200) | 25.2378 | HIT | 118 % |
| G2.11 | drum dp and memo return the same price and pieces (share of sizes) | 1 (1 to 1) | 1 | HIT | 0 % |
| G2.12 | drum dp: peak memory per unit of length at L = 2000 (bytes) | 50 (25 to 120) | 104.536 | HIT | 52 % |
| G3.1 | tier S: share of cases where the dp price equals the claim | 1 (1 to 1) | 1 | HIT | 0 % |
| G3.2 | all sampled cases: share where the greedy price is not above the dp price | 1 (1 to 1) | 1 | HIT | 0 % |
| G3.3 | all sampled cases: share where the greedy price equals the dp price | 0.85 (0.65 to 0.97) | 0.983871 | MISS | 14 % |
| G3.4 | all sampled cases: mean greedy price / dp price | 0.998 (0.99 to 1) | 0.999634 | HIT | 0 % |
| G3.5 | all sampled cases: worst greedy price / dp price | 0.93 (0.8 to 0.99) | 0.977287 | HIT | 5 % |
| G3.6 | all sampled cases: mean (pieces of the dp cut) / L | 0.75 (0.45 to 1) | 0.719898 | HIT | 4 % |
| G3.7 | tier S: mean (cost left to right) / (optimal cost) | 1.35 (1.05 to 2.2) | 4.52589 | MISS | 70 % |
| G3.8 | tier L: mean (cost left to right) / (optimal cost) | 6 (2 to 25) | 16.8708 | HIT | 64 % |
| G4.1 | chain brute: bracketings enumerated at n = 12 | 58786 (58786 to 58786) | 58786 | HIT | 0 % |
| G4.2 | chain brute: growth factor per extra matrix of the enumerated count (semi-log fit) | 3.2 (3.1 to 3.35) | 3.23749 | HIT | 1 % |
| G4.3 | chain brute: time at n = 12 (s) | 0.6 (0.25 to 2) | 0.912082 | HIT | 34 % |
| G4.4 | chain: smallest n at which dp is faster than brute | 4 (4 to 6) | 4 | HIT | 0 % |
| G4.5 | chain: brute time / dp time at n = 12 | 4000 (1000 to 20000) | 3897.36 | HIT | 3 % |
| G4.6 | chain: memo time / dp time, mean over the five sizes | 2 (1.3 to 4) | 1.61137 | HIT | 24 % |
| G4.7 | chain: dp, memo and brute return the same bracketing (share of sizes) | 1 (1 to 1) | 1 | HIT | 0 % |
| G4.8 | drum brute: cuts enumerated at L = 20 | 524288 (524288 to 524288) | 524288 | HIT | 0 % |
| G4.9 | drum brute: growth factor per extra unit of length of the time (semi-log fit) | 2 (1.85 to 2.15) | 2.03868 | HIT | 2 % |
| G4.10 | drum brute: time at L = 20 (s) | 0.9 (0.4 to 2) | 0.923708 | HIT | 3 % |
| G4.11 | drum: smallest L at which dp is faster than brute | 8 (8 to 11) | 8 | HIT | 0 % |
| G4.12 | drum: brute time / dp time at L = 20 | 12000 (3000 to 50000) | 13402.1 | HIT | 10 % |
| G4.13 | drum: memo time / dp time, mean over the five sizes | 1.6 (1.1 to 3) | 2.41625 | HIT | 34 % |
| G4.14 | drum: dp, memo and brute return the same cut (share of sizes) | 1 (1 to 1) | 1 | HIT | 0 % |
| G4.15 | drum: dp time / greedy time, mean over the five sizes | 1 (0.6 to 1.6) | 0.663053 | HIT | 51 % |

48 predictions: 46 hit, 2 miss, 0 not evaluated (round not run yet).
