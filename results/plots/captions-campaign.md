# Official campaign figure captions

All figures are deterministic results from master_release_v1 and the official
section 7.4 calendar, with identical daily inputs for every policy.

- campaign-values.png: cumulative delivered value of reachable day-1–6 loads;
  day 7 has no loading. Optimized is exact knapsack, baseline/simple use ratio
  greedy. Higher is better; values reset to base before the day's multiplier.
- campaign-urgent-wait.png: mean wait of priority-9/10 alarms over all seven
  days. Optimized heap and baseline scan use urgency order; simple uses FIFO.
  Lower is better. This is a scheduling metric, not total alarm wait.
- campaign-difficult.png: normal-day trap 47 loading value ratio (higher is
  better), and trap 48 travel cost ratio (lower is better); a reference at 1
  marks the exact optimum. They demonstrate different failure modes, not a
  combined score. No timing/error bars are implied by these quality plots.
