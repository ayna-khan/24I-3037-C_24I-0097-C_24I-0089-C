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

*A problem with the measurement itself, stated first.* The speed of the machine changed while round 1 was running. Time per DP cell: 200 ns (n = 200), 181, 145, 139 (n = 1600), then 253 (n = 3200, where the IQR is 8.8 s, 80 % of the median, so the speed changed during the 5 timed runs) and 398 ns (n = 6400);
in the W sweep, which ran afterwards on the same 1600 crates, 317 to 350 ns per cell. The greedy rule on the same 1600 crates took 7.6 ms in `A-scale-n` and 17 to 24 ms in `A-scale-W`. The operation counts are exact and did not change, so they are the reliable part of this round.
I did not establish the cause. Possible causes: laptop power or heat management, other programs running, or Windows moving the run between fast and slow cores of this hybrid Intel CPU. A repeat with the charger connected and the power mode on best performance would tell.
- **1.1 (miss, slope 2.26 +- 0.36, limit 2.25).** The interval contains my 2.0, so this is a borderline miss. Two causes: W per crate is not constant (3.4, 3.4, 2.9, 4.2, 4.2, 3.9 kg per crate for the six sizes, because the joined tier L cases differ), so the counted cells have slope 2.08 +- 0.12, not 2.0;
  and the drift above added to the time of the large sizes. Time against cells has slope 1.09 +- 0.16, so the counted operations still explain the time.
- **1.2 (miss, greedy slope 1.44, range 0.9 to 1.3).** The greedy operations have slope 1.150 +- 0.016, as predicted. The times at n = 3200 (45 ms) and n = 6400 (93 ms) are 6 and 12 times the time at n = 1600 while the operations are 2.2 and 4.8 times larger: the same drift.
- **1.3 (miss, 64.2 s against 14 s).** I took 100 ns per cell from a smoke run on a cloud machine, where the full round later gave 19.0 s. Here a cell cost 398 ns at n = 6400 (139 ns at n = 1600), and the cell count was 161 million, not my 140 million.
  The lesson: a time constant measured on one machine does not carry over to another; the cell count (a prediction I made about counts) was close.
- **1.4 (hit, 689 against 450).** A hit with a wide tolerance; I would not read much into it.
- **1.5, 1.6, 1.7, 1.8, 1.9** hit. 1.8: DP slope in W is 0.995 +- 0.037, clean because the W sweep ran at an almost constant speed. 1.7: greedy memory is 102 bytes per crate against 80 predicted (I counted too few lists of n references; not profiled further).
  1.9 is a hit only because of the tolerance: the greedy time has slope 0.08 with R^2 = 0.57 (the operation count is exactly constant), which says "no clear dependence on W" and nothing more.
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

**After the run** (Ayna's laptop): 3 of 4 inside the tolerance, miss 2.2.
- **2.2 (miss).** Brute force at n = 20 took 0.585 s against 0.17 s predicted; the first run on the cloud machine gave 0.165 s. The factor 3.6 is a machine and speed-state difference, not an error in the 2^n argument: 2.1 hit (base 2.02, interval 1.94 to 2.11) and exactly 2^n subsets were counted at every size.
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

**After the run** (Ayna's laptop): 9 of 11 inside the tolerance, misses 3.5 and 3.8.
- **3.8 (miss, 1.28 against a limit of 1.25).** Operation counts do not depend on the machine, so this is a real modelling error. I predicted that operations divided by (m log2 m) stay constant. They grow from 2.47 at m = 250 to 3.17 at m = 64000.
  My model forgot that the backlog starts at zero and then grows. A pop costs about log2 of the current backlog, so the average over the run is about log2(0.33 m) - 1.4 = log2 m - 3.0 rather than log2 m. The ratio (log2 m - 3.0) / log2 m is 0.62 at m = 250 and 0.81 at m = 64000, a growth by a factor of 1.31; measured 1.28. So the heap is m log m with a negative constant term.
- **3.5 (miss, heap at m = 64000 took 1.04 s against 0.5 s).** The first run on the cloud machine gave 0.40 s. On the laptop the heap time jumps from 0.108 s (m = 16000) to 0.481 s (m = 32000), 4.5 times for twice the size while the operations grow 2.1 times: the speed change again. As a result the scan/heap time ratio is 1.5, 1.6, 3.0, 4.8, 9.5, 17, 63, 57, 50 for the nine sizes and is not monotone at the top; do not read the 63 as a trend.
- **3.1 (hit but inflated).** The heap slope is 1.26 +- 0.11 (limit 1.3); the operations have slope 1.164 +- 0.028, which is the m log m shape I expected. **3.2:** scan slope 2.03 +- 0.16, comparisons 1.99. **3.3:** 10.7 million comparisons at m = 8000 (10.9 predicted).
- **3.4 (hit, 51.9 s against 51).** A lucky hit: my 70 ns per comparison came from the smoke run, here a comparison cost 76 ns, and the first cloud run gave 51 ns. The IQR of the scan at m = 32000 is 12.4 s (45 % of the median).
- 3.6 hit (1.5), 3.7 hit (backlog 0.331 m), 3.9 hit (185 bytes per alarm; heap and scan memory differ by under 0.1 %), 3.10 hit (the mean wait of all alarms is identical under both orders in all 62 cases), 3.11 hit with a 81 % error (ratio 429 against 80 predicted; on tier L the priority 9 and 10 alarms wait 1.5 ticks under the urgency order and 639 under first-come-first-served).

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

**After the run** (Ayna's laptop): 2 of 3 inside the tolerance, miss 4.2.
- 4.1 hit: the scan at m = 256000 passed 300 s and is recorded as DNF. 4.3 hit: the heap took 2.40 s (2.5 predicted).
- **4.2 (miss, extrapolated 1189 s against 670 s).** The extrapolation uses the fitted line through nine sizes including the disturbed ones; plain quadratic growth from the last measured size (51.9 s at m = 64000, times 16) gives about 830 s. Both are far above 300 s, so the DNF conclusion does not depend on it.
  The largest size that finished for the scan is m = 64000. The extrapolated figure is an estimate, not a measurement.

---

## Summary after all rounds

31 numerical predictions on the laptop run: 24 inside the tolerance, 7 misses (1.1, 1.2, 1.3, 2.2, 3.5, 3.8, 4.2).
- **Real modelling errors:** 3.8 (I forgot that the backlog starts at zero, so the heap work per alarm is log2 m - 3, not log2 m) and, in part, 1.1 (the capacity per crate of the pools is not constant, so the cell count grows with slope 2.08, not 2.0).
- **Caused by speed and constants of the machine:** 1.2, 1.3, 2.2, 3.5 and 4.2. The speed of the laptop changed during round 1 and again in round 3 (time per DP cell 139 ns to 398 ns, heap time jumping 4.5 times for a doubling), and the time constants I used (100 ns per cell, 4 microseconds per alarm) came from a cloud machine. Predictions of counts, memory and quality
  (1.5, 1.6, 1.8, 2.1, 3.3, 3.7, 3.10, 1.10 to 1.13) were close or exact on both machines.
- **Weak hits:** some tolerances (1.4, 1.9, 3.4, 3.11) were wide enough to hit without much understanding; 3.4 is luck.
- **What I would do differently:** predict ratios and operation counts, and calibrate any absolute time on the same machine and in the same power mode before predicting it; run timing rounds with the laptop connected to power.