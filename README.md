# LIFELINE - Algorithmic Relief-Command Engine (DAA project, group 41)

Group 41: Ayna Khan (24I-0097-C), Dur E Adan (24I-3037-C), Hamza Sardar (24I-0089-C).
Repository: see `repository.txt`.

**Status of this README.** The sections for modules A (relief inventory), D (emergency queue), C (rescue scheduling) and G (chains and cuts) are complete.
Modules B/F, the loader, campaign, CLI and local backend have now been added by Hamza. The campaign now implements the official calendar from Project Statement section 7.4 (page 7); five master cases and their baselines have been verified. The failure-mode list of section 9 is still the draft of Ayna.

## 1. Setup and dependencies

- Python 3.10 or newer (developed with 3.13; modules C and G with 3.14). The decision modules, the tests and the experiments use the standard library only.
- `matplotlib` (plots only): `pip install matplotlib`.
- Library use that the statement asks us to document: `csv` (reading the master dataset), `tracemalloc` (memory measurement),
  `matplotlib` (plots), `unittest` (tests). The test references use the built-in `sorted` to check module D; the shipped algorithms
  never call a library sort: the sorting that modules A, C and D need is our own merge sort (`src/sorting.py`). The references of C and G use `sorted`, `itertools.combinations`,
  `functools.lru_cache` and `fractions.Fraction`; the shipped code of G uses `threading` and `sys.setrecursionlimit` only to run its memoised recursion safely (section 5).
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
| Only modules C and G | `python -m unittest tests.testrescue tests.testchains` |
| Fault-injection tests of C (about 1 minute) and G (about 8 minutes) | `python -m tests.testfaultinjectionC`, `python -m tests.testfaultinjectionG` (write `results/fault-injection-C.txt` and `-G.txt`) |
| Experiments of C and G, one round | `python experiments/runC.py --master MASTER --round 1` (rounds 1 to 4; round 4 is the 5 minute DNF run), `python experiments/runG.py --master MASTER --round 1` (rounds 1 to 4; `--round all` takes about 12 minutes) |
| Fits, comparison tables and plots of C and G | `python experiments/analyzeC.py`, `python experiments/analyzeG.py` |
| Predictions against measurements of C and G | `python experiments/predictionsC.py`, `python experiments/predictionsG.py` |
| Sample outputs of C and G; rebuild the test fixtures | `python experiments/sampleC.py --master MASTER` (add `--fixture` to rebuild the fixture), `python experiments/sampleG.py --master MASTER` |
| Official seven-day campaign (readable output) | `python -m src.cli --master MASTER campaign --case 41-00 --compare` |
| Reproduce five official campaigns, comparisons and report figures | `python experiments/run_campaign.py --master MASTER` |
| Save the complete daily JSON | `python -m src.cli --master MASTER --output results/sample-outputs/campaign-official.json campaign --case 41-00 --compare` |
| B/F and campaign tests | `python -m unittest tests.testhamza tests.testofficialcampaign tests.testbackend` |
| B/F experiments, fits and plots | `python experiments/runBF.py --master MASTER`, then `python experiments/analyzeBF.py` |
| B/F and integration fault injection | `python experiments/faultBF.py` |
| Verify master SHA-256 manifest | `python -m src.cli --master MASTER verify` |
| Local frontend API | `python -m src.server --master MASTER --port 8000` |
| Newspaper interface, The Lifeline Gazette | `python -m frontend --master MASTER --open` |

The experiments use no random numbers: samples and pools are fixed by the group seed 41 (see section 4), so a rerun gives the same
inputs and the same operation counts. Times vary from machine to machine.

## 3. Repository layout

```
README.md  prediction_log.md  repository.txt  members.txt
src/        models.py (data types, errors)   measure.py (timing, memory, fits)   sorting.py (our merge sort)
            modules/inventory.py (A)   modules/emergencyqueue.py (D)   modules/rescue.py (C)   modules/chains.py (G)
            network.py  loader.py  validation.py  campaign.py  cli.py  backend.py  server.py
            modules/routes.py (B)  modules/networkplan.py (F)
frontend/   server.py (pages and API on one origin)   static/ (index.html, style.css, draw.js, app.js)
calendars/  official.json (section 7.4, default)  example.json (historical custom example)
tests/      testinventory.py  testqueue.py  testmeasure.py  testfaultinjection.py   testrescue.py  testfaultinjectionC.py   testchains.py  testfaultinjectionG.py
            reference/ (independent reference methods, never imported by src)   fixtures/ (small samples of the master data)
experiments/ runAD.py  analyzeAD.py  predictionsAD.py  sampleAD.py  mastersample.py   runC.py  analyzeC.py  predictionsC.py  sampleC.py   runG.py  analyzeG.py  predictionsG.py  sampleG.py
results/    results.csv  plots/  quality-A.csv  quality-D.csv  quality-C.csv  quality-G.csv  fits-AD.md  fits-C.md  fits-G.md  comparison-AD.md  comparison-C.md  comparison-G.md
            fault-injection-*.txt  predictions-vs-measurements-*.md  environment*.json  samples in sample-outputs/
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
- **Pools of module C (windows).** Consecutive tier cases are joined; the windows of the i-th case are shifted by `1440 * i` minutes (a case lives inside one day), so joined cases never overlap in time; ids are renumbered from 1 and the pool is cut after n windows.
  The pools therefore keep the overlap structure of one case (about 1.2 window starts per minute); they never put 3000 windows inside one day.
- **Pools of module G.** *Chains:* any list of whole numbers >= 1 is a chain, so the dimension lists of consecutive tier cases are concatenated and cut after n + 1 dimensions (the data has n <= 300 per case; the growth experiment goes to n = 640).
  *Drums:* a drum of length L only uses the prices of the lengths 1 to L, so an instance of size L is the first L prices of a real price table (case 12-47, the first case of the seed-41 samples of tier L and X with 2000 prices); tables of different cases are never joined.
- **Interpretation notes for C and G.** No trap case (46 to 49) is specific to windows, chains or drums; the tier X cases are used only as large inputs. Tier S claims exist for windows (`window_count_opt`, `window_value_opt`) and drums (`drum_opt`) but not for chains,
  so the chain optimum of tier S is checked against brute force and an independent reference.

## 5. Problem definitions and algorithms

Notation: n crates, W truck capacity (kg), m alarms; n windows (C); n matrices and drum length L (G). Ties are always broken by id ascending, except in module G, where the tie rules are stated in its section.

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

### Module C - rescue scheduling (Adan)

- **Input:** windows (id, start minute >= 0, finish minute > start, value >= 0), all whole numbers. Two windows are compatible when one starts at or after the finish of the other (touching windows are compatible).
  On day d the window with `(window_id + d) % 5 == 0` is unavailable. **Output:** a set of pairwise compatible windows with the maximum number of windows (objective `count`) or the maximum total value (objective `value`).
  No windows, or none left after the day filter, gives status `EMPTY`; a broken window, objective or method gives status `INVALID` with a note (never an exception, never a made-up plan); only a passed time budget raises `TimeBudgetExceeded`.
- **Shipped algorithms:** for the count, the **earliest-finish greedy** rule, `O(n log n)` (sort by finish, ties by window id, take each window that starts at or after the finish of the last one taken; optimal by the exchange argument).
  For the value, **weighted-interval dynamic programming with binary search**, `O(n log n)`: `best[i] = max(best[i-1], best[p(i)] + value(i))`, where p(i), the number of earlier windows that finish at or before the start of window i, is found by binary search; a window is taken only when strictly better.
- **Baselines:** the plain `O(n^2)` DP (every earlier window is examined), and brute force over all subsets in Gray-code order with conflict masks (`O(2^n)`, refused above 22 windows, status `INVALID`). The earliest-finish rule on the value objective is kept as a baseline: it ignores values and is not optimal (its note says so).
  Windows of value 0 are ignored for the value objective.
- **Tie rule:** windows with the same finish are ordered by id ascending. The total is unique; the chosen set is deterministic for greedy and dp whatever the input order; dpquad and brute guarantee only the same total.
- **Campaign interface:** `rescue.available_on_day(windows, day)` returns the windows that can be staffed that day (it raises `InvalidInputError` for a bad day or id, because it returns a list); `rescue.solve(windows, objective, method)` with objective `count` or `value` and method `greedy`, `dp`, `dpquad` or `brute`
  (default: greedy for the count, dp for the value) returns `RescuePlan(status, chosen, total, ops, note)` with the window ids in ascending order.
- **Retained or changed since the proposal:** retained (earliest-finish greedy for the count, DP with binary search for the value, plain DP and brute force as baselines). Added: the greedy rule on the value objective as a measured baseline, and the status values.

### Module G - chains and cuts (Adan)

- **Input and output.** *Chain:* dimensions p0 ... pn (whole numbers >= 1, n >= 1 matrices); a product of a p x q and a q x r matrix costs `p*q*r`; the output is the bracketing with the fewest scalar multiplications as a string such as `((A1 A2) A3)` (one matrix: `A1`) and its cost.
  *Drum:* prices for the lengths 1 to L (whole numbers >= 0; `prices[0]` is the price of length 1, a mapping `{length: price}` is accepted too, prices beyond L are not looked at); the output is a cut into whole pieces with the maximum total price, as the list of piece lengths in cutting order, and the price.
  Broken input (fewer than two dimensions, a dimension that is not a whole number >= 1, L not a whole number >= 1, a missing or negative or fractional price, a method that does not exist for the problem) gives status `INVALID`; a size that a method refuses (brute force above 12 matrices or L = 20, a recursion deeper than 20,000) gives status `TOO_LARGE`; neither raises.
- **Shipped algorithm for both: bottom-up dynamic programming with a split table.** Chain: `cost[i][j] = min over k of cost[i][k] + cost[k+1][j] + p(i-1) p(k) p(j)`, `O(n^3)` time, `O(n^2)` space, n(n-1)/2 cells and (n^3 - n)/6 split candidates. Drum: `best[l] = max over k of price(k) + best[l-k]`, `O(L^2)` time, `O(L)` space, L cells and L(L+1)/2 candidates.
- **Baselines.** The same recurrences as a **memoised recursion** (same cells and candidates, plus the recursive calls; it is as deep as n or L, so it runs in a helper thread with a large stack and a raised recursion limit and refuses depths above 20,000); for the drum the **greedy cut by price per length** (pieces ordered by exact price/length, ties longer piece first, each length cut as often as it fits, `O(L log L)`, not optimal; its note says so);
  and **brute force** (all bracketings, Catalan(n - 1), n <= 12; all cuts, 2^(L-1), L <= 20).
- **Tie rules (the same in every method and in the test references).** *Chain:* among splits of equal cost the smallest split point k, in every sub-chain. *Drum:* among cuts of equal price the one with the fewest pieces; among those the lexicographically smallest list of pieces (smallest first piece, then smallest second piece, ...).
  With these rules the answer is unique, so dp, memo and brute return exactly the same bracketing or cut (checked by the tests).
- **Campaign interface:** `chains.solve_chain(dims, method)` with method `dp`, `memo` or `brute` returns `ChainPlan(status, bracketing, cost, ops, note)`; `chains.solve_drum(prices, length, method)` with method `dp`, `memo`, `greedy` or `brute` returns `CutPlan(status, pieces, price, ops, note)`; both take an optional `deadline`.
- **Retained or changed since the proposal:** retained (bottom-up DP primary, memoised recursion and brute force as baselines, greedy cut by price per length for the drum). Added: the tie rules, the status `TOO_LARGE` and the thread for the deep recursion. Not implemented: the plain recursion `O(2^L)` for the drum without memoisation (it is the brute force above).

### Modules B, F (Hamza)

- **B input/output:** undirected roads, nonnegative destination penalties, positive minutes, HQ source and blocked road ids. Each directed step costs minutes plus destination penalty. The result includes the selected route/road ids, cost, every source distance, reachable vertices and a deterministic fewest-roads route/cost. Unreachable target: `NO_ROUTE`, empty path, null cost; malformed input raises `InvalidInputError`.
- **B primary:** counted binary-heap Dijkstra, O((V+E) log V), plus BFS for reachability/hops. Baselines: early-stopping Bellman-Ford O(VE) and BFS as a nonoptimal travel-cost policy. Adjacencies are ordered with the existing project merge sort by neighbour then road id; equal-cost predecessors keep the first found. Heap ties use location id. Preprocessing/output ordering is included in measurements; O(V+E) storage.
- **B interface:** `routes.solve(locations, roads, target, method="dijkstra", blocked=(), source=0, deadline=None)`. Methods: `dijkstra`, `bellman`, `bfs`. Retained the proposal choices; the proposed array Dijkstra is not implemented. A source-to-source route costs zero.
- **F input/output:** the same map with positive cable costs; selected roads and total cable cost, plus component vertex sets. Kruskal with path compression/union by size is primary, O(E log E + E alpha(V)); heap Prim is the independent baseline, O((V+E) log V). O(V+E) storage. Both return `FOREST` if disconnected, `OK` for one component, `EMPTY` for an empty requested subset. Equal-cost edges use road id as the deterministic tie break. Retained the proposal choices; Boruvka and array Prim were candidates only.
- **F interface:** `networkplan.solve(locations, roads, method="kruskal", blocked=(), vertices=None, source=0, deadline=None)`. All components by default; pass `vertices=route.reachable` for HQ-only cable planning. Both network modules accept a deadline and raise `TimeBudgetExceeded`; the harness records DNF. Graph records are in `src/network.py`; teammate models and implementations are unchanged.
- **Campaign interface:** `run_campaign(case, calendar=None, policy="optimized", deadline=None)` calls the existing A/B/C/D entry points with the day's transformed input, including exactly `rescue.available_on_day` and `rescue.solve`. Optional review calls F plus `chains.solve_chain(dims, "dp")` and `chains.solve_drum(prices, length, "dp")`. The default is the official calendar; section 13 documents the daily state, exact baselines and output verification.

## 6. Operation counts (Section 7.3 of the statement)

The column `ops` of `results.csv` holds one number per run; the breakdown is in the column `note`.

| Module and method | Family | What `ops` counts |
|---|---|---|
| A, DP | selection and tabulation | table cells computed: for each kept crate of weight w, `width - w + 1` evaluations of the recurrence (the filtering pass over the crates is in `items` in the note) |
| A, greedy | ordering | key comparisons (calls of the exact ratio comparison) + element moves (elements written while merging); the final pass over the sorted crates is in the note |
| A, brute force | hard problems | subsets evaluated (always 2^n) |
| D, heap | queues | key comparisons between two `(-priority, tick, id)` keys + heap slots written (hole sifting, so a swap that would count 2 counts 1 per level) |
| D, scan | queues | key comparisons during scans (backlog - 1 per release) + list moves (one per append, one per removal; the released alarm is replaced by the last one) |
| C, greedy | ordering | comparisons + moves of our merge sort by (finish, id) + windows examined in the pass |
| C, dp | selection and tabulation | the same sort + binary-search probes + windows examined + table cells (one per window) |
| C, plain DP | selection and tabulation | the same sort + pairs examined (exactly n(n-1)/2) + table cells |
| C, brute force | hard problems | subsets evaluated (always 2^n) + windows examined |
| G, DP (chain) | selection and tabulation | table cells (n(n-1)/2) + split candidates evaluated ((n^3 - n)/6); the memoised recursion has the same two counts and its recursive calls (1 + 2 x candidates) are `calls` in the note |
| G, DP (drum) | selection and tabulation | table cells (L) + candidates (L(L+1)/2); the memoised recursion has the same counts and L(L+1)/2 + 1 calls |
| G, greedy cut | ordering | comparisons + moves of our merge sort of the L pieces + pieces examined |
| G, brute force | hard problems | bracketings (Catalan(n-1)) or cuts (2^(L-1)) enumerated |
| B/F, all methods | networks and ordering | adjacency-edge examinations + successful relaxations + key comparisons + element/heap-slot writes + union-find root/parent traversals; core counts include output ordering and BFS reachability; adjacency sorting is reported separately as pre_comparisons/pre_moves; input validation is timed but its field checks are not counted |

Preprocessing is counted separately: module D first checks in one pass that ticks do not decrease (m - 1 comparisons) and runs the merge sort only if they do; this is
`pre_comparisons` and `pre_moves` in the note. Modules C and G count the validation pass over the input as `pre_items` in the note (and the pair tests of brute force in C as `pre_pair_tests`); recursive `calls` are in the note, not in `ops`. Memory (`mem_bytes`) is the peak of `tracemalloc` during one extra run, beyond the input; it is skipped (and said so in the note) when a run takes more than 8 s, because `tracemalloc` slows the run down.

## 7. Measurement method

- One discarded warm-up run, then the median of 5 runs with the interquartile range (linear interpolation of the quartiles), one thread, garbage collection switched off while a run is timed, data loading excluded.
  Runs shorter than 10 ms are timed as a batch and divided (the batch size is in the note).
- A run that passes 300 s is a DNF: the algorithm receives a deadline and raises `TimeBudgetExceeded`, and the row gets status DNF.
- Growth claims use a least-squares fit on at least 5 sizes (log-log for polynomial, semi-log for exponential) with the 95 % interval from the t distribution, R^2 and, in `results/predictions-vs-measurements-AD.md`, the relative error between prediction and measurement.
- **Hardware and software of the numbers in `results/`:** `results/environment.json`: Windows 11, an Intel laptop CPU (family 6, model 154, 12 logical processors), CPython 3.13.7, one thread, 5 timed runs after 1 warm-up.
  The numbers were measured on this one laptop. **The speed of the laptop changed during the first full run** (time per DP cell between 139 and 398 ns). Rounds 1 and 3 were therefore repeated with the charger connected and the power mode on best performance (about 85 ns per cell for 200 to 3200 crates);
  rounds 2 and 4 come from the first run and have not been repeated. One long run (6400 crates) still changed speed during its five timed runs (IQR 8.8 s). Absolute times and some fitted slopes of
  times are distorted, while operation counts, memory and quality numbers are exact and repeatable. Details and the list of affected predictions are in `prediction_log.md`. Another machine gives other absolute times.
- **Modules C and G** use the same protocol (`runC.py`, `runG.py`). The numbers of C and G were measured on Adan's laptop: `results/environmentC.json` and `results/environmentG.json` (Windows 10, Intel64 Family 6 Model 142, 8 logical CPUs, CPython 3.14.6, one thread, 5 timed runs after 1 warm-up).
  The charger and best-performance state of that laptop could not be verified and the rounds were not repeated; some runs have a large IQR (up to 30 % of the median, and the memoised chain at n = 40 is an outlier), see the "After the run" notes. The memoised recursion of G uses a helper thread with a large stack only to avoid a stack overflow; the computation stays single-threaded.
- Prediction log: `prediction_log.md` (entries written and committed before each round; "After the run" notes written afterwards). It holds the entries of Ayna (A, D) and of Adan (C, G; sections "Module C" and "Module G"); the ids of C and G start with C and G.

## 8. Results at a glance (modules A, C, D and G)

Full tables: `results/comparison-AD.md`, `results/comparison-C.md`, `results/comparison-G.md`; fits: `results/fits-AD.md`, `fits-C.md`, `fits-G.md`; plots with captions: `results/plots/` (`captions-C.md`, `captions-G.md`).

| Module | Experiment | Result |
|---|---|---|
| A | A-scale-n, 200 to 6400 crates | counted cells grow with slope 2.08 +- 0.12; DP time slope 2.22 +- 0.28 (2.05 +- 0.21 without the 6400 point, whose run changed speed); about 85 ns per cell for 200 to 3200 crates; 31.3 s at 6400 crates (161 million cells; IQR 8.8 s); greedy 40 ms; time against cells has slope 1.07 +- 0.14 |
| A | A-scale-W, n = 1600 | DP time slope 0.86 +- 0.27 in W (cells: 1.005; the first point, W = 522, is out of line at 195 ns per cell, the others cost 85 to 99 ns); greedy operation count exactly independent of W (time slope -0.08, R^2 0.07: no clear trend) |
| A | A-small-n, 8 to 20 crates | brute force doubles per crate (base 2.02, interval 1.94 to 2.11), DP is 878 times faster than brute force at n = 20 (0.67 ms against 585 ms; this round is from the first, slower run) |
| A | quality | DP equals the claim in 20 of 20 tier S cases; greedy is optimal in 7 of 20 tier S and 7 of 20 tier M cases, and loses 44 % on the trap-47 cases (mean greedy / DP 0.56) but only 0.2 % on tier M and 0.01 % on tier L |
| D | D-scale-m, 250 to 64000 alarms | heap slope 1.12 +- 0.11 (operations: 1.16), scan slope 1.96 +- 0.05 (comparisons: 1.99); scan / heap time 1.2 at 250, 29 at 16000, 113 at 64000 (heap 0.26 s, scan 29.8 s) |
| D | D-dnf, 256000 alarms | scan DNF (more than 300 s; plain quadratic growth from 29.8 s at 64000 alarms gives about 480 s, the fitted line about 390 s); heap 2.40 s, but this round is from the first, slower run and a repeat is expected to give about 1.2 s |
| D | quality | the mean wait of all alarms is the same under urgency order and first-come-first-served; priority 9 and 10 alarms wait 1.5 ticks (urgency) against 639 (FIFO) on tier L |
| C | C-scale-n, 47 to 3000 windows | time slopes: greedy 1.07 +- 0.28, dp with binary search 1.26 +- 0.10, plain O(n^2) DP 1.85 +- 0.21; at 3000 windows greedy 31 ms, dp 46 ms, plain DP 0.60 s (13 times dp); the plain DP examines exactly n(n-1)/2 pairs |
| C | C-small-n, 8 to 20 windows | brute force grows by 1.95 per window (exactly 2^n subsets), 0.63 s at n = 20; the DP is faster than brute force from n = 8 and 3,900 times faster at n = 20 |
| C | C-dnf, 200,000 windows | plain DP: DNF (more than 300 s; the fitted line extrapolates to about 1,065 s); dp 4.37 s (5,771 windows, value 360,121) |
| C | quality (62 cases) | greedy count equals the optimum in 62 of 62 cases and the DP value equals the claim in 20 of 20 tier S cases; for the value the greedy rule gives up 16 % (S), 23 % (M), 26 % (L), 28 % (X) on average and 73 % in the worst small case |
| G | G-chain-n, 10 to 640 matrices | DP time slope 2.89 +- 0.15 (operations 2.95: exactly (n^3 - n)/6 candidates), memoised recursion 2.92 +- 0.28; at n = 640 DP 13.4 s, recursion 48.7 s (3.6 times); time against operations has slope 0.98 |
| G | G-drum-L, 63 to 2000 | DP slope 2.03 +- 0.10, memoised recursion 2.02 +- 0.05 (a recursion 2,002 calls deep), greedy cut 1.16 +- 0.03; at L = 2000 DP 0.35 s, recursion 1.17 s, greedy 13.8 ms |
| G | G-small-chain, G-small-drum | brute force enumerates exactly Catalan(n-1) bracketings and 2^(L-1) cuts (growth 3.24 per matrix, 2.0 per unit of length); the DP is 3,900 times faster at n = 12 and 13,400 times at L = 20; dp, memo and brute return the same answer at every size |
| G | quality (62 cases) | the DP price equals the claim in 20 of 20 tier S cases; the greedy cut is optimal in 61 of 62 cases (worst 0.977 of the optimum, tier X case 15-49); multiplying from left to right costs 4.5 (S), 15.8 (M), 16.9 (L) and 14.9 (X) times the optimum on average |

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

### Module C - rescue scheduling

- **Ship:** the earliest-finish greedy rule when the objective is the number of windows, and the weighted-interval DP with binary search when it is the total value.
- **Evidence (experiments C-scale-n, C-dnf and the quality table):** the greedy rule gives the optimal count in 62 of 62 sampled cases (and reproduces the claim in 20 of 20 tier S cases), at 31 ms for 3000 windows. For the value it gives up 16 to 28 % on average and up to 73 % in a small case, so the DP is needed there;
  it costs 46 ms for 3000 windows and 4.4 s for 200,000, where the plain `O(n^2)` DP does not finish in 300 s.
- **Clash between theory and practice, and what we chose:** theory says that the greedy rule is optimal for the count and not for the value, and the data agree on both. What surprised us is the size of the loss (a mean of 16 to 28 %, not the 30 to 42 % we predicted, but a worst case of 73 %).
  We ship the DP for the value because the staffing decision is made once a day and costs milliseconds, and we ship greedy for the count because it is provably optimal and the fastest.
- **Assumption:** the windows compete for nothing else than time (one team that can staff one window at a time, the value of a window does not depend on the others) and the day filter is the only availability rule.
- **It would be wrong when** windows also compete for another resource (a second team, a shared vehicle): the method fails because the compatibility test only looks at start and finish. We did not simulate a second resource; the measurement that tells is to staff the plan of a day with the real resource list and count the windows that cannot be served.

### Module G - chains and cuts

- **Ship:** the bottom-up DP for both problems (the memoised recursion and brute force are baselines; for the drum the greedy cut is the fast fallback).
- **Evidence (experiments G-chain-n, G-drum-L and the quality table):** the DP reproduces the claim `drum_opt` in 20 of 20 tier S cases and agrees with the memoised recursion and brute force in all small cases. A chain of 320 matrices (a little above the largest of the data) takes 1.5 s and a drum of length 2000 takes 0.35 s;
  the memoised recursion is 3.4 to 3.6 times slower for the same counts of cells and candidates and needs a thread with a large stack from depth 500 on.
- **Clash between theory and practice, and what we chose:** the greedy cut by price per length is not optimal in theory (the textbook example loses 10 %), but on the prices of the data it is optimal in 61 of 62 cases (worst 0.977) and 25 times faster than the DP at L = 2000 (13.8 ms against 0.35 s).
  We still ship the DP: a drum is cut once, the DP costs a third of a second, and the one failing case shows that the greedy cut has no guarantee; the greedy cut is the fallback when L is so large that `L^2` is too slow.
- **Assumption:** n <= 300 matrices (about 4.5 million split candidates, about 1.3 s) and L <= 2000 (2 million candidates), as in the data; the prices follow a concave shape with noise (price per length falling with the length), which is why the greedy cut looks good.
- **It would be wrong when** n grows to thousands (the chain DP is cubic: n = 2000 has about 1.3 x 10^9 candidates, an estimated 7 minutes at 0.31 microseconds each; we did not run it), or when the price table gives a bonus for long pieces (then the greedy cut can fail badly).
  **Measurement that tells:** compute `(n^3 - n) / 6` (chain) or `L (L + 1) / 2` (drum) before the run and compare it with the budget (a rate of about 0.31 microseconds per candidate for the chain and 0.17 for the drum on our laptop); and compute the greedy price next to the DP price on a sample of the real price tables, as `quality-G.csv` does.
  A faster chain algorithm (Hu and Shing, `O(n log n)`) exists; we did not implement or measure it.

### Modules B, F

- **B: ship heap Dijkstra**, with BFS for reachability and hop count. In `B-scale-V`, seven sizes (16 to 1024), the largest Dijkstra run took 11.78 ms versus 16.69 ms for Bellman-Ford. All 867 sampled target/wave comparisons agree on shortest cost; BFS costs up to 20 times the optimum. Assumption: positive step costs and sparse networks. Negative weights invalidate Dijkstra; validation rejects them. Monitor edge signs and E/V before selecting the method. The early-stopping Bellman-Ford baseline can be competitive on small, favourably ordered maps.
- **F: ship Kruskal**, with heap Prim as the check. In `F-scale-V`, the largest runs took 17.04 ms (Kruskal) and 18.99 ms (Prim), a small difference specific to this network. All 289 sampled wave-state forest comparisons agree. Assumption: sparse maps; for dense maps consider array Prim. Monitor E/V, memory and the measured crossover rather than claiming Kruskal always wins.
- Full evidence and failure-mode contribution for Ayna: `results/comparison-BF.md`, `fits-BF.md`, `quality-BF.csv`, `plots/captions-BF.md`. Growth uses connected prefixes of one sampled real L graph, not independent graphs or pooled networks. Times are one-machine/session measurements with unverified power state; seven sizes do not establish a universal exponent. No five-minute DNF is claimed at these sizes.

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
- **Modules C and G.** Pure Python: about 0.31 microseconds per split candidate of the chain DP and about 0.17 for the drum DP; the memoised recursion is 3.4 to 3.6 times slower and runs in a helper thread above depth 500. Sizes beyond n = 640 matrices, L = 2000 and 200,000 windows were not run.
  The measurements of C and G come from one run on one laptop whose power state could not be verified; some IQR values are large (the memoised chain at n = 40, the DP at n = 320). The pools of windows never overlap across joined cases (shifted by 1440 minutes), so no experiment has thousands of windows inside one day.
  The drum experiments use prefixes of one real price table (case 12-47); the quality numbers of the greedy cut are specific to price tables of this shape. Chains have no claim in the master data, so the chain optimum is checked only against brute force and an independent reference.
  The tie rules of C (set of equal total) and of dpquad and brute force are weaker than those of greedy and dp; module G has full tie rules. `rescue.available_on_day` raises an exception for a bad day or id (it returns a list); every other entry point returns a status.
- Defects in the master dataset: none found in the sampled cases used by modules A and D (their tier S optima matched the claims in 20 of 20 cases; the same for the windows and drums of C and G, whose tier S optima matched the claims in 20 of 20 cases); we did not check the whole master dataset.

## 11. Changes after the proposal

| Module | Proposal | Now | Reason |
|---|---|---|---|
| A | DP primary; greedy and brute force baselines | unchanged; table width reduced to `min(W, total weight)` | smaller table when the capacity exceeds the total weight |
| D | heap primary; linear scan baseline | unchanged; first-come-first-served added only as a comparison policy | to show what the urgency order buys; it is not a solution of module D |
| C | greedy for the count, DP with binary search for the value; plain DP and brute force as baselines | unchanged; greedy on the value objective added as a measured baseline; statuses `EMPTY` and `INVALID` instead of exceptions | to show what the greedy rule gives up on the value and to keep the campaign from crashing on a day with no windows |
| G | bottom-up DP primary; memoised recursion, greedy cut and brute force as baselines | unchanged; tie rules fixed; status `TOO_LARGE` and a thread with a large stack for the memoised recursion | a deep recursion (L = 2000 calls deep) must be an answer or a status, never a crash; the tie rules make dp, memo and brute return the same answer |
| B, F | heap Dijkstra/BFS and Kruskal, Bellman-Ford/Prim baselines | retained; counted heap/union-find, explicit statuses, configurable campaign and input contracts added | deterministic integration and independent cross-checking |

## 12. References

- T. H. Cormen, C. E. Leiserson, R. L. Rivest, C. Stein, *Introduction to Algorithms*, 4th ed., MIT Press, 2022: dynamic programming for the 0/1 knapsack problem, binary heaps, merge sort; the activity-selection greedy rule (module C), matrix-chain multiplication and rod cutting (module G).
- J. Kleinberg, E. Tardos, *Algorithm Design*, Pearson, 2005: interval scheduling and weighted interval scheduling with binary search (module C).
- T. C. Hu, M. T. Shing, "Computation of matrix chain products", SIAM Journal on Computing, 1982 and 1984: the O(n log n) chain algorithm that we did not implement (module G).
- S. Martello, P. Toth, *Knapsack Problems: Algorithms and Computer Implementations*, Wiley, 1990: greedy ratio rule and its worst cases.
- Course project statement (Project Statement, LIFELINE) and the master dataset `master_release_v1`.

## 13. Hamza's integration, backend and report handoff

The existing A/C/D/G implementations and result rows were preserved. Hamza's
results are the B/F rows in `results/results.csv`, the BF files and the official
campaign artifacts. Teammate implementations and 169 existing result rows are preserved.
`hamza_work.md` lists the deliverables and remaining handoff decisions.

### Campaign and official calendar

The original Project Statement is now available. `calendars/official.json`
implements section 7.4, page 7, and is the default for the CLI and backend.
`calendars/example.json` remains a labelled historical custom example; the
old campaign-example output is historical and is not official evidence.

| Day | Change applied to base data | Blocked roads | Destination |
|---|---|---|---|
| 1 | Normal | none | target_0 |
| 2 | minutes = ceil(3 * base minutes / 2), tools x2, extra alarm (tick 0, priority 9) | wave 0 | target_1 |
| 3 | food x2 | wave 1 | target_2 |
| 4 | penalties >= 2 doubled | wave 2 | target_0 |
| 5 | medicine x3, extra alarm (tick 0, priority 10) | wave 3 | target_1 |
| 6 | Flood | union of all waves | target_2 |
| 7 | No loading; one-way evacuation from HQ | union of all waves | target_0 |

Each day starts at HQ. Days 2-5 close only the listed wave, not a cumulative
union. Wave index i wraps modulo the number of waves; indices refer to
ascending stored wave-label positions, normalizing both 0-based and 1-based
master groups. Changes to minutes, penalties, values, alarms and rescue
availability start afresh from base data each day. Only days 6 and 7 share the
all-wave closure. Unreachable destinations skip the trip and load, but rescue
and alarm processing still run. Day 7 is a real trip with no load, and its cost
is included if reachable. Costs describe the outbound route; the statement
does not prescribe a second return-leg computation.

The statement specifies no removal of used crates or expiry cutoff, so official
runs reset stock daily and add neither rule. Custom calendars retain optional
`inventory_mode="consume"`, `hour` and `capacity` controls.

A calendar has `name`, optional `note`, `inventory_mode` (`daily` or `consume`),
`closure_mode` (`daily` or `cumulative`) and seven days in order. Custom calendars
without closure_mode retain the former cumulative behavior. Daily fields:

| Field | Meaning |
|---|---|
| day, event | Day 1..7 and optional display label |
| target or target_key | Literal location id, or target_0/target_1/target_2; never both |
| close_waves | Exact stored wave labels |
| wave_indices | Zero-based positions, modulo number of waves |
| all_waves | Close every listed wave |
| close_roads, open_roads | Explicit ids; reopening applied after closures |
| minutes_ratio | Positive integer numerator/denominator; rounded up exactly |
| penalty_threshold, penalty_multiplier | Multiply penalties at/above threshold |
| multipliers | Category 0..4 to a nonnegative integer; base crate values multiplied exactly |
| extra_alarms | Additional [tick, priority] pairs for that day |
| hour, capacity | Optional custom expiry cutoff / capacity override |
| load | Whether loading is permitted; default true |
| objective | Rescue count or value (default value) |
| evacuation | Day-7 trip with load=false |
| review | Optional F/G review, enabled on official day 7 |

Three independent runs receive identical daily inputs:

- Optimized: A DP, B Dijkstra, C greedy-count/DP-value, D urgency heap,
  F Kruskal, G bottom-up DP.
- Algorithm baselines: A ratio greedy, B Bellman-Ford, C quadratic DP,
  D urgency scan, F Prim, G memoized chain/drum. B/C/D/F/G agree exactly;
  the loading heuristic is compared on its value gap.
- Simple policies: ratio loading, BFS travel, earliest-finish value scheduling,
  FIFO alarms, and greedy drum cuts. These are explicitly nonoptimal policies,
  not replacements for the exact algorithm baselines.

`src/campaign_checks.py` independently verifies open-road route costs,
reachability, capacity and daily load value, rescue availability/compatibility,
exact alarm order/ticks, HQ cable connectivity and G output reconstruction.
The standard-library heap in that verifier is not used by decision algorithms.
Every day records its input changes, methods, decisions, checked constraints
and outcome. Full base input is stored once per case in results/campaign/*.json.
The case input plus each day's changes reconstructs the complete daily input.

Official evidence covers 1-06 (S), 1-26 (M), 2-40 (L), 4-47 (trap 47) and
2-48 (trap 48), selected from seed-41 every-seventh tier samples: 105 daily
policy records, all checked. Trap 47's normal-day greedy load reaches 57.071%
of optimum; trap 48's BFS route costs 5.333 times the cheapest route. The large
landslide case explicitly reports disconnected targets on six days.

`python experiments/run_campaign.py --master MASTER` reproduces all five runs,
three policies each, readable output, CSV comparisons and three report figures.
For one case, the command in section 2 prints a readable table with inputs,
methods and checked constraints. Use --output PATH for full JSON, or --format
json for JSON on screen. Different objectives remain separate metrics, not a
combined score; aggregate rescue totals require the same objective each day.

### Loader and validation

`src.loader.load_case(master, case_id)` and `load_cases(master, ids, graph_only=False)`
stream only the relevant CSV tables and retain requested cases. The typed records
match the existing teammate interfaces. Validation checks schemas, integer cells,
unique ids/serials, positive edge weights/dimensions, categories, endpoints,
closure references, targets and contiguous G indices. This is an Iteration 2
input contract check, not a claim to revalidate every Phase 1 rule/optimum across
all 3,622 cases. `verify_checksums` separately checks all 20 supplied SHA-256 hashes.
Text group labels such as `43R` are preserved. Optional graph-only loading avoids
reading unrelated large tables for B/F experiments.

### Frontend API

Python interface: `Backend("MASTER")` exposes `list_cases()`, `case(case_id)`,
`route(case_id, target, method="dijkstra", blocked=())`,
`network(case_id, blocked=(), method="kruskal", reachable_only=True)`,
`campaign(case_id, calendar=None, policy="optimized")`, `chain(case_id, method="dp")`
and `drum(case_id, length=None, method="dp")`. An eight-case cache avoids repeated
CSV scans. Results are JSON-ready dictionaries; individual records in case data
serialize as field-order arrays with the fields documented in their classes.

`python -m src.server --master MASTER --port 8000` binds only to 127.0.0.1.
GET `/health`, `/cases`; POST `/case`, `/route`, `/network`, `/campaign`, `/chain`,
`/drum`, using a JSON object with the corresponding Python argument names.
POST `/campaign` accepts `{"case_id":"41-00"}` for the official default,
or add policy="baseline"/"simple" or a custom calendar.
Example POST `/route` body: `{"case_id":"41-00","target":7,"blocked":[]}`.
Errors return JSON with HTTP 422, unknown paths 404. The server is a local,
single-request-at-a-time adapter; use the Python functions or a same-origin dev
proxy from the frontend. No frontend was replaced or built here.

### Evidence for the final report

- `results/comparison-BF.md`, `fits-BF.csv`, `fits-BF.md`, `quality-BF.csv`:
  result tables, recommendations, assumptions and failure-mode paragraph.
- `results/plots/B-*.png`, `F-*.png`, `captions-BF.md`: six figures, captions and timing limits.
- `results/predictions-vs-measurements-BF.md`: pre-run predictions versus outcomes.
- `results/fault-injection-BF.txt`: 15 seeded faults caught in disposable copies;
  one deliberately broken relaxation loops and is caught by a five-second timeout.
- `results/test-summary-BF.txt`: final unit/integration/HTTP test run.
- `results/campaign-comparison.md`, `campaign-daily.csv`, `campaign-summary.csv`
  and `campaign/*.json`: official daily outcomes and baseline comparisons.
- `results/sample-outputs/campaign-official.txt`: readable program output.
- `results/plots/campaign-*.png`, `captions-campaign.md`: three report figures.
- `results/predictions-vs-measurements-campaign.md`: official-campaign predictions.
- The earlier campaign-example.json remains historical, explicitly nonofficial evidence.

Ayna still owns `report.pdf` and the ranked final failure modes; Adan owns the
frontend. Their output files were not rewritten. The handoff and reproducible commands
above accompany the B/F and campaign implementation.


### Completion and remaining team work

Hamza's modules B/F, their unit/reference tests and seven-size experiments,
the shared loader/validation, official seven-day coordinator/CLI, backend/API,
output invariants, 15 fault injections and report-ready tables/plots/test
summary are complete. B/F round 2 separates preprocessing counts, reports fit
confidence intervals/R-squared and numerical prediction relative errors.

No calendar configuration remains for Ayna. She incorporates the supplied
B/F and campaign evidence into report.pdf and finalizes her ranked failure
modes. Adan connects his frontend to the documented API. The group performs
the final demo and submission packaging. Their report/frontend files and the
unrelated local proposal changes were not overwritten.

## 14. Interface: The Lifeline Gazette (Adan)

`python -m frontend --master MASTER --open` serves the interface at `http://127.0.0.1:8000/` (change with `--port`; do not run
`src.server` on the same port at the same time). It needs only the Python standard library and a browser; the fonts come from
Google Fonts and fall back to system serif fonts offline.

| Page | What it shows |
|---|---|
| The Daily Edition | one of the seven campaign days: route map (B), load manifest (A), alarm dispatches (D), rescue timetable (C), checked constraints; day 7 adds F and G |
| Week in Review | the week's totals and, on request, our methods against the algorithm baselines and the simple policies |
| The Map Room | live B and F: choose target and method, close roads or waves, show the cable network |
| The Works Desk | live G: matrix chain and drum cut with every method |

All results come from the endpoints of section 13; the pages compute no decisions themselves. Maps are schematic, because the
data has no coordinates for locations; networks above 260 locations show the part around the route.

The server reuses the request handler of `src/server.py`. One difference: when it starts, it notes where the rows of each case lie
in the CSV files (about 20 s), and then passes only those rows to the unchanged `src.loader.load_case`. Opening a case then takes
about 1 s instead of about 1 minute on our machine. `tests/testfrontend.py` checks that both ways give the same case data on a
small fixture. Restart the server if the dataset files change.
