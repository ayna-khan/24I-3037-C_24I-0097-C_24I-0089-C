# B/F comparison and recommendation

Master sample: 62 cases, 867 route checks, 289 forest checks, including cumulative waves.
Largest growth input: 1024 vertices from case 10-40.

| Module | Method | Median seconds at largest size | IQR seconds | Operations | Peak bytes beyond input |
|---|---|---:|---:|---:|---:|
| B | dijkstra | 0.0117117 | 1.94000004e-05 | 35349 | 744192 |
| B | bellman | 0.0166039 | 6.51999999e-05 | 53403 | 752400 |
| B | bfs | 0.0101313 | 4.3e-05 | 27011 | 641376 |
| F | kruskal | 0.0169383 | 6.51e-05 | 65339 | 258896 |
| F | prim | 0.0180257 | 5.98000006e-05 | 73050 | 605584 |

B: Dijkstra and Bellman-Ford agree in every comparison. BFS chooses a fewest-roads route but its worst cost ratio is 20.000; mean ratio is 1.276 over reachable nonzero-cost targets.
F: Kruskal and Prim agree on every forest cost. Largest-input Prim/Kruskal time ratio is 1.064.

Ship heap Dijkstra for positive travel costs and BFS for reachability/hops. Keep Bellman-Ford as a check; it can be competitive on small, favourably ordered graphs because it stops early. Reject negative minutes/penalties rather than feeding them to Dijkstra.

Ship Kruskal with union by size and path compression for sparse cable networks; keep Prim as an independent baseline. A disconnected map returns a forest. For HQ-only cabling pass the reachable set. Reconsider an array Prim implementation for dense graphs; monitor E/V and memory before choosing.

Limitations: seven nested prefixes of one real network are not seven independent networks; edge density changes. Quality covers sampled cases, not the complete master release. Timing is one machine/session, power state unverified; IQR and operation counts must accompany comparisons. No 300-second DNF demonstration is claimed: these data sizes finish quickly.

Failure-mode paragraph for Ayna: positive-cost routing becomes invalid if a later data source introduces negative weights; stale closure state can dispatch into disconnected locations; unusually dense graphs increase adjacency/sorting memory and can reverse the F-method preference. The new validation, NO_ROUTE checks, independent references and seeded-fault tests exercise these boundaries. Ayna owns the final ranked list.
