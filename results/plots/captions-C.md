# Captions of the plots of module C

**C-time-vs-n.png**: Figure C1. Median time on pooled tier L windows; bars are the interquartile range. Both axes are logarithmic: the greedy rule and the DP with binary search follow lines of slope a little above 1 (n log n), the plain DP of slope close to 2 (n^2). The hollow marker and the dotted line at the right belong to the 5 minute run: the dashed line is the 300 s limit.

**C-small-inputs.png**: Figure C2. Median time on pooled tier S windows. The vertical axis is logarithmic and the horizontal one linear, so brute force (2^n subsets) is a straight line while the DP and the greedy rule stay almost flat.

**C-operations.png**: Figure C3. Operations as defined in the README: comparisons + moves of our merge sort, binary-search probes, windows examined and table cells. The two n log n methods differ by a constant factor of about 1.5; the plain DP examines n (n - 1) / 2 pairs.

**C-greedy-quality.png**: Figure C4. For every sampled case, the total value of the earliest-finish plan divided by the optimal total value found by the DP (1.0 = the greedy plan is optimal). Black bars are the means per tier. The greedy rule is optimal for the number of windows in every case, but it never looks at values.
