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
The first complete run of all rounds was then made in that session on a cloud machine, and the "After the run" notes describe that run.
The group repeats the rounds on its own machine: the prediction entries are committed first, the rerun and the new results afterwards,
and any "After the run" statement that no longer matches the new numbers is corrected in a later commit instead of being rewritten silently.

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

**After the run** (written 2026-11-16 after round 1; full table in `results/predictions-vs-measurements-AD.md`):
13 of 13 predictions were inside their tolerance, but several hits are for a different reason than the one I gave, and some tolerances were too wide to say much.
- **1.1 (slope 2.0, measured 2.14 +- 0.13).** My reasoning assumed W is proportional to n with 3.4 kg per crate. That was only true
  for the first two sizes: the pooled capacity per crate was 3.4 (n = 200, 400), 2.9 (800), 4.2 (1600, 3200) and 3.9 (6400),
  because the consecutive tier L cases that are joined have different capacities per crate. So W grew slightly faster than n and the
  slope is above 2. The better evidence is the cell count: time against cells has slope 1.03 +- 0.06, so the counted operations explain the time.
- **1.3 and 1.4 (time 14 s predicted, 19.0 s measured; ratio 450 predicted, 761 measured).** Two causes: the DP did 1.61 x 10^8 cells instead of my 1.4 x 10^8 (see above), and one cell
  costs 118 ns at the large sizes, not 100 ns (92 to 135 ns over the sizes). Constants like this are machine-dependent; the shapes are not.
- **1.7 (greedy memory 80 bytes per crate predicted, 102 measured).** I counted too few lists of n references (filter, two merge buffers,
  chosen, ids). I did not profile it further, so this explanation is a guess.
- **1.9 (greedy slope in W: 0.0 predicted, 0.12 measured).** A hit only because the tolerance was +-0.15. The fit has R^2 = 0.49 and a 95 % interval of +-0.18 that includes 0:
  the greedy times are 5 to 9 ms with noise of the same size as the trend, so this measurement says "no clear dependence on W", not more. The operation count of the greedy rule is exactly constant in W.
- **1.10 (greedy not optimal in 55 % of tier S, measured 65 %)** and **1.12 (0.55 predicted, 0.56 measured for trap 47)** are close.
  A surprise: in the tier S sample a few cases of other groups give greedy / DP of only 0.58, nearly as bad as the trap cases (see Figure A4).
- **1.13:** the DP equals the exhaustive-search claim in 20 of 20 tier S cases, so no sign of a bug or a defective case.
- The tolerance for 1.4 (200 to 1500) and 1.11 were wide; a hit there does not show that I understand the constant.


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

**After the run** (written 2026-11-16 after round 2): 4 of 4 inside the tolerance.
- 2.1: base 1.99 per crate (interval 1.91 to 2.08) and exactly 2^n subsets counted; 2.2: 0.165 s against 0.17 s predicted; 2.3: mean DP / greedy 4.6 against 4.
- 2.4 is the least informative prediction: I had seen from the smoke run that n = 8 is already a tie. At n = 8 brute force needed 47 us and the DP 37 us (ratio 1.26), so the crossover is at or below n = 8 and I did not test smaller sizes.
- At n = 20 the DP is 668 times faster than brute force; at n = 17 the IQR of brute force is large (15 ms around 28 ms), possibly because something else was running on the machine at that moment; I kept the data and did not repeat the run.


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

**After the run** (written 2026-11-16 after round 3): 10 of 11 inside the tolerance, **one miss: 3.8**.
- **3.8 (miss).** I predicted that operations divided by (m log2 m) stay constant. They do not: the value grows from 2.47 at m = 250 to 3.17 at m = 64000 (ratio 1.28, limit 1.25).
  Cause: my model forgot that the backlog starts at zero and then grows. A pop costs about log2 of the current backlog, so the average over the run is about log2(0.33 m) - 1.4 = log2 m - 3.0, not log2 m.
  The ratio (log2 m - 3.0) / log2 m is 0.62 at m = 250 and 0.81 at m = 64000, which predicts growth by a factor 1.31; measured 1.28. So the heap is m log m, but with a negative constant term.
- 3.1 and 3.2: heap slope 1.18 +- 0.03, scan slope 1.98 +- 0.06 over 9 sizes (R^2 above 0.998). The heap slope is above 1 as predicted.
- 3.3, 3.7: key comparisons of the scan at m = 8000 are 10.7 million (10.9 predicted) and the backlog is 0.331 m (0.33 predicted). These were the best predictions because they follow from counting, not from timing.
- 3.4 and 3.5 (absolute times): the scan at m = 64000 took 34.9 s (51 predicted): one comparison cost 51 ns, not 70 ns. The heap took 0.40 s (0.5 predicted).
  The scan against heap time ratio went 1.2 (m = 250), 15 (8000), 88 (64000). Time per alarm of the heap grew from 2.2 to 6.2 microseconds; operations per alarm only grew by 2.6, so part of this might be cache misses in the larger heap. I did not test that.
- 3.9 (memory): 185 bytes per alarm against 250 predicted; the heap and the scan need almost the same memory (they differ by under 0.1 %), because the answer and the arrival dictionary dominate.
- 3.10: the mean wait of all alarms is identical under both orders in all 62 sampled cases, as the conservation argument says.
- 3.11: ratio of 429 (predicted 80, tolerance 20 to 1000): a hit with a 81 % error. On tier L the priority 9 and 10 alarms wait 1.5 ticks on average under the urgency order and 639 under first-come-first-served; my estimate of the FIFO wait ("the whole backlog") was right in shape but I underestimated how short the urgent wait is.


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

**After the run** (written 2026-11-16 after round 4): 3 of 3 inside the tolerance.
- 4.1: the scan at m = 256000 passed 300 s and is recorded as DNF; the heap finished in 1.67 s (2.5 s predicted).
- Largest size that finished for the scan: m = 64000 (34.9 s). Missing point predicted from the fit on m <= 64000: 506 s (670 s predicted before the run), i.e. the scan would need about 8 to 9 minutes, which is still above the 300 s limit. The prediction error comes from the same lower cost per comparison as in 3.4.
- The 506 s is an extrapolation of a log-log fit, not a measurement: the run was stopped at 300 s.


---

## Summary after all rounds (2026-11-16)

31 numerical predictions, 30 inside the tolerance, 1 miss (3.8). The hits are not all equally meaningful:
predictions about counts and exponents (1.5, 1.8, 3.2, 3.3, 3.7) were close; predictions about absolute times (1.3, 3.4, 3.5, 4.2, 4.3)
were within 26 to 50 % and depend on the machine; and some tolerances (1.4, 1.11, 3.11) were wide enough to hit without much understanding.
The one real modelling error was 3.8: ignoring that the backlog grows from zero.

**Where the measurements were made.** These numbers were produced by the experiment scripts on a cloud virtual machine
(2 logical CPUs, Intel Xeon at 2.1 GHz, Python 3.13, Linux, one thread, see `results/environment.json`), not on a laptop.
Absolute times will differ on another machine; exponents, operation counts and quality numbers should not.
