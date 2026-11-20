# Prediction log, module G (chains and cuts), Adan (24I-3037-C)

Same rules as `prediction_log.md` (Section 7.3 of the project statement): every round has an entry that is written
**before the round is run**; the section "After the run" is added afterwards and says what was wrong and why. This file
is to be merged into `prediction_log.md` later (the ids carry the prefix G so they do not clash with the ids of the other modules).
The numbers are checked automatically by `python experiments/predictionsG.py` (same ids), which writes
`results/predictions-vs-measurements-G.md`.

Master dataset: master_release_v1 (folder `MASTER`). Group seed 41 (sample positions 41 mod 7 = 6, 13, 20, ...). Time unit: seconds on one core,
median of 5 runs after one discarded warm-up run. How the larger instances are built (`experiments/sampleG.py`):
chains: the dimension lists of consecutive tier L cases are concatenated and cut after n + 1 dimensions (any list of whole numbers >= 1 is a chain);
drums: the first L prices of the price table of case 12-47 (the first case of the seed-41 samples of tier L and X with 2000 prices); tables of different cases are never joined.

**Order of events.** The four entries below were written together on 2026-11-20 at 13:20 (UTC+5, laptop clock), after `src/modules/chains.py`, its tests
(63 tests) and the fault-injection file were written and before `runG.py`, `analyzeG.py` and `predictionsG.py` existed. No experiment of module G had been run.
The entries are not committed by me (I was not asked to commit): **commit this file before the first run.**

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

## Round 1: growth in n of the chain DP and the memoised recursion (n^3)

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

## Round 2: growth in L of the drum DP, the memoised recursion and the greedy cut (L^2)

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

## Round 3: quality of the greedy cut against the DP, and of the best bracketing against multiplying left to right

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

## Round 4: small inputs, DP and memoised recursion against brute force

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

## Summary after all rounds (2026-11-20)

48 numerical predictions, 46 inside the tolerance, **2 misses: G3.3 and G3.7**, both in the quality round.
- Predictions about counts and exponents were exact or close (G1.3, G1.4, G2.4, G2.5, G4.1, G4.8; slopes within 0.15 of the prediction), and all comparisons between exact methods agreed.
- **The high number of hits is not a strong result.** The absolute times were calibrated on durations I had seen before writing (note at the top), and several tolerances were wide: G2.8, G2.10, G2.12 and G4.15 are hits at 49 to 118 % error.
- The real modelling errors: the quality of the greedy cut (it is optimal in 61 of 62 cases, I expected about 85 %) and the cost of multiplying from left to right (4.5 times the optimum in tier S, I expected 1.35 times).
- **Where the measurements were made.** On the author's laptop (Intel64 Family 6 Model 142, 8 logical CPUs, Windows 10, Python 3.14.6, one thread; see `results/environmentG.json`). I could not verify that it was on the charger and in best-performance mode; some points are noisy (IQR up to 30 % of the median at n = 320 and a large outlier at n = 40 of the memoised recursion), so the group should repeat the runs under those conditions and note any difference under the entries above.


---

## What each round can show and what it cannot

- Round 1 shows the shape of the growth on chains made of the dimensions of the data. The dimensions are random (2 to 100), so the optimal bracketing is not shaped by any structure; a chain with a structure (many 1s, a few huge dimensions) could change the quality numbers but not the counts of the DP.
- Round 2 uses prefixes of one real price table (case 12-47). The price table is concave with noise, which is what makes the greedy cut look good in round 3; a price table with bonuses for long pieces would not.
- Round 3 is a sample of 62 cases of one dataset, not a guarantee. The chain ratios (G3.7, G3.8) compare the optimum with one naive order, not with all heuristics.
- Round 4 uses at most 12 matrices and a drum of length 20, so the numbers about brute force say little about the sizes of the data. There is no DNF round for module G: the 300 s rule is implemented in the harness (a deadline in the algorithms) and tested, but no size of the data reaches it with the DP (n = 300: about 1 s).
