# Prediction log, module C (rescue scheduling), Adan (24I-3037-C)

Same rules as `prediction_log.md` (Section 7.3 of the project statement): every round has an entry that is written
**before the round is run**; the section "After the run" is added afterwards and says what was wrong and why. This file
is to be merged into `prediction_log.md` later (the ids carry the prefix C so they do not clash with the ids of modules A and D).
The numbers are checked automatically by `python experiments/predictionsC.py` (same ids), which writes
`results/predictions-vs-measurements-C.md`.

Master dataset: master_release_v1. Group seed 41 (sample positions 41 mod 7 = 6, 13, 20, ...). Time unit: seconds on one core,
median of 5 runs after one discarded warm-up run. Pools: consecutive cases of one tier are joined, the windows of the i-th case are
shifted by 1440 * i minutes, ids are renumbered from 1, the pool is cut after the first n windows (`experiments/sampleC.py`).

**Order of events.** All four entries below were written together in one sitting on 2026-11-20, saved at 12:21 (UTC+5, laptop clock), after
`src/modules/rescue.py`, its tests and its fault-injection tests were finished and before `experiments/runC.py`, `analyzeC.py` and
`predictionsC.py` existed. No experiment of module C had been run. Entries are not committed by me (I was not asked to commit); the
timestamp in this file and the fact that the run script did not exist yet are the only evidence of the order, so **commit this file before the first run**.

**What I knew before writing (honest note).**
1. I ran the unit tests of module C (about 55 tests) several times. They do not time anything on purpose, but the test runner printed
   durations: the first version of a randomised test that called brute force on up to 22 windows took 51 s, and the test that runs
   `dp`, `dpquad` and a reference on seven master-data cases of 127 to 2185 windows took 2.2 s. I did not use these two numbers to set a constant below,
   but I cannot claim they had no influence on my sense of scale; the brute force prediction (3.3) and the `dpquad` time (1.9) are the ones they could have touched.
2. I read the sizes of the master data (windows per case: tier S 8 to 20, M 50 to 300, L 1000 to 2967, X 1000 to 2953; 1,535,262 windows in all),
   the claims of tier S, and the generator code (starts uniform in a horizon of 1440 minutes, lengths 15 to 300 minutes, or 5 to 120 in the cyclone scenario, values 1 to 100 independent of the length).
3. The per-operation constants below come from the **results of Ayna's modules** (`results/results.csv`, measured on her cloud VM, Intel Xeon 2.1 GHz, Python 3.13):
   about 155 ns per operation (comparison or move) of our merge sort, 51 ns per comparison in a Python scan loop. This laptop (Python 3.14, Windows) is a different machine,
   so absolute times carry a factor-of-two uncertainty in both directions and their tolerances are wide. Exponents, operation counts and quality numbers do not depend on the machine.

**Added after the full run (disclosure).** After this file was saved and before the full run I ran `runC.py --quick` once (tiny sizes, 12 quality cases) to test the scripts. It showed about 120 ns per inner step of `dpquad` at n = 20 000 and greedy / dp value ratios of 0.72 to 0.89. I did not change any prediction above. Several of the misses (C1.9 region, C2.5 to C2.8) are in the direction that this run showed.

**Operations counted** (the statement's families; see the module docstring): ordering = key comparisons and element moves of our merge sort
(`comparisons`, `moves`); selection and tabulation = windows examined, table cells, binary-search probes (`items_examined`, `cells`, `probes`);
all-subsets = `subsets`; preprocessing (validation pass, pair tests of the brute force) separately in `pre`. The `ops` column of `results.csv` is
`comparisons + moves + probes + items_examined + cells + subsets` (calls and `pre` are not in it), the breakdown is in the column `note`.

---

## Round 1: growth in n of the greedy rule, the DP with binary search and the O(n^2) DP

**Date and time:** 2026-11-20 12:21 UTC+5 (before running round 1)

**Experiment:** `C-scale-n`, n = 47, 94, 188, 375, 750, 1500, 3000 windows (7 sizes, ratio 2), pooled from tier L cases starting at the first case of the sample.
Algorithms: `greedy` (objective count, the shipped method for the count), `dp` (objective value, the shipped method for the value), `dpquad` (objective value).

**Which algorithm I expect to win:** `greedy` is the fastest, `dp` costs about 1.3 times as much (probes and a table on top of the same sort), and `dpquad`
gives the same total as `dp` but loses from n = 188 on and is about ten times slower at n = 3000. `dp` is the algorithm that is both fast and optimal for the value.

| id | prediction | tolerance (counts as a hit) |
|---|---|---|
| C1.1 | greedy: log-log slope of time against n is 1.1 | 0.95 to 1.3 |
| C1.2 | dp: log-log slope of time against n is 1.1 | 0.95 to 1.3 |
| C1.3 | dpquad: log-log slope of time against n is 1.75 | 1.5 to 2.05 |
| C1.4 | dpquad: `ops` at n = 3000 is 4.57 million (4 498 500 windows examined plus about 69 000 for the sort) | 4.55 to 4.60 million |
| C1.5 | greedy: `ops` at n = 3000 is 69 900 | 64 000 to 76 000 |
| C1.6 | dp: `ops` at n = 3000 is 104 700 | 96 000 to 115 000 |
| C1.7 | greedy: time at n = 3000 is 16 ms | 8 to 35 ms |
| C1.8 | dp: time at n = 3000 is 22 ms | 11 to 45 ms |
| C1.9 | dpquad: time at n = 3000 is 0.30 s | 0.15 to 0.70 s |
| C1.10 | dpquad time / dp time at n = 3000 is 14 | 6 to 40 |
| C1.11 | dpquad: log-log slope of time against `ops` is 0.95 (the counted operations explain the time) | 0.85 to 1.1 |
| C1.12 | dp and dpquad return the same total at every size (share of sizes with equal totals) | exactly 1.0 |
| C1.13 | dp time / greedy time at n = 3000 is 1.35 | 1.1 to 2.0 |
| C1.14 | greedy: number of windows chosen at n = 3000 is 80 | 40 to 160 |
| C1.15 | dp: peak memory beyond the input at n = 3000 is 230 bytes per window | 110 to 450 |
| C1.16 | the smallest n at which dpquad is more than twice as slow as dp is 188 | 94 to 375 |

**Reasoning.**
- Greedy and `dp` first validate (one pass, linear), then sort with our merge sort: bottom-up, so `moves` is exactly n * ceil(log2 n) = 36 000 at n = 3000, and
  `comparisons` for random order is about n (log2 n - 1.25) = 30 900. With the pass over the sorted windows (n) the total is 69 900 (C1.5). The DP adds binary-search probes:
  sum over i of about log2 i, about n (log2 n - 1.44) + 0.5 n = 31 800, plus n table cells and n windows examined: 69 900 - 3 000 + 31 800 + 3 000 + 3 000 = 104 700 (C1.6).
  `dpquad` looks at every earlier window of every window: exactly n (n - 1) / 2 = 4 498 500 windows plus the sort (66 900) plus n cells: 4.57 million (C1.4).
- Slopes. n log n has a local slope 1 + 1 / ln n, about 1.15 between n = 47 and 3000; the linear validation pass pulls it down, fixed per-call costs pull it down at the small sizes: 1.1 (C1.1, C1.2).
  For `dpquad` the n^2 term dominates only from n of a few hundred on (at n = 47 the sort and validation cost about as much as the 1 081 inner steps), so the fit over seven sizes is below 2: 1.75 (C1.3).
- Absolute time (machine dependent, see the note above): validation about 1.5 microseconds per window (5 ms at n = 3000, my estimate from similar loops), the sort 70 000 operations at about 155 ns (11 ms),
  so greedy is about 16 ms (C1.7); `dp` adds about 32 000 probes at about 100 ns and a table loop: 22 ms (C1.8), ratio 1.35 (C1.13).
  `dpquad` does 4.5 million inner steps of two comparisons at about 55 to 65 ns: about 0.27 s plus the 20 ms of the rest, 0.30 s (C1.9), ratio about 14 (C1.10).
  The time against operations (C1.11): at small n the time is dominated by validation, which is not in `ops`, so the slope is a little below 1.
- Crossover (C1.16): at n = 188 `dpquad` does 17 578 inner steps (about 1.1 ms) against about 0.9 ms for the whole `dp` run, ratio about 2.2; at n = 94 the ratio is about 1.5; at n = 375 about 3. The 188 is at the edge of the "more than twice" condition, so the tolerance spans a size in each direction.
- Count (C1.14): with window starts uniform and lengths 15 to 300 minutes, the next window of the earliest-finish rule finishes about 15 + 0.5 sqrt(2 pi D / lambda) minutes after the last one
  (D = 285 the spread of lengths, lambda = starts per minute, about 1.2 for a whole tier L case): about 34 minutes, so about 42 windows in a day; in the cyclone scenario (lengths 5 to 120) about 83. A pool of 3000 is one whole case of about 1800 windows plus a truncated part of the next: about 80 in total. This is the weakest prediction of the round (factor 2 either way).
- Memory (C1.15): the validation list of new `Window` tuples (about 72 bytes each plus 8 for the list slot), two lists for the merge sort, the two table lists with their integers: about 230 bytes per window. A guess.

**After the run** (written 2026-11-20 after round 1; full table in `results/predictions-vs-measurements-C.md`): 14 of 16 inside the tolerance, **2 misses: C1.8 and C1.14**. Four more hits are at the very edge of their range (C1.7, C1.9, C1.16 at 49 to 50 % error; C1.2 at the upper end), so they say little.
- **Counts and exponents were good.** `dpquad` ops at n = 3000: 4 566 739 (4.57 million predicted; 4 498 500 pairs plus the sort and n cells). Greedy ops 68 239 (69 900), dp ops 101 749 (104 700). The time of `dpquad` against its counted operations has slope 0.97 (0.95 predicted); for dp 1.07, for greedy 0.92 (R^2 0.94, the small sizes are noisy). `dp` and `dpquad` returned the same total at all 7 sizes (C1.12).
- **Slopes.** greedy 1.07 +- 0.28 (R^2 0.95; the interval is wide because the point at n = 47 is noisy: median 558 us, IQR 271 us, larger than the point at n = 94, probably another process on the laptop); dp 1.26 +- 0.10 (1.1 predicted: a hit, at the upper end; its operations alone grow with slope 1.17); dpquad 1.85 +- 0.21 (1.75 predicted). The operation count of `dpquad` has slope 1.92, so its time slope is below 2 because of the linear validation and the fixed costs at small n.
- **C1.8 (miss: 46.5 ms against 22 ms predicted, range 11 to 45), C1.7 and C1.9 (hits at 49 % and 50 % error).** All three times are about twice my estimate: greedy took 31 ms, `dpquad` 0.60 s, which is 130 ns per inner step instead of the 55 to 65 ns I assumed (I took the 51 ns of Ayna's scan loop; my loop has two comparisons and indexing into two lists).
  The validation and table costs were underestimated as well. The ratio of `dpquad` to `dp` (12.8, predicted 14) and all counts were right while the absolute times were low by a factor of two: this laptop is not the cloud VM whose constants I used, which the log said in advance.
- **C1.14 (miss: 184 windows chosen at n = 3000, 80 predicted).** My model (next window finishes 15 + 0.5 sqrt(2 pi D / lambda) minutes after the last) was too pessimistic by a factor of about 2: the generator also moves n / 8 windows so that they touch another one, and the chosen counts 18, 25, 34, 46, 58, 103, 184 for n = 47 ... 3000 grow slowly inside the first case and nearly double when the second case is joined at n = 3000. I did not test this explanation.
- **C1.16 (hit at the edge).** The smallest size where `dpquad` is more than twice as slow as `dp` was 375 (ratios 1.05, 1.5, 1.75, 2.62, 4.1, 7.5, 12.8 for n = 47 ... 3000); I predicted 188 (range 94 to 375).
- **C1.15 (memory, hit).** 172 bytes per window for `dp` (230 predicted). The peaks of greedy, dp and dpquad are almost the same (n = 375: 74 584 bytes for all three): the list of validated `Window` tuples built by `solve` dominates, not the tables.


---

## Round 2: quality of the greedy rule against the DP (count and value), on the master data

**Date and time:** 2026-11-20 12:21 UTC+5 (before running round 2)

**Experiment:** `quality-C.csv`: samples of tier S (20 cases), M (20), L (10) and X (12, the cases 46 to 49 of the sample), seed 41. For every case: the total of `greedy` and of `dp` for the count,
the value of `greedy` and of `dp` for the value, and the number of windows used by the value-optimal plan. For tier S the claims of the master data (`window_count_opt`, `window_value_opt`) are compared too.

**Which algorithm I expect to win:** for the **count**, greedy and dp tie (greedy is optimal, the exchange argument), greedy at a fraction of the cost. For the **value**, dp wins clearly: it is optimal, the greedy rule ignores the values
and gives up about a third of the value. No algorithm wins both measures unless the count is the objective.

| id | prediction | tolerance |
|---|---|---|
| C2.1 | tier S: the count of the greedy rule equals the claim `window_count_opt` in every case (share) | exactly 1.0 |
| C2.2 | tier S: the value of the dp equals the claim `window_value_opt` in every case (share) | exactly 1.0 |
| C2.3 | all sampled cases: greedy count equals dp count (share) | exactly 1.0 |
| C2.4 | tier S: the share of cases in which the greedy value is not optimal is 0.85 | 0.60 to 1.0 |
| C2.5 | tier S: mean greedy value / dp value is 0.70 | 0.58 to 0.82 |
| C2.6 | tier M: mean greedy value / dp value is 0.62 | 0.48 to 0.76 |
| C2.7 | tier L: mean greedy value / dp value is 0.58 | 0.42 to 0.72 |
| C2.8 | tier X (cases 46 to 49): mean greedy value / dp value is 0.58 | 0.42 to 0.72 |
| C2.9 | the worst greedy value / dp value over all sampled cases is 0.40 | 0.20 to 0.55 |
| C2.10 | tiers M and L: mean (windows used by the value-optimal plan) / (greedy count) is 0.75 | 0.50 to 0.95 |

**Reasoning.**
- Count: the earliest-finish rule is optimal for the number of windows (replace the first window of any optimal set by the one that finishes first: still compatible, same size, then induct), so C2.1 and C2.3
  can only fail through a bug of mine or a defective claim. The value claims are exhaustive-search optima of other groups; the dp must reproduce them (C2.2), like the DP of module A did.
- Value: values are 1 to 100 and independent of the length (generator), so the greedy rule takes about as many windows as the optimum count, with a mean value of about 50 each, while the value-optimal plan
  trades some windows for high-value ones. With about 5 windows in a plan in tier S (claims, e.g. case 1-00: 5 windows, value 345, that is 69 per window) the ratio is about 50 / 69 = 0.72 or lower (C2.5);
  it is rarely exactly optimal (C2.4). With hundreds of windows the optimum can choose among many overlapping windows and finds a chain of mean value above 70, while the greedy rule is stuck at 50 per window and
  the optimum gives up some windows, so the ratio is lower in M and L than in S (C2.6 to C2.8): 0.50 / 0.85 = 0.6. The traps 46 to 49 are built for other modules (46: sorted crates, 47: knapsack bait, 48: network, 49: log), their windows
  are ordinary tier X windows (1000 to 2953 of them), so I expect the same ratio as tier L (C2.8). The worst case (C2.9) will be a small tier S case where a single window of value 100 blocks everything.
- C2.10: the value-optimal plan uses fewer windows than the maximum count, but not many fewer, because short windows are cheap to add.
  This is a guess with a wide tolerance.

**After the run** (written 2026-11-20 after round 2): 6 of 10 inside the tolerance, **4 misses: C2.5, C2.6, C2.7, C2.8 (the value ratios)**; all exact predictions held.
- **Exact predictions held.** The greedy count equals the claim in 20 of 20 tier S cases (C2.1), the DP value equals the claim in 20 of 20 (C2.2), and the greedy count equals the DP count in 62 of 62 sampled cases (C2.3): no sign of a bug of mine or of a defective claim.
- **C2.5 to C2.8 (misses, all in the same direction).** I predicted that the greedy plan loses a third to 40 % of the value; it loses less: mean greedy / dp value 0.843 (S), 0.773 (M), 0.743 (L), 0.721 (X) against 0.70, 0.62, 0.58, 0.58 predicted, errors 17 to 22 %.
  The order I predicted (the ratio falls from S to L) held. My reason ("the optimum gives up some windows") was wrong in size: the value-optimal plan uses 0.96 (S), 0.93 (M), 0.89 (L) and 0.89 (X) of the number of windows of the greedy plan (C2.10 hit: 0.92 against 0.75 predicted, range 0.5 to 0.95),
  so the value optimum is a nearly full-length chain of better windows, not a shorter chain. I overestimated how much better the windows of the optimum are than the mean of 50: the chain constraint limits which high-value windows can be combined.
- **C2.4 (hit, 0.80 against 0.85).** The greedy value is optimal in 4 of 20 tier S cases, 1 of 20 tier M cases and none of the 22 cases of tiers L and X.
- **C2.9 (hit, but not for the right size: worst ratio 0.269, predicted 0.40, range 0.20 to 0.55).** The worst case is in tier S, as I guessed, but it is worse than my number; the worst ratios in the other tiers are 0.55 (M), 0.58 (L) and 0.62 (X). In a small case the greedy plan can lose 73 % of the value.
- I had seen 12 of these cases in the quick smoke run (ratios 0.72 to 0.89) before the full run, which could have told me that the predictions were too low; I did not change them (see the note at the top).


---

## Round 3: small inputs, DP and greedy against brute force

**Date and time:** 2026-11-20 12:21 UTC+5 (before running round 3)

**Experiment:** `C-small-n`: n = 8, 11, 14, 17, 20 windows, pooled from tier S cases (first case of the sample; the cases are joined because one tier S case has 8 to 20 windows).
Algorithms `dp`, `dpquad`, `brute` (objective value) and `greedy` (objective count).

**Which algorithm I expect to win:** greedy is the fastest at every size; between the exact methods the DP is faster than brute force from n = 8 on (brute force needs 256 subsets, each with several operations, while the DP needs a validation pass and a sort of 8 windows), and by a factor in the thousands at n = 20.

| id | prediction | tolerance |
|---|---|---|
| C3.1 | brute: time grows by a factor 2.0 per extra window (semi-log fit) | 1.85 to 2.15 |
| C3.2 | brute: number of subsets at n = 20 is 1 048 576 | exactly |
| C3.3 | brute: time at n = 20 is 0.5 s | 0.25 to 1.1 s |
| C3.4 | the smallest n (of 8, 11, 14, 17, 20) at which dp is faster than brute is 8 | 8 to 11 |
| C3.5 | brute time / dp time at n = 20 is 5000 | 1500 to 15 000 |
| C3.6 | dp time / greedy time, mean over the five sizes, is 1.3 | 1.0 to 1.9 |
| C3.7 | brute, dp and dpquad give the same total at all five sizes (share) | exactly 1.0 |
| C3.8 | dpquad time / dp time, mean over the five sizes, is 1.15 | 0.85 to 1.6 |

**Reasoning.** Brute force visits every subset once (2^n steps in Gray code), so the time doubles per window (C3.1) and the count is exactly 2^n (C3.2). A step costs a few operations on Python integers
(shift, mask, `bit_count`, two additions, two comparisons): about 0.45 microseconds, so 2^20 steps take about 0.5 s (C3.3, see the note on what I had seen). At n = 8 brute force needs 256 steps (about 0.12 ms) and the pair tests;
the DP needs validation, a sort of 8 windows and 8 table cells (about 0.05 ms): so the DP already wins at the smallest size (C3.4). At n = 20 the DP takes about 0.1 ms: ratio 5000 (C3.5).
At these sizes dp and greedy share validation and sort and differ by a small table and a few probes: ratio 1.3 (C3.6); `dpquad` does at most 190 inner steps more: ratio near 1.15 (C3.8). The totals must be identical (C3.7).

**After the run** (written 2026-11-20 after round 3): 8 of 8 inside the tolerance.
- C3.1 brute growth base 1.95 per extra window (interval 1.92 to 1.98); the counted operations grow with base 1.996 (1 048 596 at n = 20, which is 2^20 subsets plus the 20 windows examined); C3.2 the note holds exactly 1 048 576 subsets.
- C3.3 brute at n = 20: 0.634 s (0.5 predicted); the 51 s test run I had seen earlier gave me this scale (see the note at the top). C3.5: brute / dp at n = 20 is 3 901 (5 000 predicted): the DP took 163 us, more than my 100 us.
- C3.4 the DP is faster than brute force already at n = 8 (59 us against 209 us). C3.6 dp / greedy 1.31 (1.3). C3.8 dpquad / dp 1.00 (1.15 predicted): at these sizes `dpquad` is as fast as `dp`; its at most 190 inner steps cost about what the probes and the table of the DP cost.
- C3.7: the totals of brute, dp and dpquad are equal at all five sizes.
- At n = 8 the IQR of the DP and of brute force is large compared with the median (brute 209 us, IQR 85 us), so the ratio at n = 8 should not be read closely.


---

## Round 4: the five minute rule (DNF)

**Date and time:** 2026-11-20 12:21 UTC+5 (before running round 4)

**Experiment:** `C-dnf`: one run of `dpquad` (objective value, 1 timed run, no warm-up repeat needed: if it passes 300 s it is a DNF) and of `dp` at n = 200 000 windows, pooled from about 115 tier L cases.
Brute force has no DNF run: it refuses more than 22 windows by design, and 2^22 steps finish in seconds.

**Which algorithm I expect to win:** `dp` finishes (about 2 to 3 seconds); `dpquad` does not finish in 300 s and is recorded as DNF.

| id | prediction | tolerance |
|---|---|---|
| C4.1 | dpquad at n = 200 000: status (1 = DNF, 0 = finished) | exactly 1 |
| C4.2 | the time of dpquad at n = 200 000 extrapolated from the log-log fit on n up to 3000 is 600 s | 250 to 1500 s |
| C4.3 | dp at n = 200 000: time is 2.5 s | 1.2 to 7 s |

**Reasoning.** At n = 200 000 `dpquad` has to look at 2 x 10^10 pairs; even at 30 ns a pair (a faster machine than the VM) that is 600 s, at 60 ns 1200 s, so a DNF is very likely (C4.1).
The extrapolation (C4.2) takes the fit of round 1: 0.30 s at 3000 with slope 1.75 to 1.9 gives 0.30 x 66.7^1.75 = 470 s to 0.30 x 66.7^1.9 = 870 s; I say 600 s. This is an extrapolation, not a measurement.
`dp` scales like n log n: from 22 ms at n = 3000, a factor 66.7 x (17.6 / 11.6) = 101 gives 2.2 s (C4.3); caches and a heap of 200 000 windows may add a little.

**After the run** (written 2026-11-20 after round 4): 3 of 3 inside the tolerance.
- C4.1: `dpquad` at n = 200 000 passed 300 s and is recorded as DNF; `dp` finished in 4.37 s (IQR 0.23 s), choosing 5 771 windows of total value 360 121. C4.3 (2.5 s predicted, range 1.2 to 7): a hit with 43 % error, consistent with the factor of about two that all absolute times of this laptop had in round 1 (the DP did 9.9 million counted operations, about 440 ns each; at n = 3000 it was 457 ns each, so no growth of the cost per operation is visible).
- C4.2: the log-log fit on n up to 3000 extrapolates to 1 065 s (600 predicted, range 250 to 1500). This is an extrapolation of a fit with slope 1.85, not a measurement; counting pairs instead (2 x 10^10 at about 130 ns) would give about 2 600 s. The run itself was stopped at 300 s by the deadline check in the inner loop and no time was recorded.

---

## Summary after all rounds (2026-11-20)

37 numerical predictions, 31 inside the tolerance, **6 misses: C1.8, C1.14, C2.5, C2.6, C2.7, C2.8**.
- Predictions about counts and exponents (C1.4 to C1.6, C1.11, C2.1 to C2.3, C3.2, C3.7) were close or exact.
- Predictions about absolute times (C1.7 to C1.9, C4.2, C4.3) were all too low by about a factor of 2 (the laptop is about twice as slow as I assumed from Ayna's constants on her VM): four were hits at 43 to 50 % error and one (C1.8) a miss. Hits at the edge of the range (C1.7, C1.9, C1.16, C4.3) are weak evidence that I understood the constants.
- The two real modelling errors: the number of windows the greedy rule chooses (C1.14, a factor of 2.3) and the size of the value the greedy rule gives up (C2.5 to C2.8: it gives up 16 to 28 %, not 30 to 42 %).
- **Where the measurements were made.** On the author's laptop (Intel64 Family 6 Model 142, 8 logical CPUs, Windows 10, Python 3.14.6, one thread, see `results/environmentC.json`). I could not verify that it was on the charger and in best-performance mode, so the group should repeat the runs under those conditions and replace the numbers here if they differ.


---

## What each round can show and what it cannot

- Round 1 shows the shape of the growth of three algorithms on the pooled windows of the master data. It cannot show how they behave on other window distributions: the pools keep the data's density
  (about 1.2 window starts per minute inside a day) and shifting joined cases by 1440 minutes keeps them apart, so the overlap structure is that of one case, never of 3000 windows inside one day.
- Round 2 is a sample of 62 cases of one dataset, not a guarantee. A ratio of 0.58 says "about 40 % of the value is lost on these cases", not a bound.
- Round 3 uses pooled tier S cases (up to 20 windows), so the totals are small and nothing about the brute force's pruning matters (it has none).
- Round 4 is one run and an extrapolation.
