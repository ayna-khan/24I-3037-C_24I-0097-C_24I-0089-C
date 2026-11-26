# LIFELINE: Algorithmic Relief-Command Engine - Iteration 1 Approach Note
Group 41 | Dur E Adan (24I-3037-C), Ayna Khan (24I-0097-C), Hamza Sardar (24I-0089-C) | Design and Analysis of Algorithms

**General design.** The group seed is $s=41$. Every module of every case draws its randomness from a separate generator seeded with the string `41-k-module`, so the workbook is reproduced exactly by the single command given in the generator README. Unless stated otherwise, sizes are drawn uniformly from the ranges of the tier of the case. Crate weights lie in 1-20 kg, values in 10-100, expiry hours in 0-999, and the truck capacity is between 25% and 55% of the total crate weight.

## 1. From story to numbers
| **Case study** | **Main choices and the sentence of the story that justifies them** |
|---|---|
| 1 Delta Flood | The network is a random spanning tree with additional roads, with average degree 2.2-3.2 ("a flat delta of small villages joined by raised roads"). Penalties are drawn from $\{0,1,2,4,6\}$ with weights favouring large values and are then repaired until at least 40% of the locations have penalty $>= 2$ ("food and water matter most" while roads "go under water"). Three to five waves are generated, each with at most $E/6$ roads ("in waves"). At least 55% of the crates are food or water. |
| 2 Mountain Earthquake | Each node is attached to one of the three previous nodes, producing a long, narrow valley with average degree 2.0-2.6 ("a few roads and almost no alternatives"). At least 45% of the crates are medicine or tools. Alarm arrivals contain bursts around random "aftershock" ticks, and priorities are weighted towards 6-10 until the mean is at least 6.3 ("bursts of urgent calls"). |
| 3 Coastal Cyclone | At least 28% of the locations are shelters ("a port city and fishing villages"). Windows last 5-120 minutes and are placed in a shrinking time horizon until each window overlaps at least 2.3 others on average ("short and overlap"). The radio log is uniform noise over all 38 symbols ("full of noise"), so at least 30 symbols occur. |
| 4 Urban Flash Flood | The average degree is 3.6-5.0 ("many alternative routes"). On tiers M and L the alarm rate is 1.55-1.75 per tick ("faster than anyone can answer"). At least 10% of the crates are rare ("rare equipment is available"). |
| 5 Landslide Corridor | The network is a single highway $0,1,...,V-1$ with the HQ at one end, plus a few detours spanning two or three nodes, at most four roads per location and average degree at most 2.4. One road has no detour; it is closed in wave 1 and a target lies beyond it ("a collapse cuts off whole communities"). |
| 6 Outbreak Camp | At least 55% of the crates are medicine or water, and 55% of the crates receive an expiry hour of at most 300 ("supplies spoil"). The log repeats two beacon messages with 3% noise, and the data is regenerated until the most frequent symbol exceeds 30% of the log ("beacons repeat the same messages"). |

## 2. Planted objects and claims
- **Tour.** A nearest-neighbour tour from site 0 is improved by 2-opt, which can only shorten it; hence the stored length is never greater than the nearest-neighbour length.
- **Vertex cover.** The cover is chosen first and the sensor edges are sampled only among pairs that contain at least one cover node. **Safety rules.** A hidden assignment is chosen first; any rule it violates has one literal flipped. The ratio of rules to switches is set by $k mod 3$ to the bands 2.6-3.3, 3.7-4.6 and 5.0-5.8 (9, 8 and 9 of the 26 M and L cases). **Rations.** The planted items are chosen first and the target is their sum.
- **Radio.** Present phrases are cut from the log, absent phrases are redrawn until their count is zero, and all counts are recomputed by scanning with overlaps. The edit bound equals the true edit distance plus 0-3. Several windows are moved so that they start where another finishes (touching pairs).
- **Variety rules.** Even-numbered tier-S cases are resampled until greedy by value per kg is not optimal (14 of the 20 tier-S cases satisfy this), and odd-numbered tier-S cases until some target has a more expensive fewest-roads route (11 of 20). Separate random streams make all modules different across cases.
- **Claims (tier S).** The generator computes them by dynamic programming, greedy selection, and enumeration of permutations. The validator recomputes them by different methods (subset enumeration, recursion over compatible sets, recursion over cuts, Held-Karp and branching vertex cover).

## 3. The traps
| **Case** | **What was built** | **Why it is hostile** | **Check** |
|---|---|---|---|
| 46 | 2\,947 crates sorted by value (up), weight (up), expiry (down) and serial (up), i.e. four of the five fields are monotone. | Already-sorted input degrades quicksort with a first or last pivot to $O(n^2)$, and sorting steps are wasted. | V8: at least three monotone fields |
| 47 | 12 crates, capacity 20: a bait crate (11 kg, value 61, 5.55 per kg) and several crates of 10 kg and value 55 (5.50 per kg). | Greedy by value per kg takes the bait and nothing else fits: 61 against an optimum of 110 (55%). | V8: dynamic-programming optimum against greedy ($<= 60%$) |
| 48 | 2\,814 locations on a highway with hop diameter at least 2\,188. The HQ has a direct 60-minute road to location 8, whereas the 8-road detour costs 11. | The fewest-roads route (one road, cost 62) is 5.6 times as expensive as the cheapest route, so breadth-first search alone gives a wrong answer. | V8: diameter $>= 500$ and cost ratio $>= 1.5$ |
| 49 | A log of 64\,662 symbols, 92% of which is a single repeated symbol. Patterns of length 8-40 equal that symbol repeated $(l-1)$ times followed by a different symbol. | Every start position matches almost the whole pattern and then fails, so naive search needs about $N* M$ steps whereas KMP remains linear. | V8: periodic run $>= 90%$; at least four near-miss patterns |

## 4. What will be hard
| **Case study** | **Two hardest decisions and the property of the data that causes the difficulty** |
|---|---|
| 1 Delta | **B (routes):** at least 40% penalised locations make the cheapest and the fewest-roads routes differ, and each of the 3-5 waves requires a new computation. **A (inventory):** food and water crates with random weights make the density-greedy choice suboptimal. |
| 2 Earthquake | **D (queue):** bursts raise the backlog and priorities are mostly 6-10, so many alarms tie. **B/F (routes, cable):** the map is almost a tree (degree about 2.3), so one closure disconnects locations and the answer is frequently "no route". |
| 3 Cyclone | **C (scheduling):** dense overlap makes the schedules of maximum count and maximum value differ. **E (radio):** uniform noise over 38 symbols gives a Huffman code of about 5.3 bits per symbol, i.e. almost no saving. |
| 4 Urban | **D (queue):** more than 1.5 alarms arrive per tick while one is released, so the backlog grows to thousands and a linear scan costs $O(m^2)$. **B (routes):** the dense graph has many alternatives of equal length (up to $2.5V$ roads). |
| 5 Landslide | **B (reachability):** the cut leaves targets unreachable, so "no route" must be reported, and a chain of depth about $V/3$ breaks recursive searches. **F (cable):** the network is nearly a path, so only the reachable part may be spanned. |
| 6 Outbreak | **A (inventory):** half of the crates expire by hour 300, so value density alone is misleading. **E (radio):** the repetitive beacons produce many overlapping matches and a strongly skewed Huffman code. |

