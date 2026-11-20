# Captions of the plots of module G

**G-chain-time-vs-n.png**: Figure G1. Median time on pooled tier L dimensions; bars are the interquartile range. Both axes are logarithmic: the bottom-up DP and the memoised recursion follow lines of slope close to 3 (n^3 split candidates); the recursion is a constant factor slower because it makes two calls per candidate.

**G-drum-time-vs-L.png**: Figure G2. Median time on prefixes of one real price table. Both axes are logarithmic: the DP and the memoised recursion follow lines of slope close to 2 (L^2 candidates), the greedy cut a line of slope a little above 1 (sorting L pieces).

**G-small-chain.png**: Figure G3. Median time on pooled tier S dimensions. The vertical axis is logarithmic and the horizontal one linear: brute force over all bracketings (Catalan numbers) is almost a straight line, the DP and the recursion stay almost flat.

**G-small-drum.png**: Figure G4. Median time on prefixes of one tier M price table. The vertical axis is logarithmic and the horizontal one linear, so brute force over all 2^(L-1) cuts is a straight line while the DP, the recursion and the greedy cut stay almost flat.

**G-operations.png**: Figure G5. Operations as defined in the README: table cells plus split candidates for the DP (chain: n^3 / 6, drum: L^2 / 2), comparisons plus moves plus pieces examined for the greedy cut. Solid lines belong to the chain, dashed lines to the drum; the horizontal axis is n for the chain and L for the drum.

**G-greedy-quality.png**: Figure G6. For every sampled case, the total price of the greedy cut (best price per length first) divided by the optimal price found by the DP (1.0 = the greedy cut is optimal). Black bars are the means per tier.

**G-chain-left-to-right.png**: Figure G7. For every sampled case, the number of scalar multiplications of the left-to-right bracketing ((A1 A2) A3) ... divided by that of the optimal bracketing found by the DP (1.0 = left to right is optimal). Black bars are the means per tier; the vertical axis is logarithmic.
