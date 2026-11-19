| id | what | predicted (range) | measured | result | rel. error |
|---|---|---|---|---|---|
| 1.1 | A dp: log-log slope of time against n (W grows with n) | 2 (1.75 to 2.25) | 2.141 | HIT | 7 % |
| 1.2 | A greedy: log-log slope of time against n | 1.1 (0.9 to 1.3) | 1.159 | HIT | 5 % |
| 1.3 | A dp: time at n = 6400 (s) | 14 (9 to 21) | 19.01 | HIT | 26 % |
| 1.4 | A dp time / greedy time at n = 6400 | 450 (200 to 1500) | 761.4 | HIT | 41 % |
| 1.5 | A dp: smallest value over all sizes of cells / (n*W) | 0.985 (0.97 to 1) | 0.9857 | HIT | 0 % |
| 1.6 | A dp: peak memory / (n*W) at the largest size with memory measured | 1.1 (1 to 1.3) | 1.038 | HIT | 6 % |
| 1.7 | A greedy: peak memory per crate at n = 6400 (bytes) | 80 (40 to 120) | 102.4 | HIT | 22 % |
| 1.8 | A dp: log-log slope of time against W at fixed n | 0.95 (0.8 to 1.1) | 0.9668 | HIT | 2 % |
| 1.9 | A greedy: log-log slope of time against W at fixed n | 0 (-0.15 to 0.15) | 0.1243 | HIT | 100 % |
| 1.10 | A tier S sample: share of cases where greedy is not optimal | 0.55 (0.3 to 0.8) | 0.65 | HIT | 15 % |
| 1.11 | A tiers M and L samples: mean greedy / dp value | 0.997 (0.99 to 1) | 0.9985 | HIT | 0 % |
| 1.12 | A trap-47 cases: mean greedy / dp value | 0.55 (0.45 to 0.65) | 0.5607 | HIT | 2 % |
| 1.13 | A tier S sample: share of cases where dp equals the claim | 1 (1 to 1) | 1 | HIT | 0 % |
| 2.1 | A brute force: growth base per extra crate (semi-log fit) | 2 (1.85 to 2.15) | 1.993 | HIT | 0 % |
| 2.2 | A brute force: time at n = 20 (s) | 0.17 (0.1 to 0.3) | 0.1646 | HIT | 3 % |
| 2.3 | A dp time / greedy time, mean over the five small sizes | 4 (2 to 8) | 4.635 | HIT | 14 % |
| 2.4 | A smallest n at which dp is faster than brute force | 8 (8 to 11) | 8 | HIT | 0 % |
| 3.1 | D heap: log-log slope of time against m | 1.1 (0.95 to 1.3) | 1.179 | HIT | 7 % |
| 3.2 | D scan: log-log slope of time against m | 1.9 (1.7 to 2.1) | 1.981 | HIT | 4 % |
| 3.3 | D scan: key comparisons at m = 8000 | 1.09e+07 (6e+06 to 1.6e+07) | 1.067e+07 | HIT | 2 % |
| 3.4 | D scan: time at m = 64000 (s) | 51 (25 to 100) | 34.9 | HIT | 46 % |
| 3.5 | D heap: time at m = 64000 (s) | 0.5 (0.25 to 1) | 0.3981 | HIT | 26 % |
| 3.6 | D scan time / heap time at m = 250 | 1.2 (0.6 to 2) | 1.234 | HIT | 3 % |
| 3.7 | D maximum backlog / m at m = 64000 | 0.33 (0.2 to 0.45) | 0.3312 | HIT | 0 % |
| 3.8 | D heap: ops/(m log2 m) at m = 64000 divided by the same at m = 250 | 1 (0.75 to 1.25) | 1.28 | MISS | 22 % |
| 3.9 | D heap: peak memory per alarm at m = 8000 (bytes) | 250 (120 to 400) | 185 | HIT | 35 % |
| 3.10 | D: largest difference of the mean wait of all alarms, urgency order against first-come-first-served | 0 (0 to 1e-06) | 0 | HIT | 0 % |
| 3.11 | D tier L: mean wait of priority 9 and 10 alarms, first-come-first-served / urgency order | 80 (20 to 1000) | 428.8 | HIT | 81 % |
| 4.1 | D scan at m = 256000: status (1 = DNF, 0 = finished) | 1 (1 to 1) | 1 | HIT | 0 % |
| 4.2 | D scan at m = 256000: extrapolated time from the fit on m <= 64000 (s) | 670 (400 to 1100) | 505.8 | HIT | 32 % |
| 4.3 | D heap at m = 256000: time (s) | 2.5 (1.2 to 5) | 1.67 | HIT | 50 % |
