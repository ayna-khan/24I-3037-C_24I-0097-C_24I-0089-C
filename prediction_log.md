# Prediction log

Rules followed in this log (Section 7.3 of the project statement): every round has an entry
that is written and **committed before the round is run**. After the run, the section "After the run"
of the entry records what was wrong and why. The numbers below are checked automatically by
`python experiments/predictionsAD.py` (same ids), which writes `results/predictions-vs-measurements-AD.md`.

Entries in this file: Ayna Khan (24I-0097-C), modules A and D. Adan and Hamza add their own entries for
C, G and B, F below, in the same format, each committed from their own account.

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