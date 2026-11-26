# Prediction log

Rules followed in this log (Section 7.3 of the project statement): every round has an entry
that is written and **committed before the round is run**. After the run, the section "After the run"
of the entry records what was wrong and why. The numbers below are checked automatically by
`python experiments/predictionsAD.py` (same ids), which writes `results/predictions-vs-measurements-AD.md`.
The entries of modules C and G (Adan) are checked the same way by `experiments/predictionsC.py` and `experiments/predictionsG.py`
(ids C1.1 ... C4.3 and G1.1 ... G4.15; `results/predictions-vs-measurements-C.md` and `-G.md`).

Entries in this file: Ayna Khan (24I-0097-C), modules A and D (rounds 1 to 4 and the summary below); Adan (24I-3037-C), modules C and G
(the sections "Module C" and "Module G" after the summary of Ayna); Hamza adds his entries for B and F after them, in the same format, each committed from his own account.

Master dataset: master_release_v1. Group seed 41 (so the sample positions are 41 mod 7 = 6, 13, 20, ...).
Time unit: seconds on one core, median of 5 runs after one discarded warm-up run.

**Order of events.** The entries below were drafted in a working session on 2026-11-16 (times are UTC) before any full run.
A first complete run was made in that session on a cloud machine (not reported here, used only as a cross-check where it is mentioned).
The numbers in the "After the run" notes are those of the run on Ayna's laptop (Windows 11, Intel CPU with 12 logical processors, Python 3.13.7, `results/environment.json`),
which produced `results/`. Predictions were committed before that run; the notes were written after it.

**Honest note on what was known before writing.** Before the entries below, the harness
(`experiments/runAD.py --quick`) was run once on tiny sizes (n up to 400, m up to 1000) only to check that
the scripts work. That run showed roughly 100 ns per DP cell and about 4 microseconds per alarm for the heap,
and I used these two constants to put numbers on the *absolute* times below. The growth exponents, operation
counts and quality predictions come from theory and from reading the data, not from that run. It also means
that the small-size crossovers (predictions 2.4 and 3.6) are partly informed by the smoke run, and I mark them so.

---

## Round 1: module A, growth in n and W, and quality of the greedy rule

**Date and time:** 2026-11-16 18:40 UTC (before running round 1)

**Experiments:** `A-scale-n` (n = 200, 400, 800, 1600, 3200, 6400 crates, pooled from tier L cases starting at
the first case of the sample, capacity W grows with n, about 3.4 per crate), `A-scale-W` (n = 1600 fixed, W from
total weight / 32 up to the total weight, doubling), and the quality table `quality-A.csv`
(samples of tiers S, M, L, X and the trap-47 cases).

**Which algorithm I expect to win:** the greedy rule is far faster, because it sorts once (O(n log n)) while the
DP fills n x W cells. The DP wins on *value*: it is optimal, the greedy rule is not. So I expect no algorithm to win on both.

| id | prediction | tolerance (counts as a hit) |
|---|---|---|
| 1.1 | DP: log-log slope of time against n is 2.0 | 1.75 to 2.25 |
| 1.2 | greedy: log-log slope of time against n is 1.1 | 0.9 to 1.3 |
| 1.3 | DP time at n = 6400 is 14 s | 9 to 21 s |
| 1.4 | DP time / greedy time at n = 6400 is 450 | 200 to 1500 |
| 1.5 | DP cells computed divided by n x W is at least 0.985 at every size | 0.97 to 1.0 |
| 1.6 | DP peak memory beyond the input is 1.1 x (n x W) bytes (the table of take/skip bytes) | 1.0 to 1.3 |
| 1.7 | greedy peak memory at n = 6400 is 80 bytes per crate | 40 to 120 |
| 1.8 | DP: log-log slope of time against W at fixed n is 0.95 | 0.8 to 1.1 |
| 1.9 | greedy: log-log slope of time against W is 0.0 (it never looks at W except in one comparison) | -0.15 to 0.15 |
| 1.10 | tier S sample: greedy is not optimal in 55 % of the cases | 30 % to 80 % |
| 1.11 | tiers M and L samples: mean greedy value / DP value is 0.997 | 0.990 to 1.0 |
| 1.12 | trap-47 cases: mean greedy value / DP value is 0.55 | 0.45 to 0.65 |
| 1.13 | tier S sample: the DP value equals the claim of the master data in every case (share 1.0) | exactly 1.0 |

**Reasoning.**
- The DP evaluates one cell per (crate, capacity) pair, so the work is about n x W. In `A-scale-n` the capacity
  per crate is roughly constant, so W is proportional to n and the work grows as n squared: slope 2 (1.1).
  The greedy rule is a merge sort plus one pass: n log n, which on a log-log plot has a slope a little above 1 (1.2).
- Absolute time: at n = 6400, W is about 21 800 and the DP has about 1.4 x 10^8 cells. At the roughly 100 ns per
  cell seen in the smoke run this is 14 s (1.3). Greedy at n = 6400 is about 80 000 comparisons, a few
  tens of milliseconds, so the ratio is a few hundred (1.4).
- Cells: the number of cells is the sum over the crates of (W - weight + 1) = n x W - total weight + n, which is
  just below n x W because crate weights are small compared with W (1.5).
- Memory: the back-tracking needs one byte per (crate, capacity) cell, which is the n x (W + 1) bytes of the
  table; the temporary rows add a little (1.6). The greedy rule keeps two lists of n references while merging, a filtered list
  and the output, a few dozen bytes per crate (1.7).
- In `A-scale-W` the crates are fixed, so only the width of the table changes: the work is linear in W. The fixed
  cost of handling each crate (about 1600 list operations) is not proportional to W and pulls the slope slightly
  below 1 for small W (1.8). The greedy rule does not depend on W (1.9).
- Quality: ratio-greedy only loses value when a crate with a good ratio blocks a combination that fills the truck
  better, which happens often in tiny cases (8 to 20 crates) and rarely in cases with hundreds of crates, because many
  small crates fill the gaps (1.10, 1.11). Trap 47 is built so that the bait crate has the best ratio: with capacity 20,
  bait 61 against 2 x 55 = 110 gives 0.55 (1.12). The claims were computed by exhaustive search by their authors; a
  correct DP must reproduce them (1.13); a miss would mean a bug of mine or a defective case.

**After the run** (Ayna's laptop, on or before 2026-11-20; full table in `results/predictions-vs-measurements-AD.md`): 10 of 13 inside the tolerance, misses 1.1, 1.2 and 1.3.

*What changed between the two runs.* In the first run on this laptop the speed changed while the round was running: time per DP cell was 200, 181, 145, 139 ns for n = 200 to 1600, then 253 ns and 398 ns, with an IQR of 80 % of the median at n = 3200, so 1.1, 1.2 and 1.3 all missed.
I did not establish the cause (laptop power or heat management, other programs, or Windows moving the run between fast and slow cores of this hybrid Intel CPU). After connecting the charger and setting the power mode to best performance, the repeat gave 94.5, 88.8, 86.6, 83.3 and 83.8 ns per cell for n = 200 to 3200: the speed is now almost constant.
That is evidence for a power or heat effect, not proof; I changed two things at once (charger and power mode) and did not test them separately. One point is still disturbed: n = 6400 cost 194 ns per cell with an IQR of 8.8 s (28 % of the median), so the speed changed again during that longest run. In the W sweep the first point (W = 522, right after the 6400 run) cost 195 ns per cell, the other five 85 to 99 ns.
The operation counts are exact and identical in both runs.
- **1.1 (hit now, slope 2.215 +- 0.284, range 1.75 to 2.25; first run 2.26 +- 0.36).** The slope is inflated by the 6400 point. Without it, the five sizes 200 to 3200 give 2.05 +- 0.21. The counted cells have slope 2.08 +- 0.12, not 2.0, because W per crate is not constant (3.4, 3.4, 2.9, 4.2, 4.2, 3.9 kg per crate for the six sizes, since the joined tier L cases differ): a real, small modelling error in my prediction of the operation count. Time against cells has slope 1.07 +- 0.14, so the counted operations explain the time.
- **1.2 (hit now, greedy slope 1.219, range 0.9 to 1.3; first run 1.44).** The greedy operations have slope 1.150 +- 0.016, as predicted. The interval of the time slope is +- 0.28, so this is a weak confirmation.
- **1.3 (still a miss, 31.3 s against 14 s, range 9 to 21).** The cell count was 161 million, not my 140 million. Only the 6400 point is out of line: at the 84 ns per cell of n = 1600 and 3200, 161 million cells would take about 13.5 s, which is what I predicted. That is arithmetic, not a measurement; the measured value is 31.3 s and it stays a miss.
  The lesson: a long run on a laptop can change speed in the middle, and one timing of a 30 s run is not enough to separate this from the algorithm. In the first run I also used a constant (100 ns per cell) from a cloud machine; on this laptop in the good state it is 85 ns, close.
- **1.4 (hit, 778 against 450).** A hit with a wide tolerance; I would not read much into it.
- **1.5, 1.6, 1.7, 1.8, 1.9** hit. 1.8: DP slope in W is 0.858 +- 0.267 (first run 0.995 +- 0.037); the cells have slope 1.005, and the lower time slope comes from the first point (W = 522, 195 ns per cell), which is out of line. 1.7: greedy memory is 102 bytes per crate against 80 predicted (I counted too few lists of n references; not profiled further).
  1.9 is a hit only because of the tolerance: the greedy time has slope -0.08 +- 0.43 with R^2 = 0.07 (the operation count is exactly constant; the times jump between 4 and 10 ms), which says "no clear dependence on W" and nothing more.
- **1.10 to 1.13 (quality, machine independent, identical to the first run on the cloud machine):** greedy is not optimal in 65 % of tier S cases (55 % predicted), mean greedy/DP is 0.9985 on tiers M and L, 0.561 on trap 47, and the DP equals the claim in 20 of 20 tier S cases.
  A surprise: a few tier S cases of other groups give greedy/DP of only 0.58, nearly as bad as the trap cases (Figure A4).

---

## Round 2: module A, small inputs, DP and greedy against brute force

**Date and time:** 2026-11-16 18:41 UTC (before running round 2)

**Experiment:** `A-small-n`: n = 8, 11, 14, 17, 20 crates, pooled from tier S cases; algorithms DP, greedy and brute force
(all 2^n subsets in Gray-code order).

**Which algorithm I expect to win:** greedy is fastest at every size. Between the two exact methods the DP wins from
about n = 8 on, and by a factor of more than 100 at n = 20.

| id | prediction | tolerance |
|---|---|---|
| 2.1 | brute force: time grows by a factor 2.0 per extra crate (semi-log fit) | 1.85 to 2.15 |
| 2.2 | brute force time at n = 20 is 0.17 s | 0.10 to 0.30 s |
| 2.3 | DP time / greedy time, mean over the five sizes, is 4 | 2 to 8 |
| 2.4 | the smallest n at which DP is faster than brute force is 8 (partly informed by the smoke run) | 8 to 11 |

**Reasoning.** Brute force evaluates 2^n subsets, so the time doubles per crate: base 2 (2.1). One Gray-code step
costs a few hundred nanoseconds in Python, and 2^20 = 1 048 576 steps give about 0.17 s (2.2). At these sizes the
DP costs a fixed overhead per crate (list slicing) and the table has only about 60 to 100 cells per crate, so it is a small
multiple of the sort-based greedy rule (2.3). For n = 8 both finish in tens of microseconds and the exponential
has not taken off yet, so the crossover sits at the bottom of the range (2.4).

**After the run** (Ayna's laptop, first slower run; round 2 has not been repeated yet): 3 of 4 inside the tolerance, miss 2.2.
- **2.2 (miss).** Brute force at n = 20 took 0.585 s against 0.17 s predicted; the first run on the cloud machine gave 0.165 s. The factor 3.6 is a machine and speed-state difference, not an error in the 2^n argument (in this round the DP costs about 500 ns per cell, against about 85 ns in the repeated round 1, so the round ran in the slow state): 2.1 hit (base 2.02, interval 1.94 to 2.11) and exactly 2^n subsets were counted at every size.
- 2.3 hit (DP / greedy 3.9 on average). 2.4 hit (n = 8: DP 89 us, brute force 115 us, ratio 1.29); this prediction was partly informed by the smoke run and I did not test sizes below 8.
- At n = 20 the DP is 878 times faster than brute force.

---

## Round 3: module D, growth in m, and effect of the urgency order

**Date and time:** 2026-11-16 18:42 UTC (before running round 3)

**Experiments:** `D-scale-m` (m = 250, 500, 1000, ..., 64000 alarms, doubling, pooled from consecutive tier L cases
with ticks shifted past the previous case); `quality-D.csv` (samples of tiers S, M, L, X: urgency order against first-come-first-served).

**Which algorithm I expect to win:** the binary heap is faster from m = 500 on and the gap grows with m; at m = 250 they are
about equal. They give the same release order, so there is no difference in *outcome* between heap and scan, only in cost.

| id | prediction | tolerance |
|---|---|---|
| 3.1 | heap: log-log slope of time against m is 1.1 | 0.95 to 1.3 |
| 3.2 | scan: log-log slope of time against m is 1.9 | 1.7 to 2.1 |
| 3.3 | scan: key comparisons at m = 8000 are 10.9 million | 6 to 16 million |
| 3.4 | scan: time at m = 64000 is 51 s | 25 to 100 s |
| 3.5 | heap: time at m = 64000 is 0.5 s | 0.25 to 1.0 s |
| 3.6 | scan time / heap time at m = 250 is 1.2 (partly informed by the smoke run) | 0.6 to 2.0 |
| 3.7 | the maximum backlog is 0.33 m at m = 64000 | 0.20 m to 0.45 m |
| 3.8 | heap: ops / (m log2 m) at m = 64000, divided by the same ratio at m = 250, is 1.0 | 0.75 to 1.25 |
| 3.9 | heap: peak memory beyond the input at m = 8000 is 250 bytes per alarm | 120 to 400 |
| 3.10 | mean wait of all alarms is the same under urgency order and first-come-first-served (difference 0) | exactly 0 |
| 3.11 | tier L: mean wait of priority 9 and 10 alarms is 80 times higher under first-come-first-served than under urgency order | 20 to 1000 |

**Reasoning.**
- The alarm rate is 1.2 to 1.8 per tick against one release per tick, so the backlog keeps growing, in a pooled stream
  to about a third of m (3.7). The scan looks at the whole backlog at every tick: total work = sum of backlogs, about
  0.17 m^2 comparisons (mean backlog is half of the final one), so 0.17 x 64 x 10^6 = 10.9 million at m = 8000 (3.3),
  and quadratic growth with slope slightly below 2 because small m have a small backlog (3.2). At about 70 ns
  per comparison in Python, m = 64000 needs 0.17 x 4.1 x 10^9 x 70 ns = 50 s (3.4).
- The heap costs O(log backlog) per alarm: m log m growth, slope a little above 1 (3.1), about 4 to 8 microseconds
  per alarm, so about 0.5 s at m = 64000 (3.5). Because the backlog is proportional to m, log(backlog) is about log m and the
  operations per (m log2 m) are nearly constant (3.8).
- Memory beyond the input is dominated by the answer itself: one (id, tick) tuple per alarm plus a dictionary of arrival ticks,
  around 100 to 250 bytes per alarm, and the heap or list adds a backlog of tuples (3.9).
- Every policy that releases one alarm per tick whenever somebody is waiting uses exactly the same release ticks, and
  total wait = sum of release ticks - sum of arrival ticks; so the total, and the mean over all alarms, is
  identical for any such policy (3.10): a conservation law. What changes is *who* waits. Priority 9 and 10 make up
  about 20 % of the alarms, which is less than one per tick, so under the urgency order they are answered within a few ticks,
  while under first-come-first-served they wait behind the whole backlog, hundreds of ticks (3.11).
- At m = 250 the backlog is under 50 and a scan of 40 entries costs about as much as the overhead of heap
  operations (3.6).

**After the run** (Ayna's laptop, repeated on 2026-11-20 with the charger connected and power mode best performance): 10 of 11 inside the tolerance, miss 3.8.
- **3.8 (miss, 1.28 against a limit of 1.25).** Operation counts do not depend on the machine, so this is a real modelling error. I predicted that operations divided by (m log2 m) stay constant. They grow from 2.47 at m = 250 to 3.17 at m = 64000.
  My model forgot that the backlog starts at zero and then grows. A pop costs about log2 of the current backlog, so the average over the run is about log2(0.33 m) - 1.4 = log2 m - 3.0 rather than log2 m. The ratio (log2 m - 3.0) / log2 m is 0.62 at m = 250 and 0.81 at m = 64000, a growth by a factor of 1.31; measured 1.28. So the heap is m log m with a negative constant term.
- **3.5 (hit now, heap at m = 64000 took 0.265 s, range 0.25 to 1; first run 1.04 s).** In the first run the heap time jumped 4.5 times for a doubling of m (speed change). In the repeat the heap times are smooth except at m = 4000 (24 ms, with an IQR of 6.5 ms; m = 8000 took 25 ms), which I read as one disturbed measurement, not as algorithm behaviour. The scan/heap time ratio for the nine sizes is 1.2, 1.7, 2.7, 4.7, 4.1, 16, 29, 57, 113; the dip at 4000 comes from that heap time. The ratio grows with m, as the shapes m log m and m^2 predict.
- **3.1 (hit).** The heap slope is 1.124 +- 0.112 (first run 1.26); the operations have slope 1.164 +- 0.028, which is the m log m shape I expected. **3.2:** scan slope 1.961 +- 0.054, comparisons 1.99. **3.3:** 10.7 million comparisons at m = 8000 (10.9 predicted).
- **3.4 (hit, 29.8 s against 51, range 25 to 100).** A hit by tolerance, with a relative error of 71 %: I used 70 ns per comparison, and the repeated round gives 37 to 44 ns (the first laptop run gave 76 ns, the first cloud run 51 ns). The scan times now follow the comparison counts closely (time against operations has slope 0.985 +- 0.025).
- 3.6 hit (1.17), 3.7 hit (backlog 0.331 m), 3.9 hit (185 bytes per alarm; heap and scan memory differ by under 0.1 %), 3.10 hit (the mean wait of all alarms is identical under both orders in all 62 cases), 3.11 hit with a 81 % error (ratio 429 against 80 predicted; on tier L the priority 9 and 10 alarms wait 1.5 ticks under the urgency order and 639 under first-come-first-served).

---

## Round 4: module D, the 5 minute rule (DNF)

**Date and time:** 2026-11-16 18:43 UTC (before running round 4)

**Experiment:** `D-dnf`: one run of the scan baseline and the heap at m = 256000 alarms (pooled tier L streams).

**Which algorithm I expect to win:** the heap, which finishes; the scan does not finish in 300 s and is recorded as DNF.

| id | prediction | tolerance |
|---|---|---|
| 4.1 | the scan at m = 256000 is a DNF (passes 300 s) | DNF |
| 4.2 | the missing point, extrapolated from the log-log fit on m up to 64000, is 670 s | 400 to 1100 s |
| 4.3 | the heap at m = 256000 takes 2.5 s | 1.2 to 5 s |

**Reasoning.** Quadratic growth from 51 s at m = 64000 gives 51 x 16 = 816 s at 4 times the size; with the slope a bit below 2, 670 s
(4.2). That is above 300 s, hence DNF (4.1). The heap is about 5 times 0.5 s with the logarithmic factor (4.3).

**After the run** (Ayna's laptop; round 4 has not been repeated yet and comes from the first, slower run, except that the extrapolation in 4.2 now uses the repeated round 3): 2 of 3 inside the tolerance, miss 4.2.
- 4.1 hit: the scan at m = 256000 passed 300 s and is recorded as DNF. 4.3 hit: the heap took 2.40 s (2.5 predicted). Caution: this number comes from the slower run. The repeated round 3 gives 0.265 s at m = 64000, and 2.40 s at 256000 alarms would be 9 times that for 4 times the alarms, so a repeat of round 4 is likely to give about 1.2 s and change this hit into a miss.
- **4.2 (miss, extrapolated 390 s against 670 s, range 400 to 1100).** The fitted line through the nine sizes of the repeated round 3 gives 390 s; plain quadratic growth from the last measured size (29.8 s at m = 64000, times 16) gives about 477 s. The miss is small (the range starts at 400) and comes from my constant (70 ns per comparison, measured here: about 40 ns). Both estimates are above 300 s, so the DNF conclusion holds, but it is close enough that it should be confirmed by the repeated round 4 (the DNF row itself is a measurement: the scan passed 300 s).
  The largest size that finished for the scan is m = 64000. The extrapolated figure is an estimate, not a measurement.

---

## Summary after all rounds

31 numerical predictions, with rounds 1 and 3 repeated on 2026-11-20 (charger connected, best performance) and rounds 2 and 4 from the first laptop run: 27 inside the tolerance, 4 misses (1.3, 2.2, 3.8, 4.2).
In the first laptop run alone it was 24 hits and 7 misses (1.1, 1.2, 1.3, 2.2, 3.5, 3.8, 4.2).
- **Real modelling errors:** 3.8 (I forgot that the backlog starts at zero, so the heap work per alarm is log2 m - 3, not log2 m) and, in a small way, 1.1 (the capacity per crate of the pools is not constant, so the cell count grows with slope 2.08, not 2.0; the hit there is by tolerance).
- **Caused by speed and constants of the machine:** 1.3 (the n = 6400 run changed speed during the run), 2.2 (round 2 ran in the slow state), 4.2 (my 70 ns per comparison against about 40 ns measured). Moving from the first to the repeated run turned 1.1, 1.2 and 3.5 into hits, which supports the explanation by machine speed. Predictions of counts, memory and quality
  (1.5, 1.6, 2.1, 3.3, 3.7, 3.10, 1.10 to 1.13) were close or exact in every run on both machines.
- **Weak hits:** some tolerances (1.4, 1.9, 3.4, 3.11) were wide enough to hit without much understanding; 3.4 is a hit with a relative error of 71 %.
- **Still open:** rounds 2 and 4 should be repeated in the same power state as rounds 1 and 3; 2.2 and 4.3 are the two predictions that this is likely to change.
- **What I would do differently:** predict ratios and operation counts, and calibrate any absolute time on the same machine and in the same power mode before predicting it; run every timing round with the laptop connected to power in best performance mode, and run the longest sizes more than once.


---

## Module C (rescue scheduling), Adan (24I-3037-C): notes before the rounds

Master dataset: master_release_v1. Group seed 41 (sample positions 41 mod 7 = 6, 13, 20, ...). Time unit: seconds on one core,
median of 5 runs after one discarded warm-up run. Pools: consecutive cases of one tier are joined, the windows of the i-th case are
shifted by 1440 * i minutes, ids are renumbered from 1, the pool is cut after the first n windows (`experiments/sampleC.py`).

**Order of events.** All four entries below were written together in one sitting on 2026-11-20, saved at 12:21 (UTC+5, laptop clock), after
`src/modules/rescue.py`, its tests and its fault-injection tests were finished and before `experiments/runC.py`, `analyzeC.py` and
`predictionsC.py` existed. No experiment of module C had been run. The entries were first written in their own files (`predlogC.md`, `predlogG.md`, now merged into this file) and those files were committed together with the module, after the runs; the timestamps below and the fact that the run scripts did not exist yet are the only evidence of the order of events.

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

## Module C, round 1: growth in n of the greedy rule, the DP with binary search and the O(n^2) DP

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

## Module C, round 2: quality of the greedy rule against the DP (count and value), on the master data

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

## Module C, round 3: small inputs, DP and greedy against brute force

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

## Module C, round 4: the five minute rule (DNF)

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

## Module C, summary after all rounds (2026-11-20)

37 numerical predictions, 31 inside the tolerance, **6 misses: C1.8, C1.14, C2.5, C2.6, C2.7, C2.8**.
- Predictions about counts and exponents (C1.4 to C1.6, C1.11, C2.1 to C2.3, C3.2, C3.7) were close or exact.
- Predictions about absolute times (C1.7 to C1.9, C4.2, C4.3) were all too low by about a factor of 2 (the laptop is about twice as slow as I assumed from Ayna's constants on her VM): four were hits at 43 to 50 % error and one (C1.8) a miss. Hits at the edge of the range (C1.7, C1.9, C1.16, C4.3) are weak evidence that I understood the constants.
- The two real modelling errors: the number of windows the greedy rule chooses (C1.14, a factor of 2.3) and the size of the value the greedy rule gives up (C2.5 to C2.8: it gives up 16 to 28 %, not 30 to 42 %).
- **Where the measurements were made.** On the author's laptop (Intel64 Family 6 Model 142, 8 logical CPUs, Windows 10, Python 3.14.6, one thread, see `results/environmentC.json`). I could not verify that it was on the charger and in best-performance mode, so the group should repeat the runs under those conditions and replace the numbers here if they differ.


---

## Module C, what each round can show and what it cannot

- Round 1 shows the shape of the growth of three algorithms on the pooled windows of the master data. It cannot show how they behave on other window distributions: the pools keep the data's density
  (about 1.2 window starts per minute inside a day) and shifting joined cases by 1440 minutes keeps them apart, so the overlap structure is that of one case, never of 3000 windows inside one day.
- Round 2 is a sample of 62 cases of one dataset, not a guarantee. A ratio of 0.58 says "about 40 % of the value is lost on these cases", not a bound.
- Round 3 uses pooled tier S cases (up to 20 windows), so the totals are small and nothing about the brute force's pruning matters (it has none).
- Round 4 is one run and an extrapolation.


---

## Module G (chains and cuts), Adan (24I-3037-C): notes before the rounds

Master dataset: master_release_v1 (folder `MASTER`). Group seed 41 (sample positions 41 mod 7 = 6, 13, 20, ...). Time unit: seconds on one core,
median of 5 runs after one discarded warm-up run. How the larger instances are built (`experiments/sampleG.py`):
chains: the dimension lists of consecutive tier L cases are concatenated and cut after n + 1 dimensions (any list of whole numbers >= 1 is a chain);
drums: the first L prices of the price table of case 12-47 (the first case of the seed-41 samples of tier L and X with 2000 prices); tables of different cases are never joined.

**Order of events.** The four entries below were written together on 2026-11-20 at 13:20 (UTC+5, laptop clock), after `src/modules/chains.py`, its tests
(63 tests) and the fault-injection file were written and before `runG.py`, `analyzeG.py` and `predictionsG.py` existed. No experiment of module G had been run.
The entries were first written in their own files (`predlogC.md`, `predlogG.md`, now merged into this file) and those files were committed together with the module, after the runs; the timestamps below and the fact that the run scripts did not exist yet are the only evidence of the order of events.

**What I knew before writing (honest note).**
1. The first full run of the unit tests printed the durations of the slowest tests, and an early version of two of them was heavy: a memoised recursion on a 700-matrix chain
   (about 57 million split candidates) together with the DP on the same chain took 102 s, and the DP alone on a 700-matrix chain 19 s; a DP on a drum of length 3000 (4.5 million candidates) took about 1 s.
   From this I took about **0.33 microseconds per split candidate for the chain DP and about 1.5 microseconds for the memoised recursion** (two calls per candidate), and about 0.2 microseconds per candidate for the drum DP.
   My first guess, before seeing these numbers, was 0.22 and 0.45 microseconds; the absolute times below are therefore *calibrated* on what I had seen and are weaker evidence than a prediction made without it.
2. From module C on this laptop I knew that one inner-loop step of a plain Python loop with two comparisons costs about 130 ns.
3. I read the sizes of the master data (matrices per case: tier S 4 to 8, M 15 to 60, L 100 to 300, X 100 to 300; drum length: S 5 to 14, M 40 to 200, L 500 to 2000, X 500 to 2000),
   the claims `drum_opt` of tier S, and the generator code of the data: dimensions are uniform in 2 to 100; the price of length j is round(scale * j^0.7 + noise) with noise uniform in -5 to 15, capped to 1..500, scale = (150 to 330) / L^0.7.
   I did not run the algorithms on any instance of the experiments before writing, apart from the two fixtures of the tests (27 cases) and the textbook examples.
4. The counts of operations (cells, candidates, calls, enumerated) follow from the algorithms and are exact predictions.

**Added after the full run (disclosure).** After this file was saved and before the full run I ran `runG.py --quick` once (tiny sizes, 12 quality cases) to test the scripts; at that moment the fault-injection suite was running in the background, so its timings were inflated and I ignored them. It also showed quality rows (for example a tier S chain ratio of 5.7 and greedy = DP in the first cases). I did not change any prediction above. The misses G3.3 and G3.7 are in the direction that this run showed.

**Operations counted** (the statement's families; see the module docstring): selection and tabulation = table `cells` computed, split `candidates` evaluated, recursive `calls`;
ordering (greedy cut) = `comparisons` and `moves` of our merge sort plus `items_examined`; all-bracketings or all-cuts = `enumerated`; preprocessing (the validation pass) separately in `pre`.
The `ops` column of `results.csv` is `comparisons + moves + items_examined + cells + candidates + enumerated` (the recursive `calls` and `pre` are not in it); the breakdown, with `calls`, is in the column `note`.

---

## Module G, round 1: growth in n of the chain DP and the memoised recursion (n^3)

**Date and time:** 2026-11-20 13:20 UTC+5 (before running round 1)

**Experiment:** `G-chain-n`, n = 10, 20, 40, 80, 160, 320, 640 matrices (7 sizes, ratio 2), pooled from tier L cases starting at the first case of the sample. Algorithms `dp` and `memo`.
(n = 640 is beyond the n <= 300 of the data on purpose: a chain is any list of dimensions, and the fits need the range.)

**Which algorithm I expect to win:** `dp`, at every size, by a factor that grows to about 4.5: both do exactly the same cells and candidates, but the recursion pays two function calls per candidate. They return the same bracketing and cost.

| id | prediction | tolerance (counts as a hit) |
|---|---|---|
| G1.1 | dp: log-log slope of time against n is 2.85 | 2.6 to 3.1 |
| G1.2 | memo: log-log slope of time against n is 2.85 | 2.6 to 3.1 |
| G1.3 | dp: `ops` at n = 320 is 5 512 320 (51 040 cells + 5 461 280 candidates) | exactly |
| G1.4 | memo: recursive calls at n = 320 are 10 922 561 (1 + 2 x 5 461 280) | exactly |
| G1.5 | dp: time at n = 640 is 14 s | 8 to 28 s |
| G1.6 | memo: time at n = 640 is 65 s | 30 to 140 s |
| G1.7 | memo time / dp time at n = 640 is 4.5 | 2.5 to 7.5 |
| G1.8 | dp and memo return the same cost at every size (share of sizes) | exactly 1.0 |
| G1.9 | dp: peak memory beyond the input at n = 160 is 40 bytes per n^2 | 25 to 70 |
| G1.10 | memo peak memory / dp peak memory at n = 160 is 0.8 | 0.5 to 1.1 |
| G1.11 | dp: time at n = 160 is 0.23 s | 0.12 to 0.5 s |
| G1.12 | dp: time at n = 640 / time at n = 320 is 8 | 6.5 to 10 |
| G1.13 | dp: log-log slope of the counted operations against n is 2.95 | 2.90 to 3.00 |

**Reasoning.**
- The DP fills n (n - 1) / 2 cells and tries (n^3 - n) / 6 split candidates: at n = 320, 51 040 cells and 5 461 280 candidates, so `ops` = 5 512 320 (G1.3). The memoised recursion reaches the same cells and candidates, and every candidate calls the function twice
  (once for each part), plus the top call: 1 + 2 x 5 461 280 = 10 922 561 (G1.4).
- Slope of the operations (G1.13): n^3 / 6 plus the quadratic number of cells; between n = 10 (210 operations) and n = 640 (43.9 million) the log-log slope is 2.95. The time slope is below 3 because the table allocation and the validation are quadratic and linear, which matter at the small sizes: 2.85 (G1.1, G1.2).
- Absolute time (calibrated, see the note above): 43.7 million candidates x 0.33 microseconds = 14 s for the DP (G1.5), 43.7 million x 1.5 microseconds = 65 s for the recursion (G1.6), ratio 4.5 (G1.7).
  Doubling n multiplies the candidates by 8: 8 (G1.12); the time at n = 160: 0.68 million candidates x 0.33 microseconds = 0.23 s (G1.11).
- Memory (G1.9): the DP keeps three tables of (n + 2)^2 references (cost, its transpose, split): 3 x 8 bytes per n^2, plus the integers of the costs (about 32 bytes each for n^2 / 2 cells, shared between the two cost tables): about 40 bytes per n^2. The memoised recursion has two tables only and the result strings are small: 0.8 (G1.10).
  The memoised recursion runs in a thread for n > 500 and `tracemalloc` does not count the thread stack, which does not matter at n = 160.

**After the run** (written 2026-11-20 after round 1; full table in `results/predictions-vs-measurements-G.md`): 13 of 13 inside the tolerance. This is a weaker result than it looks: the exact counts were derived from the algorithms, and the absolute times were calibrated on durations I had seen (see the note at the top).
- **Exact counts (G1.3, G1.4).** `ops` of the DP at n = 320: 5 512 320, and 10 922 561 recursive calls of the memoised recursion: both exactly as predicted. The counted operations grow with slope 2.950 +- 0.027 (2.95 predicted), and the time grows in proportion to them: slope of time against operations 0.98 for the DP and 0.99 for the recursion.
- **Slopes of the time:** dp 2.89 +- 0.15, memo 2.92 +- 0.28 (2.85 predicted for both). The interval of the recursion is wide because of noisy points (see below).
- **G1.5 to G1.7 (times, hits but not equally good).** dp at n = 640: 13.4 s (14 predicted). memo at n = 640: 48.7 s (65 predicted, 33 % error), ratio 3.6 (4.5 predicted). So the recursion costs about 3.6 DP-times, i.e. about 1.1 microseconds per candidate, not the 1.5 that I had taken from the slow test: that value included the thread route and a loaded machine.
  G1.12: doubling n from 320 to 640 multiplied the DP time by 9.0 (8 predicted, range 6.5 to 10): the 1.49 s at n = 320 is a little too fast for its operations (cache effects of the larger tables are one explanation; I did not test it).
- **Noise.** The IQR is large at some sizes: DP at n = 320: median 1.49 s, IQR 0.30 s; memo at n = 320: 5.72 s, IQR 1.73 s; memo at n = 40: 32.0 ms, IQR 36.7 ms, which makes the ratio memo / dp 11.5 at n = 40 against 3 to 4 at all other sizes. I did not repeat these runs; I believe another process on the laptop was responsible (I could not check that), so the point at n = 40 should not be read.
- **Memory (G1.9, G1.10):** 42 bytes per n^2 for the DP at n = 160 (40 predicted) and the recursion needs 0.80 of that (0.8 predicted): two tables instead of three, as reasoned. At n = 640 the memory was not measured (a run is longer than 8 s, `tracemalloc` is too slow).


---

## Module G, round 2: growth in L of the drum DP, the memoised recursion and the greedy cut (L^2)

**Date and time:** 2026-11-20 13:20 UTC+5 (before running round 2)

**Experiment:** `G-drum-L`, L = 63, 125, 250, 500, 1000, 2000 (6 sizes, ratio 2), the first L prices of the price table of case 12-47. Algorithms `dp`, `memo` (a recursion 2 000 calls deep, run in a thread with a large stack) and `greedy`.

**Which algorithm I expect to win:** `greedy` is by far the fastest (it sorts L pieces once), `dp` is the shipped method and `memo` is about four times slower than `dp` with the same answer. On the data the greedy rule is almost always optimal (see round 3), so the time of the DP buys little here.

| id | prediction | tolerance |
|---|---|---|
| G2.1 | dp: log-log slope of time against L is 1.95 | 1.8 to 2.1 |
| G2.2 | memo: log-log slope of time against L is 1.95 | 1.8 to 2.1 |
| G2.3 | greedy: log-log slope of time against L is 1.1 | 0.9 to 1.3 |
| G2.4 | dp: `ops` at L = 2000 is 2 003 000 (2 000 cells + 2 001 000 candidates) | exactly |
| G2.5 | memo: recursive calls at L = 2000 are 2 001 001 | exactly |
| G2.6 | dp: time at L = 2000 is 0.4 s | 0.2 to 0.9 s |
| G2.7 | memo: time at L = 2000 is 1.7 s | 0.8 to 4 s |
| G2.8 | greedy: time at L = 2000 is 7 ms | 3 to 20 ms |
| G2.9 | memo time / dp time at L = 2000 is 4 | 2 to 7 |
| G2.10 | dp time / greedy time at L = 2000 is 55 | 15 to 200 |
| G2.11 | dp and memo return the same price and the same number of pieces at every size (share of sizes) | exactly 1.0 |
| G2.12 | dp: peak memory beyond the input at L = 2000 is 50 bytes per unit of length | 25 to 120 |

**Reasoning.**
- For every length l the DP tries l first pieces: L (L + 1) / 2 = 2 001 000 candidates and L = 2000 cells (G2.4); the recursion makes one call per candidate and one for the top: 2 001 001 (G2.5). Both are quadratic with a slope just under 2 because of the linear validation (G2.1, G2.2).
  The greedy cut sorts L pieces (L log L comparisons and moves) and then walks the list: slope a little above 1 (G2.3).
- Times (calibrated): 2 million candidates x 0.2 microseconds = 0.4 s (G2.6); the recursion adds one call per candidate (about 0.65 microseconds from the chain observation: 1.5 versus 0.33 for two calls): 1.7 s (G2.7), ratio 4 (G2.9).
  Greedy at L = 2000: about 20 000 comparisons and 22 000 moves of the merge sort at about 150 ns plus the validation: about 7 ms (G2.8), so the DP is about 55 times slower (G2.10).
- The deep recursion: depth 2002 is above the default limit of Python (1000); the module raises the limit for the call and uses a thread with a large stack, so all sizes must finish with status OK and the same answer as the DP (G2.11).
- Memory (G2.12): three lists of L + 1 entries (best, pieces, first piece) and the list of prices of the validation, plus the integers: about 100 kB for L = 2000.

**After the run** (written 2026-11-20 after round 2): 12 of 12 inside the tolerance, but two of them only because the tolerance was wide.
- **Exact counts (G2.4, G2.5):** 2 003 000 operations of the DP and 2 001 001 calls of the recursion at L = 2000, exactly. The recursion, 2 002 calls deep, finished with the same price and the same pieces as the DP at all 6 sizes (G2.11): the raised recursion limit and the thread with a large stack work on this machine.
- **Slopes:** dp 2.03 +- 0.10, memo 2.02 +- 0.05, greedy 1.16 +- 0.03 (1.95, 1.95 and 1.1 predicted). The time slopes of the quadratic methods are slightly above 2, although their operations have slope 1.988: at these sizes the larger tables are a little slower per operation. I did not test why.
- **Times:** dp at L = 2000 0.35 s (0.4 predicted), memo 1.17 s (1.7 predicted, ratio 3.4 against 4 predicted).
- **G2.8 and G2.10 (weak hits).** The greedy cut took 13.8 ms at L = 2000, twice my 7 ms (49 % error); so the DP was only 25 times slower than greedy, not 55 (the tolerance 15 to 200 is what made it a hit: 118 % error). My estimate of the cost of the merge sort of tuples (about 150 ns per operation) was too low: 41 110 counted operations took 13.8 ms, about 340 ns each, because every comparison calls a Python function that unpacks two tuples.
- **G2.12 (weak hit, 52 % error):** 105 bytes per unit of length for the DP against 50 predicted (range 25 to 120). I forgot the tuple of pieces and the validation table of prices (a second list) when adding up.


---

## Module G, round 3: quality of the greedy cut against the DP, and of the best bracketing against multiplying left to right

**Date and time:** 2026-11-20 13:20 UTC+5 (before running round 3)

**Experiment:** `quality-G.csv`: samples of tier S (20 cases), M (20), L (10) and X (12), seed 41. For every case: the price of the greedy cut and of the DP cut of its drum (and the claim `drum_opt` for tier S),
the number of pieces, and, for its matrix chain, the cost of the optimal bracketing against the cost of multiplying from left to right, ((A1 A2) A3) ... An.

**Which algorithm I expect to win:** the DP is optimal by construction (and must reproduce the claim of tier S); the greedy cut will be optimal or within a very small distance of the optimum in most cases. The reason is the shape of the data:
the price of length j is about scale x j^0.7 plus noise, so the price per length falls with the length and the best price per length is almost always at length 1 or 2; a greedy cut that repeats the best piece is then optimal except for a remainder.

| id | prediction | tolerance |
|---|---|---|
| G3.1 | tier S: the DP price equals the claim `drum_opt` in every case (share) | exactly 1.0 |
| G3.2 | all sampled cases: the greedy price is never above the DP price (share of cases) | exactly 1.0 |
| G3.3 | all sampled cases: share of cases in which the greedy price equals the DP price | 0.85 (0.65 to 0.97) |
| G3.4 | all sampled cases: mean greedy price / DP price | 0.998 (0.990 to 1.0) |
| G3.5 | all sampled cases: worst greedy price / DP price | 0.93 (0.80 to 0.99) |
| G3.6 | all sampled cases: mean (pieces of the DP cut) / L | 0.75 (0.45 to 1.0) |
| G3.7 | tier S: mean (cost of left to right) / (cost of the optimal bracketing) | 1.35 (1.05 to 2.2) |
| G3.8 | tier L: mean (cost of left to right) / (cost of the optimal bracketing) | 6 (2 to 25) |

**Reasoning.**
- G3.1, G3.2: the DP reproduces exhaustive-search optima (as the DP of module A did); no cut can beat the optimum.
- G3.3 to G3.5: if the best price per length is at length k and k divides L, the greedy cut repeating it is optimal; if k does not divide L, the remainder is filled by worse pieces and the optimum may rearrange.
  I estimate that the best ratio is at length 1 in about 60 % of the cases (then greedy is optimal for sure: no piece has a better ratio), and that in the other cases it fails about a third of the time: not optimal in about 15 % of the cases, by a small amount.
  The loss can be a few percent in a small drum (tier S, L = 5 to 14), hence a worst case of about 0.93 and a mean of 0.998. These three are guesses, the second and third with wide tolerances.
- G3.6: pieces of length 1 (price per length best at 1) or of length 2 (about half as many pieces): 0.75 is the midpoint, a guess.
- G3.7, G3.8: for random dimensions 2 to 100, multiplying from left to right costs p0 times the sum of p(k) p(k+1), while the optimum uses small dimensions as pivots; for 4 to 8 matrices the difference is small (a few tens of percent),
  for 100 to 300 matrices a factor of several. These two numbers are the weakest of the round (I have no model of the ratio, only the order of magnitude), hence the wide tolerances.

**After the run** (written 2026-11-20 after round 3): 6 of 8 inside the tolerance, **2 misses: G3.3 and G3.7**.
- **Exact predictions held:** the DP price equals the claim `drum_opt` in 20 of 20 tier S cases (G3.1) and the greedy price is never above the DP price in 62 of 62 cases (G3.2).
- **G3.3 (miss: the greedy cut is optimal in 61 of 62 cases = 0.984, predicted 0.85, range 0.65 to 0.97).** I was right about the reason (the price per length falls with the length because the prices follow j^0.7) but too pessimistic about the cases in which the best piece does not divide L:
  the greedy cut equals the DP price in all 20 tier S, 20 tier M and 10 tier L cases and in 11 of 12 tier X cases. The only case where it is not optimal is the tier X case 15-49 (L = 513), at 0.977 of the optimum. So G3.4 (mean 0.9996, predicted 0.998) and G3.5 (worst 0.977, predicted 0.93) were hits with a ratio too low.
  My reasoning about when the remainder loses was wrong: a remainder is filled with pieces of a slightly worse ratio, but the optimum rarely finds a better combination because the ratios of the short pieces are close to each other. I did not examine the cases further, so this explanation is untested.
- **G3.6 (hit):** the DP cut has 0.72 of L pieces on average (0.75 predicted): pieces of length 1 and 2 dominate, as reasoned (0.69 in tier S, 0.82 in tier X).
- **G3.7 (miss: tier S mean left-to-right / optimal = 4.53, predicted 1.35, range 1.05 to 2.2).** I had no model and guessed "a few tens of percent" for 4 to 8 matrices; the mean is dominated by large ratios (15.4, 14.7, 14.3, 9.1, 6.2, 5.7 in 6 of 20 cases; two cases have ratio exactly 1.0). With random dimensions between 2 and 100 a bad order costs a lot even for 4 to 8 matrices.
  G3.8 (tier L: 16.9, predicted 6, range 2 to 25) was a hit with a 64 % error; the means for M and X are 15.8 and 14.9, so the ratio hardly depends on the number of matrices beyond about 40.
- I had seen 12 of these cases in the quick smoke run (a tier S ratio of 5.7 in the second case) before the full run, which could have told me that G3.7 was too low; I did not change the predictions (see the note at the top).


---

## Module G, round 4: small inputs, DP and memoised recursion against brute force

**Date and time:** 2026-11-20 13:20 UTC+5 (before running round 4)

**Experiments:** `G-small-chain`: n = 4, 6, 8, 10, 12 matrices (dimensions concatenated from tier S cases), algorithms `dp`, `memo`, `brute` (all bracketings: Catalan numbers 5, 42, 429, 4 862, 58 786).
`G-small-drum`: L = 8, 11, 14, 17, 20 (the first L prices of the first sampled tier M case), algorithms `dp`, `memo`, `greedy`, `brute` (all cuts: 2^(L - 1)).

**Which algorithm I expect to win:** `dp` (and `greedy` for the drum) from the smallest size on; brute force grows by a constant factor per extra element (about 3.2 per matrix, 2 per unit of length) and is thousands of times slower at the largest size.

| id | prediction | tolerance |
|---|---|---|
| G4.1 | chain brute force: bracketings enumerated at n = 12 | 58 786 exactly |
| G4.2 | chain brute force: growth factor per extra matrix of the enumerated count (semi-log fit) | 3.2 (3.1 to 3.35) |
| G4.3 | chain brute force: time at n = 12 is 0.6 s | 0.25 to 2.0 s |
| G4.4 | the smallest n (of 4, 6, 8, 10, 12) at which the chain DP is faster than brute force is 4 | 4 to 6 |
| G4.5 | chain: brute time / dp time at n = 12 is 4000 | 1000 to 20 000 |
| G4.6 | chain: memo time / dp time, mean over the five sizes, is 2.0 | 1.3 to 4 |
| G4.7 | chain: dp, memo and brute return the same cost at all five sizes (share) | exactly 1.0 |
| G4.8 | drum brute force: cuts enumerated at L = 20 | 524 288 exactly |
| G4.9 | drum brute force: growth factor per extra unit of length of the time (semi-log fit) | 2.0 (1.85 to 2.15) |
| G4.10 | drum brute force: time at L = 20 is 0.9 s | 0.4 to 2.0 s |
| G4.11 | the smallest L (of 8, 11, 14, 17, 20) at which the drum DP is faster than brute force is 8 | 8 to 11 |
| G4.12 | drum: brute time / dp time at L = 20 is 12 000 | 3000 to 50 000 |
| G4.13 | drum: memo time / dp time, mean over the five sizes, is 1.6 | 1.1 to 3 |
| G4.14 | drum: dp, memo and brute return the same price at all five sizes (share) | exactly 1.0 |
| G4.15 | drum: dp time / greedy time, mean over the five sizes, is 1.0 | 0.6 to 1.6 |

**Reasoning.**
- Brute force counts exactly the Catalan number C(n - 1) of bracketings (G4.1) and 2^(L - 1) cuts (G4.8). The Catalan numbers grow by 3.23 per extra matrix between n = 4 and 12 (58 786 / 5 over 8 steps) (G4.2); the time has a small fixed part and a per-bracketing cost of about 10 microseconds
  (generators, string concatenation), so 58 786 bracketings take about 0.6 s (G4.3). The DP at n = 12 has 66 cells and 286 candidates (about 0.15 ms with validation and the tables): ratio about 4000 (G4.5). Already at n = 4 (5 bracketings) the DP is not slower (G4.4).
- The recursion for 12 matrices makes about 570 calls against 286 candidates: 2 times the DP including the shared overhead (G4.6); for the drum one call per candidate: 1.6 (G4.13).
- Drum brute force: one recursion node per partial cut, about 1.2 microseconds per leaf: 2^19 leaves are 0.6 to 1 s (G4.10), the time doubles per unit (G4.9). The DP at L = 20: 210 candidates, about 40 to 70 microseconds with the validation: ratio about 12 000 (G4.12).
  At L = 8 brute force has 128 cuts (about 0.15 ms) against about 20 microseconds of the DP (G4.11). dp and greedy both have a linear validation and an O(L log L) or O(L^2) part that are about equal at L <= 20 (G4.15).
- All exact methods apply the same tie rule, so they must give the same answer (G4.7, G4.14).

**After the run** (written 2026-11-20 after round 4): 15 of 15 inside the tolerance.
- **Exact counts:** brute force enumerated 58 786 bracketings at n = 12 (G4.1) and 524 288 cuts at L = 20 (G4.8), and its count grows by 3.237 per extra matrix (3.2 predicted; interval 3.03 to 3.46) and exactly 2.000 per unit of length. dp, memo and brute returned the same bracketing in 5 of 5 chains and the same price and cut in 5 of 5 drums (G4.7, G4.14).
- **Brute force times (G4.3, G4.10):** 0.91 s for 58 786 bracketings (15.5 microseconds each, 0.6 s predicted, a hit with 34 % error) and 0.92 s for 524 288 cuts (0.9 predicted). The time of the chain brute force grows by 3.34 per matrix (interval 2.84 to 3.94), the drum brute force by 2.04 per unit.
- **Crossovers:** the DP is faster than brute force from the smallest size on, in both problems (n = 4 and L = 8; G4.4 and G4.11), but at the smallest sizes the IQR is of the size of the median (chain n = 4: dp 27.6 us, IQR 21.9 us), so the ratios there (2.3 at n = 4) are not reliable. At the largest sizes brute / dp is 3 897 (chain, n = 12) and 13 402 (drum, L = 20).
- **memo / dp:** 1.6 on average in the chain at small n (2.0 predicted) and 2.4 in the drum (1.6 predicted): the recursion costs more than I thought for the drum, where each candidate is one call of a function with a loop. **G4.15:** the DP is faster than greedy at small L (ratio 0.66; I predicted 1.0): the sort of tuples in greedy costs more than the DP's 100 to 230 candidates (see round 2).

---

## Module G, summary after all rounds (2026-11-20)

48 numerical predictions, 46 inside the tolerance, **2 misses: G3.3 and G3.7**, both in the quality round.
- Predictions about counts and exponents were exact or close (G1.3, G1.4, G2.4, G2.5, G4.1, G4.8; slopes within 0.15 of the prediction), and all comparisons between exact methods agreed.
- **The high number of hits is not a strong result.** The absolute times were calibrated on durations I had seen before writing (note at the top), and several tolerances were wide: G2.8, G2.10, G2.12 and G4.15 are hits at 49 to 118 % error.
- The real modelling errors: the quality of the greedy cut (it is optimal in 61 of 62 cases, I expected about 85 %) and the cost of multiplying from left to right (4.5 times the optimum in tier S, I expected 1.35 times).
- **Where the measurements were made.** On the author's laptop (Intel64 Family 6 Model 142, 8 logical CPUs, Windows 10, Python 3.14.6, one thread; see `results/environmentG.json`). I could not verify that it was on the charger and in best-performance mode; some points are noisy (IQR up to 30 % of the median at n = 320 and a large outlier at n = 40 of the memoised recursion), so the group should repeat the runs under those conditions and note any difference under the entries above.


---

## Module G, what each round can show and what it cannot

- Round 1 shows the shape of the growth on chains made of the dimensions of the data. The dimensions are random (2 to 100), so the optimal bracketing is not shaped by any structure; a chain with a structure (many 1s, a few huge dimensions) could change the quality numbers but not the counts of the DP.
- Round 2 uses prefixes of one real price table (case 12-47). The price table is concave with noise, which is what makes the greedy cut look good in round 3; a price table with bonuses for long pieces would not.
- Round 3 is a sample of 62 cases of one dataset, not a guarantee. The chain ratios (G3.7, G3.8) compare the optimum with one naive order, not with all heuristics.
- Round 4 uses at most 12 matrices and a drum of length 20, so the numbers about brute force say little about the sizes of the data. There is no DNF round for module G: the 300 s rule is implemented in the harness (a deadline in the algorithms) and tested, but no size of the data reaches it with the DP (n = 300: about 1 s).


## Module B and Module F — Hamza, round 1

Date: 2026-11-26 (client date), recorded before the first full B/F experiment.
No B/F timing calibration was run before these predictions. This is a new local
round, not a repeat or replacement of Ayna's or Adan's measurements.

Plan: `python experiments/runBF.py --master MASTER`. One discarded warmup,
five repetitions, median/IQR, single thread, input loading excluded, separate
peak-memory run. At least five nested connected BFS prefixes of ONE sampled L
network (16 to 1024 vertices when available); never pool networks. Quality:
seed 41, every seventh tier case, 20 S/20 M/10 L/12 X, all three targets before
and after each cumulative closure wave. Growth evidence is specific to this
network and its changing edge density, not a controlled universal exponent.

| id | prediction | tolerance |
|---|---|---|
| BF1 | Dijkstra and Bellman-Ford shortest costs agree on every quality row | 100% |
| BF2 | Kruskal and Prim forest costs agree after every wave | 100% |
| BF3 | BFS travel cost is never below optimal travel cost | ratio >= 1 |
| BF4 | At least one sampled route shows a cost loss from BFS | max ratio > 1 |
| BF5 | Dijkstra counted-operation log-log slope in V is near sparse n log n | 0.7 to 1.8 |
| BF6 | Kruskal counted-operation slope is near sparse E log E | 0.7 to 1.8 |
| BF7 | Dijkstra is faster than Bellman-Ford on the largest prefix | ratio Bellman/Dijkstra > 1 |
| BF8 | All growth runs finish within 300 seconds | no DNF |

No prediction of an absolute runtime: CPU power state is unknown. Bellman-Ford
can stop early on this network, so BF7 may fail despite the worst-case theory.

After the run: all eight stated tolerances were met. See
`results/predictions-vs-measurements-BF.md`. Dijkstra/Bellman agree on 867
route checks, and Kruskal/Prim on 289 forest checks across 62 sampled cases.
Worst BFS/optimal cost ratio: 20; operation exponents: 1.099 (Dijkstra),
1.187 (Kruskal); largest Bellman/Dijkstra time ratio: 1.418.
An initial timing trial overlapped fault-injection work and was discarded;
the published growth measurements were rerun after that work finished. No
other project benchmark was running during the published timings. CPU power
state and unrelated background load could not be verified. The quality pass
was also rerun. No pre-run prediction was changed.

## Hamza: official campaign and B/F round 2

Recorded 2026-11-26 08:48:06 UTC (before the full runs in this round).
The original Project Statement is now available. Section 7.4 fixes the
calendar, so the former example no longer represents the required campaign.
The official run uses five seed-41 sample cases (S, M, L, trap 47 and trap 48),
seven days each, optimized methods, algorithm baselines and simple policies.

Predictions for `python experiments/run_campaign.py --master MASTER`:

| ID | Point prediction | Tolerance and reasoning |
|---|---|---|
| CAM1 | All 105 daily policy records pass the output invariants | 100%; daily changes are checked against input contracts |
| CAM2 | Exact B/C/D/F/G baselines agree in every applicable comparison | 100%; same problem and identical daily input |
| CAM3 | Day-1 greedy load value on trap 47 is at most 60% of DP | 0 to 0.60; hostile data construction |
| CAM4 | Day-1 BFS cost on trap 48 exceeds cheapest cost | ratio > 1; hop-count trap |

B/F round 2 repeats the same seven input sizes after adjacency sorting is
reported separately as pre_comparisons/pre_moves. It retains the 300-second
deadline and warmup/five-run protocol. Core operations exclude pre_*; timing
and memory include preprocessing. No new absolute-time claim is made.

For every method/metric fit, tolerance is +/- 0.35 in the exponent:
- Memory exponent: 1.0 for every method.
- BFS time and core-operation exponents: 1.0.
- Dijkstra and early-stopping Bellman-Ford time/core exponents: 1.1.
- Kruskal and Prim time/core exponents: 1.2.

These point predictions are informed by the earlier published round and its
input family, not blind predictions or worst-case Bellman-Ford claims.
The fits will report prediction/measurement relative error as required by
section 7.3. Master-data quality comparisons will be rerun unchanged.

After this round: pending.
