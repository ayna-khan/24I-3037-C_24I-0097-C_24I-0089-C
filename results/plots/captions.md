# Captions of the plots

**A-time-vs-n.png**: Figure A1. Median time of the DP and of the ratio greedy rule on pooled tier L crates; bars are the interquartile range. Both axes are logarithmic: the DP follows a line of slope about 2 (n x W work), the greedy rule about 1.

**A-time-vs-W.png**: Figure A2. Median time for 1600 crates while only the capacity grows. The DP is linear in W (slope near 1); the greedy rule does not depend on W.

**A-small-inputs.png**: Figure A3. Median time on pooled tier S crates. The vertical axis is logarithmic and the horizontal one linear, so brute force (2^n subsets) is a straight line and the DP stays almost flat.

**D-time-vs-m.png**: Figure D1. Median time to release all alarms of pooled tier L streams; bars are the interquartile range. The linear scan is quadratic (slope about 2) because the backlog grows in proportion to m; the heap is close to m log m. The dashed line is the 300 s limit.

**AD-operations.png**: Figure AD1. Operations as defined in the README: table cells (A, DP), comparisons plus moves (A, greedy; D, heap and scan). Solid lines belong to module A and dashed lines to module D; the horizontal axis is n for A and m for D.

**A-greedy-quality.png**: Figure A4. For every sampled case, the value of the ratio-greedy load divided by the optimal value found by the DP (1.0 = greedy is optimal). Black bars are the means per group of cases.

**D-wait-of-urgent-alarms.png**: Figure D2. Mean number of ticks that an alarm of priority 9 or 10 waits before release, averaged over the sampled cases of each tier. The mean wait of all alarms is identical in both orders; only who waits changes.
