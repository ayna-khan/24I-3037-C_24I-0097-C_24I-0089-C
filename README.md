# LIFELINE - Algorithmic Relief-Command Engine (DAA project, group 41)

Group 41: Ayna Khan (24I-0097-C), Dur E Adan (24I-3037-C), Hamza Sardar (24I-0089-C).
Repository: see `repository.txt`.

**Status of this README.** The sections for modules A (relief inventory) and D (emergency queue) are complete.
Sections marked **TO BE FILLED BY ADAN** and **TO BE FILLED BY HAMZA** are placeholders for modules C, G (Adan) and B, F
and the campaign (Hamza); each of them uses the same format as the sections for A and D so that the README reads as one document.

## 1. Setup and dependencies

- Python 3.10 or newer (developed with 3.13). The decision modules, the tests and the experiments use the standard library only.
- `matplotlib` (plots only): `pip install matplotlib`.
- Library use that the statement asks us to document: `csv` (reading the master dataset), `tracemalloc` (memory measurement),
  `matplotlib` (plots), `unittest` (tests). The test references use the built-in `sorted` to check module D; the shipped algorithms
  never call a library sort: the sorting that module A and D need is our own merge sort (`src/sorting.py`).
- Master dataset: `master_release_v1` (release of 2026-11-12, 3,622 cases from 75 groups). Download it from the course link, keep the
  folder anywhere, and check it with `CHECKSUMS.txt`. The code takes its location as an argument; it is not copied into the repository.

## 2. How to run

All commands are run from the repository root. `MASTER` is the folder with the master CSV files.

| What | Command |
|---|---|
| All unit, integration and reference tests | `python -m unittest discover -s tests -t .` |
| Only modules A and D | `python -m unittest tests.testinventory tests.testqueue tests.testmeasure` |
| Fault-injection tests of A and D (about 2 minutes) | `python -m tests.testfaultinjection` (writes `results/fault-injection-AD.txt`) |
| Experiments of A and D, one round | `python experiments/runAD.py --master MASTER --round 1` (rounds 1, 2, 3, 4; see the prediction log) |
| Fits, comparison tables and plots of A and D | `python experiments/analyzeAD.py` |
| Predictions against measurements | `python experiments/predictionsAD.py` |
| Sample outputs of A and D | `python experiments/sampleAD.py --master MASTER` |
| Seven-day campaign | **TO BE FILLED BY HAMZA** (one documented command that runs the project from the master dataset) |

The experiments use no random numbers: samples and pools are fixed by the group seed 41 (see section 4), so a rerun gives the same
inputs and the same operation counts. Times vary from machine to machine.

## 3. Repository layout

```
README.md  prediction_log.md  repository.txt  members.txt
src/        models.py (data types, errors)   measure.py (timing, memory, fits)   sorting.py (our merge sort)
            modules/inventory.py (A)   modules/emergencyqueue.py (D)   [loader, validation layer, B, C, F, G, campaign: teammates]
tests/      testinventory.py  testqueue.py  testmeasure.py  testfaultinjection.py
            reference/ (independent reference methods, never imported by src)   fixtures/ (small samples of the master data)
experiments/ runAD.py  analyzeAD.py  predictionsAD.py  sampleAD.py  mastersample.py
results/    results.csv  plots/  quality-A.csv  quality-D.csv  fits-AD.md  comparison-AD.md  samples in sample-outputs/
generator/  validator/  cases.xlsx  approach.pdf  proposal.pdf   (Iteration 1, unchanged)
```

## 4. Data, samples and pooling

- Only the master dataset `master_release_v1` is used in Iteration 2. Master order is the row order of `cases.csv`.
- **Sample** of N cases of a tier: positions `s mod 7`, `s mod 7 + 7`, ... of the list of the cases of that tier, in master order, first N, with
  s = 41, so 41 mod 7 = 6. (We read "in master order" as "in the order of the tier's cases in `cases.csv`".)
- **Pools.** To get more elements than a case holds we join consecutive tier cases, starting at the first case of our sample, and renumber ids from 1:
  crates are appended and the capacity of the pool is `floor(n * sum of capacities / sum of crate counts)` over the joined cases (the statement does not
  fix the capacity of a pool; this keeps the capacity per crate of the data). Alarm ticks of each joined case are shifted past the last tick of the
  previous case. Networks are never pooled.
- **Interpretation notes.** The capacity of the pools varies between 2.9 and 4.2 kg per crate across sizes because different cases are joined.
  Pools of module D keep the arrival rate of the data (1.2 to 1.8 alarms per tick), so the backlog is a third of m.

## 5. Problem definitions and algorithms

Notation: n crates, W truck capacity (kg), m alarms. Ties are always broken by id ascending.

### Module A - relief inventory (Ayna)

- **Input:** crates (id, category, weight in whole kg > 0, value >= 0 of the day), integer capacity W >= 0.
- **Output:** a set of whole crates of total weight at most W with maximum total value (0/1 knapsack), or status `EMPTY` with a reason (no crates, capacity 0, nothing fits).
  Broken input (negative or fractional weight, duplicate ids, bad capacity) raises `InvalidInputError`; it is never turned into a plausible answer.
- **Shipped algorithm: dynamic programming over the capacity**, `O(n W)` time and `n (W + 1)` bytes for the back-tracking table.
  `best[c]` = largest value with total weight at most c; crate i updates `best[c] = max(best[c], best[c - w] + v)` for c >= w, and one byte per cell
  records whether crate i was taken. Crates heavier than W or of value 0 are dropped, and the table width is `min(W, total weight)`.
  The total value is unique; among equal-value sets the back-tracking (last crate first) returns the one that prefers earlier crates in the input order.
- **Baseline 1: ratio greedy**, `O(n log n)`: crates sorted by value/weight descending, compared as exact fractions by cross-multiplication
  (integers, never floats), ties by crate id, using our merge sort; each crate that still fits is loaded, and the pass continues after a crate that does not fit.
- **Baseline 2: brute force**, `O(2^n)`, all subsets in Gray-code order, refused for n > 22.
- **Campaign interface:** `inventory.solve(crates, capacity, method)` with method `dp`, `greedy` or `brute`; `inventory.with_day_values(crates, {category: multiplier})`
  gives `floor(base value * multiplier)` (whole-number multipliers: tools x2 on day 2, food x2 on day 3, medicine x3 on day 5).
  The result is a `LoadPlan(status, selected, total_weight, total_value, ops, note)`.
- **Retained or changed since the proposal:** retained (primary DP, baselines greedy and brute force). Added: the table width is reduced to `min(W, total weight)`.

### Module D - emergency queue (Ayna)

- **Input:** alarms (id, arrival tick >= 0, priority 1 to 10). **Output:** the release order, one alarm per tick, with its release tick. At every tick the alarms present are
  those with arrival tick <= now that are not released yet; the one released is the most urgent: priority descending, then arrival tick ascending, then id ascending.
  When nobody is present the tick passes with no release and the clock jumps to the next arrival. No alarms gives status `EMPTY`; broken input raises `InvalidInputError`.
  The plan also reports the maximum backlog, the total wait and the longest wait.
- **Shipped algorithm: binary min-heap** on the key `(-priority, tick, id)`, `O(m log m)`, sifting with a hole.
- **Baseline: linear scan** of all waiting alarms at every tick, `O(m * backlog)`. It gives exactly the same release order as the heap (checked by the tests).
- **Policy used only for comparison: first come, first served** (`release_fifo`), which ignores priority; it is not a solution of module D.
- **Campaign interface:** `emergencyqueue.release_order(alarms, method)` with method `heap` or `scan`; `emergencyqueue.with_extra_alarms(alarms, [(tick, priority), ...])` adds the day-2 alarm
  (priority 9, tick 0) and the day-5 alarm (priority 10, tick 0) with ids after the largest existing id, so they lose ties against older alarms of the same priority and tick.
- **Retained or changed since the proposal:** retained (heap primary, scan baseline). Not implemented: the ten-bucket queue named as a candidate in the proposal.

### Modules B, F (Hamza) and C, G (Adan)

**TO BE FILLED BY HAMZA (B route planning, F network planning, campaign) and ADAN (C rescue scheduling, G chains and cuts):**
for each module the same five items as above: input and output, shipped algorithm with its complexity, baseline, campaign interface, retained or changed since the proposal.

## 6. Operation counts (Section 7.3 of the statement)

The column `ops` of `results.csv` holds one number per run; the breakdown is in the column `note`.

| Module and method | Family | What `ops` counts |
|---|---|---|
| A, DP | selection and tabulation | table cells computed: for each kept crate of weight w, `width - w + 1` evaluations of the recurrence (the filtering pass over the crates is in `items` in the note) |
| A, greedy | ordering | key comparisons (calls of the exact ratio comparison) + element moves (elements written while merging); the final pass over the sorted crates is in the note |
| A, brute force | hard problems | subsets evaluated (always 2^n) |
| D, heap | queues | key comparisons between two `(-priority, tick, id)` keys + heap slots written (hole sifting, so a swap that would count 2 counts 1 per level) |
| D, scan | queues | key comparisons during scans (backlog - 1 per release) + list moves (one per append, one per removal; the released alarm is replaced by the last one) |

Preprocessing is counted separately: module D first checks in one pass that ticks do not decrease (m - 1 comparisons) and runs the merge sort only if they do; this is
`pre_comparisons` and `pre_moves` in the note. Memory (`mem_bytes`) is the peak of `tracemalloc` during one extra run, beyond the input; it is skipped (and said so in the note) when a run takes more than 8 s, because `tracemalloc` slows the run down.

## 7. Measurement method

- One discarded warm-up run, then the median of 5 runs with the interquartile range (linear interpolation of the quartiles), one thread, garbage collection switched off while a run is timed, data loading excluded.
  Runs shorter than 10 ms are timed as a batch and divided (the batch size is in the note).
- A run that passes 300 s is a DNF: the algorithm receives a deadline and raises `TimeBudgetExceeded`, and the row gets status DNF.
- Growth claims use a least-squares fit on at least 5 sizes (log-log for polynomial, semi-log for exponential) with the 95 % interval from the t distribution, R^2 and, in `results/predictions-vs-measurements-AD.md`, the relative error between prediction and measurement.
- **Hardware and software of the numbers in `results/`:** `results/environment.json`: Windows 11, an Intel laptop CPU (family 6, model 154, 12 logical processors), CPython 3.13.7, one thread, 5 timed runs after 1 warm-up.
  The numbers were measured on this one laptop. **The speed of the laptop changed during the first full run** (time per DP cell between 139 and 398 ns). Rounds 1 and 3 were therefore repeated with the charger connected and the power mode on best performance (about 85 ns per cell for 200 to 3200 crates);
  rounds 2 and 4 come from the first run and have not been repeated. One long run (6400 crates) still changed speed during its five timed runs (IQR 8.8 s). Absolute times and some fitted slopes of
  times are distorted, while operation counts, memory and quality numbers are exact and repeatable. Details and the list of affected predictions are in `prediction_log.md`. Another machine gives other absolute times.
- Prediction log: `prediction_log.md` (entries written and committed before each round; "After the run" notes written afterwards).

## 8. Results at a glance (modules A and D)

Full tables: `results/comparison-AD.md`; fits: `results/fits-AD.md`; plots with captions: `results/plots/`.

| Module | Experiment | Result |
|---|---|---|
| A | A-scale-n, 200 to 6400 crates | counted cells grow with slope 2.08 +- 0.12; DP time slope 2.22 +- 0.28 (2.05 +- 0.21 without the 6400 point, whose run changed speed); about 85 ns per cell for 200 to 3200 crates; 31.3 s at 6400 crates (161 million cells; IQR 8.8 s); greedy 40 ms; time against cells has slope 1.07 +- 0.14 |
| A | A-scale-W, n = 1600 | DP time slope 0.86 +- 0.27 in W (cells: 1.005; the first point, W = 522, is out of line at 195 ns per cell, the others cost 85 to 99 ns); greedy operation count exactly independent of W (time slope -0.08, R^2 0.07: no clear trend) |
| A | A-small-n, 8 to 20 crates | brute force doubles per crate (base 2.02, interval 1.94 to 2.11), DP is 878 times faster than brute force at n = 20 (0.67 ms against 585 ms; this round is from the first, slower run) |
| A | quality | DP equals the claim in 20 of 20 tier S cases; greedy is optimal in 7 of 20 tier S and 7 of 20 tier M cases, and loses 44 % on the trap-47 cases (mean greedy / DP 0.56) but only 0.2 % on tier M and 0.01 % on tier L |
| D | D-scale-m, 250 to 64000 alarms | heap slope 1.12 +- 0.11 (operations: 1.16), scan slope 1.96 +- 0.05 (comparisons: 1.99); scan / heap time 1.2 at 250, 29 at 16000, 113 at 64000 (heap 0.26 s, scan 29.8 s) |
| D | D-dnf, 256000 alarms | scan DNF (more than 300 s; plain quadratic growth from 29.8 s at 64000 alarms gives about 480 s, the fitted line about 390 s); heap 2.40 s, but this round is from the first, slower run and a repeat is expected to give about 1.2 s |
| D | quality | the mean wait of all alarms is the same under urgency order and first-come-first-served; priority 9 and 10 alarms wait 1.5 ticks (urgency) against 639 (FIFO) on tier L |

## 9. Recommendation for the lead designer (Problem N)

### Module A - relief inventory

- **Ship:** the dynamic programme over the capacity.
- **Evidence (experiments A-scale-n and the quality table):** it reproduces the exhaustive-search optimum in 20 of 20 tier S cases; the greedy rule loses 44 % on the trap-47 crates
  (greedy / DP between 0.55 and 0.59 in 10 of 10 cases) and up to 42 % in some tier S cases. Cost for the sizes of the data: a tier L case (up to 1500 crates, W up to about 10,000) is at most about 15 million cells,
  roughly 1.3 s here (0.88 s measured for 10.6 million cells: 1600 crates, W = 6637, at about 83 ns per cell).
- **Clash between theory and practice, and what we chose:** on tiers M and L the greedy rule is within 0.2 % and 0.01 % of the optimum in 0.1 % to 0.5 % of the time (sizes 1600 to 6400 crates). We still ship the DP because a daily
  truck load is decided once, the DP costs seconds, and a missed 40 % on a hostile case (trap 47) is not acceptable for lives; the greedy rule is the fallback when the DP is too slow.
- **Assumption:** weights are small whole numbers and the capacity is moderate, so that `n * W` stays below about 5 x 10^7 cells (about 4 to 10 s here at 85 to 190 ns per cell, depending on the speed of the machine at that moment) and the `n * W` byte table fits in memory (about 160 MB at 6400 crates and W = 25,000, computed as n * W, not measured).
- **It would be wrong when** the capacity is measured in a much finer unit (grams instead of kilograms multiplies W by 1000) or the fleet is much larger. **Measurement that tells:** compute `items * min(W, total weight)` before the run;
  above about 5 x 10^7 (or when the table would not fit in memory), switch to the greedy rule and report its gap, or implement branch and bound.

### Module D - emergency queue

- **Ship:** the binary heap.
- **Evidence (experiments D-scale-m and D-dnf):** the heap is 113 times faster than the scan at 64,000 alarms (0.26 s against 29.8 s) and finishes 256,000 alarms in 2.4 s (first, slower run), where the scan does not finish in 300 s.
  Under the urgency order, alarms of priority 9 and 10 wait 1.5 ticks on tier L, against 639 under first-come-first-served, with the same mean wait for all alarms.
- **Assumption:** more alarms arrive than can be answered (1.2 to 1.8 per tick against one release per tick), so the backlog grows with m (a third of m in our data) and the scan has to look at thousands of alarms per release.
- **It would be wrong when** the alarm rate stays below one per tick: then the backlog stays small and a scan of a few dozen alarms is as fast as the heap (they were close at 250 alarms: ratio 1.5). With only ten priority levels a
  ten-bucket queue would probably beat the heap; we did not implement or measure it. **Measurement that tells:** the maximum backlog reported in every release plan; if it stays below about 30 alarms, the heap is unnecessary.

### Modules B, C, F, G

**TO BE FILLED BY HAMZA (B, F) AND ADAN (C, G):** algorithm to ship, evidence with experiment name, assumption, one condition under which it would be wrong and the measurement that would tell.

### The three failure modes of the whole engine that worry us most (ranked)

**TO BE FILLED BY AYNA AFTER ALL MODULES ARE MEASURED** (the draft below is from modules A and D only; the final list must use the other modules too).

1. Cost of module A when the capacity or the number of crates is much larger than in the data: the table has `n * W` cells and `n * W` bytes; there is no safety net other than the deadline.
2. A backlog of alarms that never shrinks when the alarm rate stays above one per tick: the urgency order keeps priority 9 and 10 alarms fast, but low-priority alarms wait without bound (the longest wait was 2023 ticks for 2258 alarms in one tier L case).
3. Results that depend on our reading of the statement: how pools get their capacity, which tie rule is chosen among equal-value loads, and what "master order" means for samples.

## 10. Known limitations

- Pure Python: a DP cell costs about 85 ns on our laptop in the good state (up to 400 ns in the disturbed first run), so module A is slow compared with compiled code; sizes beyond 6400 crates were not run.
- **Timing noise.** The first full run changed speed on the laptop; rounds 1 and 3 were repeated with the charger connected and best performance, and are mostly clean (about 85 ns per DP cell). The 6400-crate run (IQR 8.8 s) and the W = 522 point are still disturbed, and rounds 2 and 4 (brute force at 8 to 20 crates, the 256,000-alarm run) come from the first, slower run, so their absolute times are less reliable than the operation counts, memory and quality numbers.
- The DP keeps one byte per (crate, capacity) cell; memory was not measured above 8 s per run (n = 1600 is the largest size with a measurement: 1.08 times `n * W` bytes).
- Module D assumes one release per tick and no preemption; values of day events enter only through the data given to the module.
- The tie rule among equal-value loads of module A is documented but arbitrary, so another correct implementation may return a different set with the same value.
- The ten-bucket queue and branch and bound (candidates in the proposal) are not implemented.
- The experiments were run on one machine, one run of each configuration (5 timed repetitions), with no control of other load on that machine; the IQR of some runs is large (see `results/comparison-AD.md`).
- Defects in the master dataset: none found in the sampled cases used by modules A and D (their tier S optima matched the claims in 20 of 20 cases); we did not check the whole master dataset.

## 11. Changes after the proposal

| Module | Proposal | Now | Reason |
|---|---|---|---|
| A | DP primary; greedy and brute force baselines | unchanged; table width reduced to `min(W, total weight)` | smaller table when the capacity exceeds the total weight |
| D | heap primary; linear scan baseline | unchanged; first-come-first-served added only as a comparison policy | to show what the urgency order buys; it is not a solution of module D |
| B, C, F, G | see proposal | **TO BE FILLED BY HAMZA AND ADAN** | |

## 12. References

- T. H. Cormen, C. E. Leiserson, R. L. Rivest, C. Stein, *Introduction to Algorithms*, 4th ed., MIT Press, 2022: dynamic programming for the 0/1 knapsack problem, binary heaps, merge sort.
- S. Martello, P. Toth, *Knapsack Problems: Algorithms and Computer Implementations*, Wiley, 1990: greedy ratio rule and its worst cases.
- Course project statement (Project Statement, LIFELINE) and the master dataset `master_release_v1`.